================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 5 | LOW: 1

## Findings

### [CRITICAL] God Class / God Module
File: src/AppManager.js:4-139
Description: `AppManager` is a single class that creates the DB schema and seed data (`initDb`, lines 10-23), defines all HTTP routes (`setupRoutes`, lines 25-138), runs the entire checkout business flow (course lookup, user creation, fake payment approval, enrollment, payment, audit logging), and computes the admin financial report — all with raw SQL calls inlined directly in the same methods.
Impact: No part of the app can be unit tested or changed in isolation; a change to how payments work risks breaking user creation, enrollment, and reporting because they all live in the same file and share the same callback chains.
Recommendation: Split into per-domain Models (User, Course, Enrollment, Payment) for data access and separate Controllers for checkout/financial-report/user-management flows, per the target MVC layout.

### [CRITICAL] Hardcoded Credentials / Secrets
File: src/utils.js:1-7
Description: `config` hardcodes `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, and `dbUser`/`smtpUser` as literal strings in source. The live-looking payment key is additionally printed to the console on every checkout (`src/AppManager.js:45`, `` `Processando cartão ${cc} na chave ${config.paymentGatewayKey}` ``).
Impact: Anyone with repo read access — or access to application logs — obtains what looks like a live payment gateway key and DB credentials.
Recommendation: Move all values in `config` to environment variables read via a dedicated config module, and remove the secret from the log line entirely.

### [CRITICAL] Unauthenticated Admin Endpoint
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` performs no authentication or authorization check before returning full revenue and per-student payment data for every course.
Impact: Any anonymous caller can read the business's complete financial and enrollment data.
Recommendation: Add an authentication/authorization gate (admin token or role check) in front of this route, and ensure it fails closed (401/403) when the gate's credential is not configured.

### [CRITICAL] Unauthenticated Destructive Endpoint
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes a user row with no authentication check and no validation of `id`; the handler comment even acknowledges the resulting `enrollments`/`payments` rows are left orphaned ("ficaram sujos no banco").
Impact: Any anonymous caller can permanently delete any user by guessing/iterating IDs, and the resulting orphaned enrollment/payment rows corrupt the financial report's joins.
Recommendation: Require authentication/authorization before deletion, validate `id`, and either cascade-delete or soft-delete related enrollments/payments.

### [HIGH] Business Logic Trapped in Controller — Checkout
File: src/AppManager.js:28-78
Description: The `/api/checkout` handler inlines the entire business flow: input parsing, course lookup, conditional user creation with password hashing, a fake payment-gateway decision (`cc.startsWith("4")`, line 46), enrollment insertion, payment insertion, and audit logging — all directly in the route callback.
Impact: None of this checkout logic can be tested without booting the HTTP server and a real SQLite instance, and the same flow will likely be re-duplicated the next time a similar purchase endpoint is added.
Recommendation: Extract into a `CheckoutController` that delegates to a `CheckoutService`/use case, with Models handling persistence.

### [HIGH] Business Logic Trapped in Controller — Financial Report
File: src/AppManager.js:80-129
Description: The `/api/admin/financial-report` handler manually aggregates revenue per course and builds the student list inline, using hand-written `coursesPending`/`enrPending` counters to detect when all nested async callbacks have finished (lines 86, 93, 97-99, 117-122).
Impact: The aggregation logic can't be reused or tested outside the route, and the manual pending-counter pattern is fragile — any added/removed callback branch silently breaks completion detection.
Recommendation: Move aggregation into a `FinancialReportService`/model method that returns the assembled data, leaving the route to just call it and shape the response.

### [HIGH] Tight Coupling / No Dependency Injection
File: src/AppManager.js:4-8
Description: The constructor directly instantiates a concrete SQLite connection (`this.db = new sqlite3.Database(':memory:')`) with no way to substitute a test double or a differently-configured connection, and every route handler reaches into `this.db`/`self.db` directly.
Impact: The class cannot be unit tested without a real (in-memory) SQLite engine, and swapping databases or mocking persistence requires editing `AppManager` itself.
Recommendation: Inject the DB connection/repository through the constructor (or a composition root), so Models receive their dependency rather than constructing it.

### [HIGH] Mutable Global State
File: src/utils.js:9-15
Description: `globalCache` (line 9) is a module-level object mutated by `logAndCache` (lines 12-15) on every checkout, shared across all concurrent requests; `totalRevenue` (line 10) is a module-level counter that is exported but never actually updated anywhere in the codebase.
Impact: `globalCache` entries accumulate for the lifetime of the process with no eviction, and concurrent requests read/write the same object with no isolation, which is a race condition under real concurrency; `totalRevenue` is dead, misleading state that looks like a running total but never changes.
Recommendation: Replace `globalCache` with a proper cache with scoping/eviction (or remove it if unnecessary), and delete the unused `totalRevenue` variable.

