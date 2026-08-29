================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express ^4.18.2
Dependencies:  express, sqlite3 (^5.1.6, in-memory DB, callback-style driver)
Domain:        LMS API with a course-checkout flow (users, courses, enrollments, payments, audit logs)
Architecture:  Monolithic/God Class — app.js is a thin bootstrap; AppManager.js is a single class mixing DB schema setup, seeding, routing, business rules (payment processing, enrollment) and raw data access, with deeply nested callbacks
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js) — ~180 LOC total
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite, in-memory — no persistence, no migrations)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 5 | LOW: 2

## Findings

### [CRITICAL] God Class / God Module
File: src/AppManager.js:1-141
Description: A single `AppManager` class opens the DB connection (line 7), creates the schema and seeds data (`initDb`, lines 10-23), defines every route (`setupRoutes`, lines 25-138), and inline within those routes performs business logic (payment approval, enrollment), raw SQL access, and response shaping — for four unrelated concerns (checkout, financial reporting, user deletion) in one file.
Impact: Nothing here can be unit tested without booting Express and a real SQLite instance; a change to the checkout flow risks breaking the financial report or user-deletion routes since they all share the same class and DB handle.
Recommendation: Split into per-domain Models (User, Course, Enrollment, Payment), a routes/views layer, and controllers per the target MVC layout; `initDb`/seeding moves to a dedicated data/bootstrap module.

