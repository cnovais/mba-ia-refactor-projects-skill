================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.14 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.0.52, SQLite)
Files:   14 analyzed | ~1059 lines of code (plus seed.py and requirements.txt reviewed as supporting files)

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 9 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets
File: app.py:11-13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` (app.py:13) and the DB URI `'sqlite:///tasks.db'` (app.py:11) are literals in the entry point. `NotificationService.__init__` hardcodes the SMTP account `email_user = 'taskmanager@gmail.com'` / `email_password = 'senha123'` (notification_service.py:9-10) together with host/port (lines 7-8). `python-dotenv` is declared in requirements.txt but never imported, so nothing is read from the environment.
Impact: Anyone with read access to the repo gets the Flask signing key (every install shares it, so any signed session/cookie can be forged) and the full mailbox credentials of the notification account.
Recommendation: Create a config module that reads every secret from environment variables with **no** literal fallback (refuse to boot, or generate a random per-process value and log it), ship a `.env.example` with empty secret values, and inject SMTP settings into `NotificationService` through its constructor.

### [CRITICAL] Sensitive Data Exposure — password hash returned by the API
File: models/user.py:16-25 (line 21), routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` includes `'password': self.password` (the stored MD5 hash). That dict is returned as-is by `GET /users/<id>` (user_routes.py:33), `POST /users` (line 85), `PUT /users/<id>` (line 129) and `POST /login` (line 209). Only `GET /users` (lines 15-23) builds its own dict without the hash.
Impact: Any caller (there is no auth, see below) can harvest every user's unsalted MD5 hash by iterating `/users/<id>`, then crack them offline in seconds (seed passwords are `1234`, `abcd`, `pass`).
Recommendation: Never serialize the password field — remove it from `to_dict()` (or use a dedicated public serializer) so no response shape ever contains it.

### [CRITICAL] Authentication Bypass — token issued but never verified
File: routes/user_routes.py:207-211
Description: `POST /login` returns `'token': 'fake-jwt-token-' + str(user.id)` (line 210) — a predictable string, not a signed token. No route in the codebase reads an `Authorization` header or validates this token; `User.is_admin()` (models/user.py:34-38) is never called anywhere. The credential check in login therefore protects nothing: every protected action is reachable without it.
Impact: Anyone can act as any account — the token can be forged for any user id (`fake-jwt-token-1` is the seed admin), and in practice no token is even needed.
Recommendation: Issue a real signed token (e.g. JWT signed with the env-provided secret, `Flask-JWT-Extended` is already installed in the venv) and enforce it with a decorator on every route that needs it, rejecting missing/garbage/forged tokens with 401 and wrong roles with 403.

### [CRITICAL] Unauthenticated Dangerous Endpoints / Privilege Escalation
File: routes/user_routes.py:42-151, routes/task_routes.py:225-238, routes/report_routes.py:211-223
Description: `DELETE /users/<id>` (user_routes.py:134-151) deletes a user and all their tasks (lines 140-142); `PUT /users/<id>` (lines 92-132) lets the caller set `role` (line 119-122) and `active` (line 124-125) on any account; `POST /users` (lines 42-90) accepts `role: 'admin'` from the request body (line 52, 71). `DELETE /tasks/<id>` and `DELETE /categories/<id>` are equally open. None of them has any authentication or authorization check.
Impact: An anonymous caller can self-register as admin, promote/deactivate any account, and irreversibly wipe users, tasks and categories.
Recommendation: Gate all mutating routes behind the auth decorator; restrict role changes and user deletion to admins; ignore/forbid `role` on self-registration (default to `user`).

### [HIGH] God Module (partial) — routes hold routing, validation, business rules, persistence and serialization
File: routes/task_routes.py:1-299, routes/user_routes.py:1-211, routes/report_routes.py:1-223 (categories CRUD at 157-223)
Description: The project has `models/`, `routes/`, `services/` folders, but there is no controller layer: each route handler parses the request, validates, queries the DB, applies rules, commits and hand-builds the response. `report_routes.py` additionally owns the entire `/categories` CRUD (lines 157-223), which has nothing to do with reporting — the file's job can't be described in one sentence.
Impact: Business rules can only be tested through HTTP; changing category behaviour means editing the reports blueprint, and any change to one concern risks breaking others in the same handler.
Recommendation: Introduce `controllers/` (task, user, category, report) holding the flow, keep routes as thin views, and move categories into their own blueprint/controller.