### [HIGH] Weak / Homemade Cryptography
File: src/utils.js:17-23
Description: `badCrypto` "hashes" passwords by repeatedly base64-encoding the plaintext and slicing fixed substrings — it is not a cryptographic hash at all (no salt, trivially invertible/collidable). It is used to store new users' passwords in plaintext-equivalent form at `src/AppManager.js:68-69`.
Impact: Any compromise of the `users` table (or the `pass` column) exposes effectively-recoverable passwords for every user, including the default `"123456"` applied when no password is supplied.
Recommendation: Replace with a real salted password hash (bcrypt/scrypt/argon2) and drop the silent `"123456"` fallback in favor of requiring a password.

### [MEDIUM] N+1 Query Pattern
File: src/AppManager.js:83-127
Description: For each course returned (line 83), the handler queries enrollments (line 92); for each enrollment, it queries the user (line 104) and then the payment (line 106) — a query fan-out three levels deep instead of a single joined query.
Impact: Response time grows with `courses × enrollments`, turning a report endpoint into an increasingly slow one as course/enrollment volume grows.
Recommendation: Replace with one query joining `courses`, `enrollments`, `users`, and `payments`, and aggregate in application code (or SQL `GROUP BY`).

### [MEDIUM] Missing Route-Level Validation
File: src/AppManager.js:29-35, 131-133
Description: The checkout handler validates presence of `u`, `e`, `cid`, `cc` (line 35) but not `p` — a missing password silently falls back to the hardcoded default `"123456"` (line 68). `DELETE /api/users/:id` (lines 131-133) uses `req.params.id` with no format/existence validation at all before issuing the delete.
Impact: Malformed or missing input reaches business logic and the database unchecked — e.g. every user created without a password gets the same guessable default password.
Recommendation: Validate all required fields (including `p`) up front and reject requests with malformed `id`/missing fields before any DB call.

### [MEDIUM] Callback Hell / Deeply Nested Async Flow
File: src/AppManager.js:37-77, 83-127
Description: The checkout handler nests `db.get`/`db.run` callbacks up to six levels deep (lines 37→40→50→54→57, plus the inner `processPaymentAndEnroll` closure at line 43). The financial-report handler nests four levels (`db.all`→`db.all`→`db.get`→`db.get`, lines 83-106) combined with manual completion counters.
Impact: Hard to read or modify safely, and error handling is inconsistent across nesting levels (see next finding), making an inner failure easy to lose track of.
Recommendation: Rewrite using a promise-based SQLite wrapper with `async`/`await` to flatten the flow (see deprecated-API finding below).

### [MEDIUM] Inconsistent / Silent Error Handling
File: src/AppManager.js:92, 104, 106, 133-136
Description: The `err` parameter is captured but never checked in the enrollments query callback (line 92), the user lookup callback (line 104), and the payment lookup callback (line 106) inside the financial report — a query failure would throw on `enrollments.length` instead of returning an error response. The delete-user handler (lines 133-136) also ignores `err` entirely and always responds with a success message regardless of whether the delete actually succeeded.
Impact: A transient DB error in the financial report crashes the request with an unhandled exception instead of a controlled 500; a failed user deletion is silently reported to the caller as successful.
Recommendation: Check `err` at every callback and return an appropriate error response; centralize this into shared error-handling middleware so it isn't repeated ad hoc per route.

### [MEDIUM] Deprecated / Obsolete API Usage
File: package.json:11, used throughout src/AppManager.js
Description: The project depends on the callback-style `sqlite3` driver (`^5.1.6`) and every query in `AppManager.js` is written against its callback API, which has no native Promise support.
Impact: Forces the deep callback nesting and inconsistent error handling documented above, and blocks a clean migration to `async`/`await`.
Recommendation: Replace with a promise-based driver (`better-sqlite3` or the `sqlite` wrapper around `sqlite3`) and rewrite queries with `async`/`await`.

### [LOW] Poor Naming / Magic Numbers & Strings
File: src/AppManager.js:29-33, 46; src/utils.js:19; src/app.js:13
Description: Checkout destructures request fields into single/double-letter names `u`, `e`, `p`, `cid`, `cc` (lines 29-33) instead of descriptive names; the entire "payment gateway" decision is the unexplained magic check `cc.startsWith("4")` (line 46); `badCrypto` loops a magic `10000` times with no explanation (utils.js:19); and `app.js:13` logs the stray leftover name "Frankenstein LMS" that doesn't match the project's actual name.
Impact: Forces every future reader to reverse-engineer intent from context instead of reading it directly; the "Frankenstein LMS" string in particular suggests un-cleaned boilerplate.
Recommendation: Rename variables to their domain meaning (`username`, `email`, `password`, `courseId`, `cardNumber`), name the card-prefix check as a constant/comment, and fix the stray log string.

================================
Total: 15 findings
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

Fase 3 executada em 2026-09-27. Aplicação foi iniciada com `node src/app.js` sem
`ADMIN_TOKEN` configurado (estado padrão de `.env.example`) e as duas rotas administrativas
(`GET /api/admin/financial-report`, `DELETE /api/users/:id`) responderam 403 sem
credenciais; com `ADMIN_TOKEN` configurado e o header `x-admin-token` correto, ambas
responderam com sucesso. `POST /api/checkout` foi exercitado com sucesso, pagamento
recusado, e validação de campo obrigatório (senha ausente → 400). As 15 findings da Fase 2
foram verificadas como resolvidas nesta refatoração — nenhuma foi adiada.