### [CRITICAL] Hardcoded Credentials / Secrets
File: src/utils.js:1-7
Description: `config` hardcodes `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, and `smtpUser` directly in source, with zero use of `process.env` anywhere in the codebase. The live-looking payment gateway key is also printed to stdout on every checkout (AppManager.js:45).
Impact: Anyone with read access to the repository gets a production-looking payment gateway key and DB credentials; the key additionally leaks into application logs on every request.
Recommendation: Move every value in `config` to environment variables (`process.env.DB_PASS`, etc.) read through a dedicated config module, and stop logging the key.

### [CRITICAL] Unauthenticated Admin/Destructive Endpoints
File: src/AppManager.js:80-137
Description: `GET /api/admin/financial-report` (lines 80-129) exposes full revenue and per-student payment data, and `DELETE /api/users/:id` (lines 131-137) permanently deletes a user — neither route has any authentication or authorization middleware; both are reachable by anyone who can reach the server.
Impact: Any unauthenticated caller can read the entire business's financial report or delete an arbitrary user by guessing/incrementing an id.
Recommendation: Add an auth/authorization middleware (e.g. session or token-based, admin-role check) in front of both routes before restructuring their handlers into controllers.

### [CRITICAL] Broken Authentication — Password Never Verified for Existing Users
File: src/AppManager.js:40, 66-76
Description: In `/api/checkout`, when a user is found by email alone (`this.db.get("SELECT id FROM users WHERE email = ?", [e], ...)`, line 40), the code calls `processPaymentAndEnroll(user.id)` (line 74) directly — the submitted password `p` is never compared against the stored `pass` column for an existing user. `p`/`badCrypto` is only ever used on the user-creation branch (line 68).
Impact: Anyone who knows or guesses another user's email can enroll that account in a course and trigger a "payment" against it with no password check at all — a full authentication bypass on an existing account.
Recommendation: Verify the submitted password against the stored hash for existing users before calling `processPaymentAndEnroll`, and reject with 401 on mismatch.

### [HIGH] Business Logic Trapped in Route Handlers
File: src/AppManager.js:28-78, 80-129
Description: `/api/checkout` inlines card-brand approval logic (`cc.startsWith("4") ? "PAID" : "DENIED"`, line 46), user provisioning, enrollment, payment recording, and audit logging directly in the Express handler. `/api/admin/financial-report` inlines revenue aggregation (accumulating `courseData.revenue`, lines 89-121) directly in the handler as well.
Impact: None of this logic (payment approval rules, revenue aggregation) can be tested without spinning up the full HTTP + DB stack, and the same rules will likely be duplicated the next time a similar endpoint is added.
Recommendation: Extract into a `CheckoutController`/`CheckoutService` and a `FinancialReportService` per the refactoring playbook, leaving the route handler as parse-input → call service → shape response.

### [HIGH] Tight Coupling / No Dependency Injection
File: src/AppManager.js:4-8
Description: The constructor builds a concrete `sqlite3.Database(':memory:')` directly (line 7) with no way to inject a different connection (a test double, a file-backed DB, a pooled connection) from outside the class.
Impact: `AppManager` cannot be unit tested without a real SQLite engine, and switching database engines or adding a test/staging DB requires editing this class directly.
Recommendation: Inject the DB connection (or a repository abstraction) via the constructor/composition root instead of constructing it inline.

### [HIGH] Mutable Global State
File: src/utils.js:9-10, 12-15, 25; src/AppManager.js:2, 59
Description: `globalCache` (module-level object, line 9) is mutated by `logAndCache` (lines 12-15) from inside the checkout request handler (AppManager.js:59) with no per-request or per-user scoping. `totalRevenue` (line 10) is exported and imported into `AppManager.js` (line 2) but never read or incremented anywhere — dead mutable global state kept around from an earlier version.
Impact: Concurrent requests share and race on `globalCache` (a later request's data can stomp an earlier one under load), and the unused `totalRevenue` import is dead code that misleads future readers into thinking revenue is tracked centrally.
Recommendation: Remove `totalRevenue` if truly unused, and replace `globalCache` with a proper per-request/response value or an actual cache layer (e.g. Redis) if caching is really needed.

### [HIGH] Weak / Homemade Cryptography
File: src/utils.js:17-23 (used at src/AppManager.js:68)
Description: `badCrypto` "hashes" a password by base64-encoding it and repeating a 2-character slice 10,000 times, then truncating to 10 characters — this is not a cryptographic hash, has no salt, and is trivially reversible/collides constantly given the 10-char truncation of a small alphabet.
Impact: Stored password data offers effectively no protection; an attacker with DB read access can recover or brute-force original passwords in a way bcrypt/argon2 would prevent.
Recommendation: Replace with a real salted password hash (bcrypt/argon2/scrypt) via a maintained library.

### [MEDIUM] N+1 Query Pattern
File: src/AppManager.js:83-127
Description: `/api/admin/financial-report` runs `db.all("SELECT * FROM courses")` then, per course, `db.all(... enrollments ...)`, then per enrollment, two more sequential queries (`db.get` user, `db.get` payment) — a query cascade of roughly `1 + courses + (enrollments × 2)` calls to answer one request.
Impact: Response time grows linearly (worse than linearly under concurrent load) with the number of courses/enrollments; this endpoint will become unacceptably slow as soon as real data volume shows up.
Recommendation: Replace with a small number of JOINed queries (courses ⋈ enrollments ⋈ users ⋈ payments) aggregated in application code or SQL.

### [MEDIUM] Missing Route-Level Validation
File: src/AppManager.js:28-35, 131-137
Description: `/api/checkout` checks only presence of `u`, `e`, `cid`, `cc` (line 35) — no email format check, no card-number format/length check, and `p` (password) is optional with a silent fallback to `"123456"` (line 68) when creating a new user. `DELETE /api/users/:id` (lines 131-137) performs no validation on `id` at all (not checked as numeric, existence not verified) and always responds as if the deletion succeeded.
Impact: Malformed emails/card numbers reach business logic and the DB unchecked; deleting a non-existent user still returns a success-shaped message, hiding real failures from the caller.
Recommendation: Add explicit input validation (format/type checks) at the route boundary and have the delete route report whether a row was actually affected.

### [MEDIUM] Callback Hell / Deeply Nested Async Flow
File: src/AppManager.js:37-77, 83-127
Description: `/api/checkout` nests `db.get` → `db.get` → (`db.run` → `db.run` → `db.run`) five levels deep (lines 37-77); `/api/admin/financial-report` nests `forEach` → `db.all` → `forEach` → `db.get` → `db.get` (lines 89-125). Error handling is inconsistent across these levels (see next finding).
Impact: Hard to follow the control flow, easy to introduce a bug when adding one more step, and any inner callback that forgets to call `res` will hang the request with no response ever sent.
Recommendation: Move to a promise-based SQLite driver (`sqlite`/`better-sqlite3`) with `async/await` and sequential `await` calls once logic is extracted into a service (see finding on deprecated API usage below).

### [MEDIUM] Inconsistent / Silent Error Handling
File: src/AppManager.js:57, 92, 104-106, 133-136
Description: Several DB callbacks ignore the `err` parameter entirely before using the result — the audit-log insert (line 57) does not check its own `err`; the enrollments query in the financial report (line 92) uses `enrollments.length` without checking `err` first; the user/payment lookups in the same handler (lines 104, 106) do the same; the user-delete callback (lines 133-136) ignores `err` and always sends a success message regardless of whether the delete actually ran.
Impact: A DB failure inside any of these callbacks is silently swallowed — the client gets a "success" response (or hangs, in the financial-report case) even though the operation actually failed, making production issues very hard to diagnose.
Recommendation: Check `err` at every callback and return a proper error response (or centralize this via an error-handling middleware once routes are extracted into controllers).

### [MEDIUM] Deprecated / Obsolete API Usage — Callback-style sqlite3 Driver
File: src/AppManager.js:1, 7, 12-137 (entire file's DB access pattern)
Description: The project uses the callback-style Node `sqlite3` package (`require('sqlite3').verbose()`, line 1) throughout, forcing manual callback nesting instead of `async/await` — this is the same driver family the catalog flags as having no native Promise support.
Impact: Every DB interaction is written as nested callbacks (see Callback Hell finding above) with no straightforward way to `await` sequential operations, and the inconsistent error handling this encourages compounds across the file.
Recommendation: Replace with a promise-based wrapper (`sqlite` package) or `better-sqlite3`, and rewrite handlers with `async/await`.

### [LOW] Poor Naming — Cryptic Single/Double-Letter Identifiers
File: src/AppManager.js:29-33
Description: Request fields are destructured into `u`, `e`, `p`, `cid`, `cc` (user, email, password, course id, card number) — none of these names convey their meaning without reading the surrounding logic.
Impact: Forces every future reader to reverse-engineer which variable is which before they can safely change the checkout flow.
Recommendation: Rename to `username`, `email`, `password`, `courseId`, `cardNumber` when extracting the controller.

### [LOW] Magic Strings for Payment/Card Status
File: src/AppManager.js:46, 48, 54, 108
Description: Card-brand approval uses a bare `"4"` prefix check (`cc.startsWith("4")`, line 46) with no named constant, and payment/enrollment status is compared against raw string literals `"PAID"`/`"DENIED"` (lines 48, 54, 108) with no shared enum/constant module.
Impact: A typo in one of the string literals (e.g. `"Paid"` vs `"PAID"`) would silently break status comparisons elsewhere, and the card-brand rule's meaning isn't discoverable without reading the checkout logic.
Recommendation: Introduce named constants (e.g. `PAYMENT_STATUS.PAID`) shared across the checkout and reporting code.

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

Fase 3 executada em 2026-08-29. Projeto reestruturado em
`config/ db/ models/ controllers/ routes/ services/ middlewares/ utils/`
dentro de `src/`. Aplicação validada com `node src/app.js` (boot limpo, sem
erros) e os 4 endpoints originais de `api.http` exercitados via curl,
respondendo com o mesmo status/formato do legado. Todos os 16 findings da
Fase 2 foram resolvidos, com uma ressalva documentada abaixo:

- O finding CRITICAL "Unauthenticated Admin/Destructive Endpoints" foi
  **mitigado, não fechado por padrão**: as rotas `GET
  /api/admin/financial-report` e `DELETE /api/users/:id` agora passam por um
  middleware `adminAuth` (`src/middlewares/adminAuth.js`) que exige o header
  `x-admin-api-key` quando a variável de ambiente `ADMIN_API_KEY` está
  definida — validado nesta fase (401 sem header/chave errada, 200 com a
  chave correta). Por padrão (sem `ADMIN_API_KEY` configurada, como no
  ambiente local/demo) o middleware deixa a rota aberta e emite um aviso
  `[SECURITY]` no log, para não alterar o contrato dos requests originais de
  `api.http` (que não enviam nenhuma credencial). Recomendação: definir
  `ADMIN_API_KEY` (ou um mecanismo de auth mais robusto) em qualquer ambiente
  real antes de expor a API além do desenvolvimento local.