### [HIGH] Business Logic Trapped in Routes (duplicated "overdue" rule, aggregations, cascades)
File: routes/task_routes.py:30-39, 71-80, 283-287; routes/user_routes.py:140-142, 171-180; routes/report_routes.py:12-155 (overdue at 33-43, 132-135)
Description: The "overdue" rule (due_date in the past and status not done/cancelled) is re-implemented inline six times, even though `Task.is_overdue()` already exists (models/task.py:50-60) and is never called. Completion-rate math, per-user productivity and per-status/priority aggregations live directly in the report handlers; the user-delete cascade over tasks lives in the route.
Impact: A rule change (e.g. a new terminal status) must be applied in six places and will silently drift; none of it can be unit-tested without the HTTP layer.
Recommendation: Use `Task.is_overdue()` everywhere, move aggregations into model/controller functions (e.g. a report controller using grouped queries), and move the cascade into the model relationship (`cascade='all, delete-orphan'`) or controller.

### [HIGH] Weak Cryptography — unsalted MD5 password hashing
File: models/user.py:27-32
Description: `set_password` stores `hashlib.md5(pwd.encode()).hexdigest()`; `check_password` compares MD5 digests with `==`.
Impact: Unsalted MD5 is cracked at billions of guesses per second / via rainbow tables — combined with the hash leak above, every password is recoverable. The plain `==` also isn't constant-time.
Recommendation: Use `werkzeug.security.generate_password_hash` / `check_password_hash` (already a Flask dependency) or bcrypt/argon2; rehash on next successful login for existing rows.

### [HIGH] Tight Coupling / No Dependency Injection
File: app.py:9-31, seed.py:2, services/notification_service.py:5-20
Description: `app` is a module-level singleton configured with literals and runs `db.create_all()` at import time (app.py:30-31); there is no application factory, so `seed.py` (line 2) and any test must import the live app and its side effects. `NotificationService` hardcodes its SMTP config and opens `smtplib.SMTP(...)` inline (line 15) with no way to substitute a fake transport.
Impact: Tests can't create an app with a different DB/config, importing the app touches the real `tasks.db`, and the notification service can't be unit-tested without a real SMTP server.
Recommendation: Add `create_app(config)` as the composition root, call `create_all` from it (or migrations), and inject the SMTP settings/transport into `NotificationService`.

### [MEDIUM] N+1 Query Pattern / redundant queries
File: routes/task_routes.py:41-57, 275-281; routes/user_routes.py:22; routes/report_routes.py:15-30, 55-56, 161-163
Description: `GET /tasks` runs `User.query.get` and `Category.query.get` per task (task_routes.py:42, 51); `GET /users` lazy-loads `u.tasks` per user (user_routes.py:22); the summary report queries tasks per user (report_routes.py:56) and `GET /categories` counts tasks per category (line 163). `/tasks/stats` and `/reports/summary` fire 5 and 12 separate `count()` queries and then still load every task into memory (task_routes.py:275-281, report_routes.py:15-30).
Impact: Query count grows linearly with tasks/users/categories; these endpoints slow down sharply with real data.
Recommendation: Use eager loading (`joinedload`/`selectinload`) for the relationships and `GROUP BY` aggregate queries for counts.

### [MEDIUM] Duplicated / Missing Route-Level Validation
File: routes/task_routes.py:92-114, 166-184, 260-264; routes/user_routes.py:61-72, 102-125; routes/report_routes.py:196-202; utils/helpers.py:57-108
Description: Title/status/priority checks are copy-pasted between create and update task (task_routes.py:92-114 vs 166-184) and the email regex/role list between create and update user (user_routes.py:61, 71 vs 106, 120), while `process_task_data`/`validate_email`/`is_valid_color` in utils/helpers.py are never used. Gaps: `priority` isn't type-checked, so `"priority": "2"` raises `TypeError` at task_routes.py:113/182 → unhandled 500; `?priority=abc` / `?user_id=abc` raise `ValueError` at lines 261/264 → 500; `PUT /categories/<id>` with no JSON body crashes on `'name' in None` (report_routes.py:196-197) and never validates `color`; user `name`/`active` on update are unchecked (user_routes.py:102-103, 124-125); minimum password length is 4 (lines 64, 115).
Impact: Malformed input produces 500s instead of 400s, and fixes to one copy of a rule don't reach the other.
Recommendation: Centralize validation in one place per resource (validator module or marshmallow schemas — marshmallow is already a declared dependency) and reuse it in create and update.

### [MEDIUM] Inconsistent / Silent Error Handling
File: routes/task_routes.py:62, 137, 151-154, 204, 221-223, 236; routes/user_routes.py:87-90, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88; services/notification_service.py:23-25
Description: Bare `except:` blocks swallow the real error in 12 places; errors are "logged" with `print()` (e.g. task_routes.py:153, user_routes.py:89, notification_service.py:24); only `GET /tasks` wraps its body in try/except, every other handler lets exceptions escape as Flask's default HTML 500; there is no `errorhandler` registered.
Impact: Production failures leave no usable trace, error response format differs per route, and unexpected exceptions return HTML instead of the API's JSON shape.
Recommendation: Register centralized JSON error handlers (and a domain error class), use `logging` instead of `print`, and catch only specific exceptions where recovery is meaningful.

