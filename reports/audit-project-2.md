================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 1

## Findings

### [CRITICAL] God Class / God Module
File: src/AppManager.js:4-139
Description: `AppManager` is a single class that creates the DB schema and seed data (`initDb`, lines 10-23), defines every HTTP route (`setupRoutes`, lines 25-138), runs the entire checkout business flow (course lookup, user creation, fake payment approval, enrollment, payment, audit log), computes the admin financial report, and deletes users — all with raw SQL inlined in the same methods.
Impact: No part of the app can be unit tested or changed in isolation; a change to how payments work risks breaking user creation, enrollment, and reporting because they share one file and the same callback chains.
Recommendation: Split into per-domain Models (User, Course, Enrollment, Payment, AuditLog) for data access, Controllers for checkout / financial report / user management, and a routes layer, per the target MVC layout.

### [CRITICAL] Hardcoded Credentials / Secrets
File: src/utils.js:1-7; src/AppManager.js:45
Description: `config` hardcodes `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` and `smtpUser` as literals in source. On every checkout, `AppManager.js:45` logs the live-looking gateway key **and the full card number** (`` `Processando cartão ${cc} na chave ${config.paymentGatewayKey}` ``).
Impact: Anyone with repo read access — or access to application logs — obtains a production-looking payment key and DB credentials, and logs accumulate raw card numbers (PAN), which is also a PCI-DSS violation.
Recommendation: Read every secret from environment variables through a dedicated config module with no literal fallback (fail to boot if missing), keep `.env.example` values empty, and remove both the key and the card number from the log line.

### [CRITICAL] Authentication Bypass / Credential Not Verified
File: src/AppManager.js:40, 66-75
Description: `POST /api/checkout` receives a password (`p = req.body.pwd`, line 31) and does "find or create" on the email (line 40). When the email is new it hashes `p` and creates the user (lines 66-72); when the email **already exists** it goes straight to `processPaymentAndEnroll(user.id)` (lines 73-75) — the submitted password is never compared with the stored `pass`. The seeded account `leonan@fullcycle.com.br` (line 18) can be enrolled/charged by anyone who sends that email with any password (or none).
Impact: Full authentication bypass: knowing an e-mail address is enough to act as that account — creating enrollments and payment records in the victim's name.
Recommendation: On the existing-user branch, verify the submitted password against the stored hash (constant-time compare) and return 401 with no side effects on mismatch; require `pwd` on every path.

### [CRITICAL] Unauthenticated Admin Endpoint
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` performs no authentication or authorization check before returning revenue and per-student payment data for every course.
Impact: Any anonymous caller can read the business's complete financial and enrollment data, including student names.
Recommendation: Put an admin auth gate (token/role check) in front of the route that fails closed — 401/403 when the gate's secret is not configured, never open.

### [CRITICAL] Unauthenticated Destructive Endpoint
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes a user row with no authentication and no validation of `id`; the response text itself admits the `enrollments`/`payments` rows are left orphaned ("as matrículas e pagamentos ficaram sujos no banco").
Impact: Any anonymous caller can permanently delete any user by iterating IDs, and the orphaned enrollment/payment rows silently corrupt the financial report (students show as "Unknown").
Recommendation: Require the same fail-closed admin gate, validate `id` (404 if not found), and delete dependent enrollments/payments in a transaction (or soft-delete).

### [HIGH] Business Logic Trapped in Controller — Checkout
File: src/AppManager.js:28-78
Description: The `/api/checkout` handler inlines the whole flow: input parsing, course lookup, conditional user creation with password hashing, a fake payment-gateway decision (`cc.startsWith("4")`, line 46), enrollment insert, payment insert, audit log insert, and cache write — all inside the route callback.
Impact: None of the checkout rules can be tested without booting HTTP and SQLite, and the multi-step write (enrollment + payment + audit) has no transaction, so a mid-flow failure leaves an enrollment without a payment.
Recommendation: Move the flow into a checkout controller/service that orchestrates Models (ideally inside a DB transaction) and isolate the payment decision in a payment-gateway module.

### [HIGH] Business Logic Trapped in Controller — Financial Report
File: src/AppManager.js:80-129
Description: The `/api/admin/financial-report` handler aggregates revenue per course and builds the student list inline, using hand-written `coursesPending`/`enrPending` counters to detect when all nested callbacks have finished (lines 86-87, 93, 97-98, 117-121).
Impact: The aggregation can't be reused or tested outside the route, and the manual counter pattern is fragile — any added or failing branch either never responds or responds twice.
Recommendation: Move aggregation into a report model/service that returns the assembled data; the route only calls it and serializes.

### [HIGH] Tight Coupling / No Dependency Injection
File: src/AppManager.js:5-8; src/app.js:8-10
Description: The constructor directly instantiates `new sqlite3.Database(':memory:')` (line 7) with no way to inject another connection, and every handler reaches into `this.db`/`self.db`; `app.js` builds `new AppManager()` and calls `initDb()` without waiting for it to finish.
Impact: Nothing can be tested without a real SQLite engine; changing the DB (or its path) requires editing the class itself, and schema creation races with the server start.
Recommendation: Create the connection in a db module/composition root, await schema init before `listen`, and pass the connection into the Models.

### [HIGH] Mutable Global State
File: src/utils.js:9-15, 25; src/AppManager.js:59
Description: `globalCache` (line 9) is a module-level object mutated by `logAndCache` (lines 12-15) on every checkout (`AppManager.js:59`), shared by all requests with no eviction; `totalRevenue` (line 10) is exported as a mutable "running total" but is a primitive copied on import and never updated anywhere.
Impact: The cache grows without bound for the process lifetime and is shared across requests; `totalRevenue` is dead, misleading state that looks like a business metric.
Recommendation: Replace `globalCache` with an encapsulated cache with bounded size/TTL (or drop it — nothing reads it), and delete `totalRevenue`.

### [HIGH] Weak / Homemade Cryptography
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: `badCrypto` "hashes" passwords by repeating the first two base64 characters of the plaintext and slicing 10 characters — no salt, not a hash, and collides for any passwords sharing a prefix. It's used at `AppManager.js:68` with a silent default password `"123456"` when `pwd` is absent; the seed user is stored with the plaintext `'123'` (line 18).
Impact: A leaked `users` table exposes trivially recoverable passwords; many different passwords map to the same stored value, and password-less signups all share one guessable password.
Recommendation: Use a slow, salted password hash (e.g. Node's built-in `crypto.scrypt` or bcrypt/argon2) with a timing-safe verify, hash the seed password too, and remove the `"123456"` fallback.

### [MEDIUM] N+1 Query Pattern
File: src/AppManager.js:83-127
Description: For each course (line 83) the handler queries its enrollments (line 92); for each enrollment it queries the user (line 104) and then the payment (line 106) — a 1 + C + 2E query fan-out instead of a single join.
Impact: Response time grows with `courses × enrollments` — the report gets steadily slower as sales grow.
Recommendation: Replace with one query joining `courses`, `enrollments`, `users`, `payments` (LEFT JOINs) and aggregate the result in the model.

### [MEDIUM] Missing Route-Level Validation
File: src/AppManager.js:29-35, 68, 131-133
Description: Checkout only checks that `u`, `e`, `cid`, `cc` are truthy (line 35) — no email format, numeric `c_id`, or card-format checks, and `p` isn't required (it falls back to `"123456"` at line 68). `DELETE /api/users/:id` passes `req.params.id` to SQL with no format check (lines 132-133).
Impact: Malformed input reaches business logic and the DB unchecked (e.g. a numeric `card` crashes `cc.startsWith`, invalid emails are stored as identities).
Recommendation: Validate all fields at the route/controller boundary (required, type, format) and return 400 before any DB call.

### [MEDIUM] Callback Hell / Deeply Nested Async Flow
File: src/AppManager.js:37-77, 83-128
Description: Checkout nests `db.get` → `db.get` → `db.run` → `db.run` → `db.run` callbacks five levels deep (lines 37, 40, 50, 54, 57) plus the `processPaymentAndEnroll` closure (line 43), mixing `this` and `self` to work around `function` callbacks; the report nests `db.all` → `db.all` → `db.get` → `db.get` (lines 83, 92, 104, 106).
Impact: Hard to read or extend safely; error handling drifts between levels (see next finding).
Recommendation: Flatten with `async`/`await` over a promise-based DB layer (see deprecated-API finding).

### [MEDIUM] Inconsistent / Silent Error Handling
File: src/AppManager.js:38, 57-60, 92-93, 104-106, 133-135
Description: Line 38 turns any DB error into "Curso não encontrado" (404); the audit-log insert callback (line 57) ignores `err` and still answers 200; in the report, `err` is never checked at lines 92, 104, 106 (a failure throws on `enrollments.length`); the delete handler (lines 133-135) ignores `err` and always reports success, even for a nonexistent id. Errors are plain-text `res.send` strings with no central handler.
Impact: DB failures are misreported as 404/200, the report can crash the request with an unhandled exception, and failed deletions look successful to callers.
Recommendation: Propagate errors to a single Express error-handling middleware that logs and returns a consistent 500 JSON body.

### [MEDIUM] Deprecated / Obsolete API Usage
File: package.json:11; src/AppManager.js:1, 7-138
Description: The project uses the callback-style `sqlite3` driver (`^5.1.6`) and every query in `AppManager.js` is written against its callback API, which has no native Promise support.
Impact: It forces the callback nesting and manual completion counters documented above and blocks a clean `async`/`await` design.
Recommendation: Wrap the driver in a promise-based layer (`sqlite` package, `util.promisify`, or `better-sqlite3`) and rewrite queries with `async`/`await`.

### [LOW] Poor Naming / Magic Numbers & Strings
File: src/AppManager.js:26, 29-33, 46; src/utils.js:17-23; src/app.js:13
Description: Request fields are bound to `u`, `e`, `p`, `cid`, `cc` (lines 29-33) and `self = this` (line 26); the payment rule is the unexplained magic `cc.startsWith("4")` (line 46); `badCrypto` loops a magic `10000` times and slices magic `2`/`10` (utils.js:19-22); `app.js:13` logs the leftover name "Frankenstein LMS".
Impact: Every reader must reverse-engineer intent from context.
Recommendation: Use domain names (`name`, `email`, `password`, `courseId`, `cardNumber`), name the card-prefix rule as a constant in the payment module, and fix the startup log.

================================
Total: 16 findings
================================

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados
- [x] Detecção de APIs deprecated incluída (se aplicável)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
- [x] Gates de autenticação falham fechados sem o secret configurado (401/403, testado em runtime)
- [x] Nenhum segredo com valor padrão fixo no código (sem a variável, a aplicação não sobe ou usa chave aleatória — testado em runtime)
- [x] Credenciais verificadas em todos os caminhos (credencial errada para conta existente → 401/403, testado em runtime)

Fase 3 executada em 2026-10-03 (humano aprovou no gate). Evidências de runtime desta execução:

- **Segredos:** `src/config/index.js` é o único leitor de `process.env`; grep não encontrou fallback
  literal para segredo (os únicos defaults são `PORT=3000` e `DB_PATH=:memory:`, não secretos).
  `dbUser`/`dbPass`/`smtpUser` foram removidos (SQLite não usa credenciais e SMTP não era usado).
  Com `PAYMENT_GATEWAY_KEY` ausente ou só com espaços (inclusive via `npm start` sem `.env`), a
  aplicação recusou o boot com `exit=1` e mensagem nomeando a variável. `.env.example` deixa
  `PAYMENT_GATEWAY_KEY=` e `ADMIN_TOKEN=` vazios.
- **Gate admin fail-closed:** boot sem `ADMIN_TOKEN` → `GET /api/admin/financial-report` e
  `DELETE /api/users/:id` responderam 403 sem header, com header vazio e com os chutes
  `undefined`/`null`. Com `ADMIN_TOKEN` configurado, token errado → 403 e token correto → 200.
- **Credenciais em todos os caminhos:** `POST /api/checkout` para conta existente com senha errada
  (seed `leonan@…` e um usuário criado no checkout) → 401, sem matrícula/pagamento criados e sem
  chamada ao gateway (relatório inalterado; 5 cobranças no log para 5 checkouts aprovados/recusados).
  Sem `pwd` → 400. Com a senha correta → 200. Pagamento recusado não cria mais o usuário.
- **Endpoints originais:** checkout sucesso (200 `{msg, enrollment_id}`), pagamento recusado (400),
  curso inexistente (404), relatório (200, mesmo formato `[{course, revenue, students[{student, paid}]}]`),
  delete (200; agora 404 para id inexistente e 400 para id inválido, removendo matrículas/pagamentos
  junto). 15 checkouts concorrentes para o mesmo e-mail novo → 15×200, sem erros.
- **Logs:** nenhuma ocorrência da chave do gateway nem do número completo do cartão (`****4444`).
- **Re-scan:** sem `badCrypto`, `globalCache`, `totalRevenue`, `AppManager` nem SQL interpolado;
  o driver `sqlite3` é usado só em `src/db/connection.js` (wrapper com Promises). As 16 findings
  da Fase 2 foram resolvidas — nenhuma adiada.
- **Mudanças de contrato intencionais:** `pwd` passou a ser obrigatório (antes caía no padrão
  `"123456"`); senha errada para conta existente → 401; rotas admin exigem `x-admin-token`;
  respostas de erro de validação trazem os campos inválidos. Documentado no README e em `api.http`.