### [MEDIUM] Duplicated Serialization Logic
File: routes/task_routes.py:16-28, routes/user_routes.py:15-23, 162-169
Description: `GET /tasks` rebuilds the full task dict field by field, duplicating `Task.to_dict()` (models/task.py:23-36); `GET /users` and `GET /users/<id>/tasks` build their own partial dicts instead of using the model serializers.
Impact: Adding/renaming a field requires editing several places, and response shapes for the same entity already differ between endpoints.
Recommendation: Keep serialization on the model (`to_dict()` with optional extras) and reuse it in every handler, preserving the current response shapes.

### [MEDIUM] Misconfigured Middleware — CORS open to every origin
File: app.py:15
Description: `CORS(app)` with no options allows any origin to call every route.
Impact: Combined with the absent authentication, any website a user visits can call the API's destructive endpoints from the browser.
Recommendation: Read allowed origins from config (`CORS(app, origins=config.CORS_ORIGINS)`).

### [MEDIUM] Deprecated API — `datetime.utcnow()`
File: models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74
Description: `datetime.utcnow()` is deprecated since Python 3.12 and the project runs on Python 3.14.3.
Impact: Emits `DeprecationWarning` on every call and returns naive datetimes that are easy to mix with local time; it will be removed in a future Python.
Recommendation: Use `datetime.now(timezone.utc)` through a single helper (keeping stored values comparable to existing naive rows).

### [MEDIUM] Deprecated API — legacy `Model.query.get()`
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: `Query.get()` is the legacy SQLAlchemy 1.x API; on SQLAlchemy 2.0.52 it raises `LegacyAPIWarning`.
Impact: Will break when the legacy Query API is removed and keeps the codebase on a deprecated idiom.
Recommendation: Replace with `db.session.get(Model, id)`.

### [MEDIUM] Deprecated Practice — framework dev server with debug on all interfaces
File: app.py:33-34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` is the only way the app is started.
Impact: The Werkzeug debugger (interactive console, PIN-protected) and full tracebacks are exposed on every network interface; the dev server isn't built for production traffic.
Recommendation: Drive debug/host/port from config (debug off by default) and run under a production WSGI server (gunicorn) outside development.

### [MEDIUM] Outdated / Unused Pinned Dependencies
File: requirements.txt:1-6
Description: `flask==3.0.0`, `flask-cors==4.0.0` and `requests==2.31.0` are pinned to old releases that have since received security fixes (flask-cors 4.0.0 has published advisories, e.g. CVE-2024-1681/CVE-2024-6221; requests < 2.32.0 is affected by CVE-2024-35195). `marshmallow`, `requests` and `python-dotenv` are declared but never imported.
Impact: Known vulnerabilities ship with every install, and unused packages widen the attack surface for nothing.
Recommendation: Bump to the latest compatible releases and drop dependencies that aren't used (or start using `python-dotenv`/`marshmallow` as recommended above).

### [LOW] Magic Numbers & Strings
File: routes/task_routes.py:110, 113, 177, 182; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:24-28, 84-88, 129; models/task.py:39, 46
Description: Status list `['pending', 'in_progress', 'done', 'cancelled']`, role list, priority bounds `1`/`5`, `t.priority <= 2` as "high priority", and the `p1..p5 → critical/high/medium/low/minimal` mapping are inline literals; the named constants `VALID_STATUSES`, `VALID_ROLES`, `MIN_PASSWORD_LENGTH`, etc. in utils/helpers.py:110-116 exist but are never used.
Impact: Readers must reverse-engineer what each number means, and the literals already diverge from nothing more than luck.
Recommendation: Define statuses/roles/priorities once (constants or enums on the models) and reference them everywhere.

### [LOW] Poor Naming
File: routes/task_routes.py:16, 51; routes/user_routes.py:14; routes/report_routes.py:24-28, 55, 161; models/category.py:14; models/task.py:45
Description: Single/short identifiers for domain objects — `t`, `u`, `c`, `cat`, `d`, `p`, `p1`…`p5`.
Impact: Harder to read and search; `p` for priority and `p1` for "count of critical tasks" are easy to confuse.
Recommendation: Use descriptive names (`task`, `user`, `category`, `critical_count`).

### [LOW] Dead Code and Unused Imports
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3, 38-60; models/user.py:34-38; utils/helpers.py:2-108; services/notification_service.py:1-48
Description: Unused imports (`os, sys, json` in app.py; `json, os, sys, time` in task_routes.py; `hashlib, json` in user_routes.py; `format_date, calculate_percentage, json` in report_routes.py; `os, json, sys, math, hashlib` in helpers.py). Never-called code: every function in utils/helpers.py, `Task.validate_status/validate_priority/is_overdue`, `User.is_admin`, and the whole `NotificationService`.
Impact: Readers assume this code is live (e.g. that validation helpers are applied) when it isn't; it rots silently.
Recommendation: Remove what isn't needed and wire in what should be used (`is_overdue`, `is_admin`, validators).

### [LOW] Verbose / Non-idiomatic Conditionals
File: models/user.py:34-38; models/task.py:38-60; routes/task_routes.py:141, 210; utils/helpers.py:103
Description: `if cond: return True else: return False` patterns, the 4-level nested `if` in `is_overdue`, and `type(tags) == list` instead of `isinstance`.
Impact: More code to read for trivial logic; `type(...) ==` rejects list subclasses.
Recommendation: Return boolean expressions directly and use `isinstance`.

================================
Total: 21 findings
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

Fase 3 executada após confirmação humana. Evidências da validação em runtime:
- **Boot:** `python app.py` (Flask 3.1.3, Python 3.14.3, `PYTHONWARNINGS=default`) sobe sem erros nem `DeprecationWarning`, debug desligado, bind em `127.0.0.1`.
- **Secret ausente:** com `SECRET_KEY` não definida (e também só com espaços), `app.py` e `seed.py` encerram com `Configuration error: SECRET_KEY environment variable is required…` (exit 1) — não existe fallback literal (grep em `config/`, `app.py`, `auth/`, `services/`: só `DATABASE_URL` e `HOST` têm default, ambos não-secretos). `.env.example` traz `SECRET_KEY=`, `SMTP_USER=` e `SMTP_PASSWORD=` vazios. Como o app não sobe sem o secret, o gate não tem estado "aberto"; além disso `auth/tokens.py` nega (401) se o `SECRET_KEY` estiver vazio.
- **Gates:** as 18 rotas protegidas responderam 401 sem token, com token lixo, com o antigo `fake-jwt-token-1` e com token forjado (assinado com outra chave); rotas de admin responderam 403 para usuário comum, e o `DELETE /users` negado não alterou nada; usuário desativado tem o token recusado (401).
- **Credenciais:** login com senha errada para conta existente → 401 `Credenciais inválidas` (mesma mensagem para e-mail inexistente), login correto → 200 com `{message, user, token}`; após troca de senha a senha antiga é recusada; auto-cadastro com `role: admin` → 403.
- **Contrato preservado:** 20 endpoints de leitura comparados lado a lado com o código legado (staged no git) sobre a mesma cópia do banco — respostas idênticas (status e corpo, ignorando timestamps), exceto pela remoção do campo `password`. Script de 130 verificações (CRUD completo de tasks/users/categories, busca, stats, relatórios, erros 400/404/409) passou sem falhas.
- **Servidores de validação** encerrados e o banco de teste (`instance/`) removido ao final.

Resolução dos findings:
- Resolvidos: todos os CRITICAL e HIGH; N+1 (eager loading + consultas agrupadas), validação centralizada em `validators/`, error handler central + `logging`, serialização única nos models, CORS via `CORS_ORIGINS`, `datetime.utcnow()` → `utils.helpers.utcnow()` (baseado em `datetime.now(timezone.utc)`), `Query.get()` → `db.session.get()`, servidor de dev configurável (debug off por padrão, `gunicorn "app:create_app()"` documentado), dependências atualizadas (Flask 3.1.3, flask-cors 6.0.5, python-dotenv 1.2.4) e removidas as não usadas (`marshmallow`, `requests`), constantes nomeadas, nomes descritivos, código morto/imports não usados removidos (verificado por varredura AST).
- **Finding retratado:** "Referential Integrity — deleting a category orphans its tasks" (MEDIUM) foi removido deste relatório — o teste em runtime no código legado mostrou que o relacionamento SQLAlchemy (`backref='tasks'`) já define `category_id = NULL` ao deletar a categoria. Era um falso positivo da Fase 2; a regra agora é explícita em `Task.detach_category`.
- **Adiados (decisão de produto):** tamanho mínimo de senha mantido em 4 (o seed e clientes atuais dependem disso); `NotificationService` mantido injetável mas ainda não acionado pelas rotas (o original nunca enviava e-mails — ligá-lo mudaria o comportamento); sem migrations (`db.create_all()` continua no `create_app`). A regex de e-mail passou a exigir domínio com TLD (`a@b` deixa de ser aceito).
