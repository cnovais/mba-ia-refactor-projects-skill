================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   14 analyzed | ~1158 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 6 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Secret Key
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` is a literal string committed to source instead of being read from an environment variable.
Impact: Anyone with repo read access gets the Flask signing key, which (if sessions/CSRF tokens are ever added, as the presence of `SECRET_KEY` implies is planned) lets them forge signed cookies/tokens.
Recommendation: Move to a config module that reads `SECRET_KEY` from the environment (`os.environ`/`python-dotenv`, already a declared but unused dependency), with no hardcoded fallback in production.

### [CRITICAL] Hardcoded SMTP Credentials
File: services/notification_service.py:7-10
Description: `email_host`, `email_user='taskmanager@gmail.com'` and `email_password='senha123'` are hardcoded inside `NotificationService.__init__`.
Impact: Full mailbox credentials are exposed to anyone reading the repo; if this account is real, it can be used to send mail as the app or read its inbox.
Recommendation: Extract SMTP host/user/password into environment-backed config and inject them into `NotificationService` via its constructor instead of hardcoding.

### [CRITICAL] No Authentication/Authorization on Any Mutating Endpoint
File: routes/task_routes.py:85-238, routes/user_routes.py:42-211, routes/report_routes.py:167-223
Description: Every `POST`/`PUT`/`DELETE` route (create/update/delete task, user, category) executes with zero authentication or authorization check. `POST /login` (user_routes.py:185-211) returns `'token': 'fake-jwt-token-' + str(user.id)` (line 210), but this token is never generated as a real JWT and is never validated by any other route — it's decorative. `User.is_admin()` (models/user.py:34-38) is defined but never called anywhere in the codebase, so the existing `role` field enforces nothing.
Impact: Any anonymous caller can delete any user (which cascades to delete all of that user's tasks, user_routes.py:140-151), delete any task or category, or promote/edit any account — a complete authorization bypass on the entire write surface of the API.
Recommendation: Add a real auth mechanism (e.g. Flask-JWT-Extended or session-based auth) that issues verifiable tokens on login, and enforce it with a decorator/middleware on every mutating route; use the already-defined `is_admin()` to gate admin-only actions.

### [HIGH] Business Logic Duplicated in Controllers Instead of Using the Model
File: routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180; routes/report_routes.py:34-43, 132-135
Description: The exact same "is this task overdue" logic (`due_date < datetime.utcnow() and status not in ('done','cancelled')`) is hand-rolled inline as nested `if` statements in five separate route handlers, even though `Task.is_overdue()` (models/task.py:50-60) already implements it and is never called from anywhere.
Impact: The rule now has five copies to keep in sync; a future change to the overdue definition (e.g. adding a grace period) requires editing five call sites, and it's easy to miss one, producing inconsistent `overdue` flags across endpoints.
Recommendation: Delete the inline duplicates and call `task.is_overdue()` from each handler (or serialize it inside `Task.to_dict()` so every endpoint gets it for free).

### [HIGH] Weak/Homemade Password Hashing
File: models/user.py:27-32
Description: `set_password`/`check_password` hash the raw password with unsalted `hashlib.md5`.
Impact: MD5 is fast and unsalted — passwords are crackable in bulk via rainbow tables/GPU brute force the moment the `users` table leaks; two users with the same password get identical hashes, leaking that fact too.
Recommendation: Replace with a slow, salted password hash (bcrypt, scrypt, or argon2 via `werkzeug.security.generate_password_hash`/`check_password_hash`, which Flask already pulls in transitively).

### [HIGH] Dead Service With No Dependency Injection
File: services/notification_service.py:1-49
Description: `NotificationService` is defined but never instantiated or imported anywhere else in the codebase (`grep` for `NotificationService` matches only its own class definition) — task assignment (task_routes.py create/update) and overdue detection never call `notify_task_assigned`/`notify_task_overdue`. Even if wired in, it builds its own concrete `smtplib.SMTP` client inline (line 15) rather than receiving a mail client as a dependency.
Impact: The notification feature the domain clearly intends to have (task assignment, overdue alerts) silently does nothing — users are never actually notified — and the module can't be unit tested without a real SMTP server even after it's wired up.
Recommendation: Either call this service from the task-assignment and overdue-check flows, or remove it if the feature is out of scope; if kept, inject the SMTP client/config instead of constructing it inside `__init__`.

### [MEDIUM] N+1 Queries When Listing Tasks, Categories, and Building Reports
File: routes/task_routes.py:41-57; routes/report_routes.py:53-68, 159-165
Description: `get_tasks()` runs one `User.query.get(...)` and one `Category.query.get(...)` per task inside the result loop; `summary_report()` runs `Task.query.filter_by(user_id=u.id)` once per user inside its loop; `get_categories()` runs `Task.query.filter_by(category_id=c.id).count()` once per category inside its loop.
Impact: Response time for `/tasks`, `/reports/summary`, and `/categories` grows linearly with the number of tasks/users/categories instead of staying flat, turning cheap list endpoints into slow ones as real data accumulates.
Recommendation: Replace the per-row queries with a single eager-loaded query (`joinedload`/`selectinload` on the `user`/`category` relationships) or one aggregated `GROUP BY` query for the counts.

### [MEDIUM] Duplicated and Dead Validation Logic
File: routes/task_routes.py:96-114, 166-184; routes/user_routes.py:61, 106; utils/helpers.py:19-23, 57-116; routes/report_routes.py:196-202
Description: Title-length/status/priority validation is copy-pasted almost verbatim between `create_task` and `update_task`; the email regex is copy-pasted between `create_user` and `update_user`. Meanwhile `utils/helpers.py` already defines a *third*, unused copy of this logic (`validate_email`, `process_task_data`, `VALID_STATUSES`, `VALID_ROLES`, `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `DEFAULT_PRIORITY`) that no route imports (only `format_date`/`calculate_percentage` are imported, and per a repo-wide grep even those two are never actually called). Separately, `update_category` (report_routes.py:196-202) is missing the `if not data: return ...400` guard every sibling update handler has, so a request with no JSON body raises an unhandled `TypeError` on `'name' in data` instead of a clean 400.
Impact: A validation rule fixed in one copy (e.g. tightening the email regex) silently stays broken in the other two; the `update_category` gap means malformed requests get an opaque Flask 500/stack trace instead of a proper error response.
Recommendation: Delete the dead code in `utils/helpers.py` or make it the single source of truth (import `VALID_STATUSES`/`process_task_data`/`validate_email` from there in both route files), and add the missing `if not data` guard to `update_category`.

### [MEDIUM] Inconsistent, Silent Error Handling
File: task_routes.py:62, 137, 204, 236; user_routes.py:130, 149; report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88
Description: Twelve bare `except:` blocks swallow the real exception entirely (no logged type/traceback), several returning a generic `{'error': 'Erro interno'}`/`{'error': 'Erro ao atualizar'}`. Where an exception *is* captured (`except Exception as e:` in task_routes.py:151/221, user_routes.py:87), it's routed to `print(f"...{str(e)}")` (task_routes.py:153, 219; user_routes.py:89, 147; notification_service.py:24) rather than a real logger.
Impact: Production incidents are undebuggable — there is no way to tell *why* a create/update/delete failed after the fact, since nothing captures the exception type, traceback, or a timestamped log record.
Recommendation: Replace bare `except:` with `except Exception as e:`, log via Python's `logging` module (with traceback) instead of `print`, and centralize this into a Flask error handler (`@app.errorhandler`) instead of repeating try/except in every route.

### [MEDIUM] Deprecated API Usage
File: models/task.py:15-16, 52; models/user.py:14; app.py:24; routes/task_routes.py (multiple); routes/user_routes.py (multiple); routes/report_routes.py (multiple) — 22 occurrences total; also every `Model.query.get/.all/.filter_by` call (56 occurrences repo-wide); also app.py:34
Description: (1) `datetime.utcnow()` is used 22 times across models, app.py, and all three route files — deprecated since Python 3.12. (2) The legacy Flask-SQLAlchemy `Model.query.get/.all/.filter_by` API is used in all 56 query call sites in the codebase — this `Query` API is legacy under SQLAlchemy 2.x. (3) `app.run(debug=True, host='0.0.0.0', port=5000)` (app.py:34) runs Flask's built-in dev server with debug mode as the app's only entry point.
Impact: (1) `datetime.utcnow()` returns a naive datetime with no tzinfo, which is easy to mismatch against timezone-aware values and is slated for removal; (2) the legacy `Query` API is on a deprecation path and blocks adopting SQLAlchemy 2.0-style sessions cleanly; (3) `debug=True` exposes the interactive Werkzeug debugger (arbitrary code execution) if an unhandled exception ever reaches it, and the dev server isn't built for concurrent/production traffic.
Recommendation: Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`; migrate queries to `db.session.get(Model, id)` / `db.session.execute(select(...))`; run via a production WSGI server (gunicorn/waitress) with `debug` driven by an environment variable defaulting to `False`.

### [LOW] Cryptic Single-Letter Identifiers
File: routes/task_routes.py:16, 268; routes/user_routes.py:14, 37, 161; routes/report_routes.py:33, 55, 59, 119, 161
Description: Loop variables and lookups are named `t` (task), `u` (user), `c`/`cat` (category), `e` (exception), `p` (password/priority depending on context) throughout the three route files instead of descriptive names.
Impact: Purely cosmetic today, but forces every future reader to trace usage back to infer what `t`/`u`/`c` actually holds in each function.
Recommendation: Rename to `task`, `user`, `category`, etc. during the Phase 3 restructuring pass.

### [LOW] Magic Numbers for Priority Levels
File: routes/report_routes.py:24-28, 84-89, 117, 129; models/task.py:45-48
Description: Priority is a bare integer 1-5 compared/branched on directly (`priority <= 2`, `p1`..`p5` mapped positionally to `'critical'..'minimal'`) with no named levels, even though `utils/helpers.py:115` already defines `DEFAULT_PRIORITY` as a start toward named constants.
Impact: The mapping from priority number to business meaning ("1 = critical") exists only implicitly in variable ordering; a reordering or off-by-one bug in these lines would silently mislabel the report with no error.
Recommendation: Introduce a `PRIORITY_LABELS = {1: 'critical', 2: 'high', ...}` constant (or an enum) and use it everywhere priority is displayed or compared.

================================
Total: 14 findings
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

## Notas de execução da Fase 3

**Nova estrutura:** `models/` (persistência + invariantes), `controllers/` (casos de
uso), `routes/` (roteamento fino), `validators/` (regras de payload reaproveitadas
por create/update), `config/settings.py` (toda config lida de env, via `python-dotenv`
— antes uma dependência declarada e nunca usada), `middlewares/error_handler.py`
(handler central: `ApiError` → status/mensagem específicos, `HTTPException` → repassa
código, `Exception` → log + 500 genérico, substituindo os 12 `except:` mudos
espalhados pelas rotas), `auth/tokens.py` (token de login assinado via
`itsdangerous`), `errors.py` (a exceção `ApiError` usada por todos os controllers).
`services/notification_service.py` teve suas credenciais SMTP removidas do código e
passou a receber configuração por injeção.

**Findings resolvidos:** os 3 CRITICAL de segredo hardcoded (`SECRET_KEY`,
credenciais SMTP) e o HIGH de hashing fraco (MD5 → `werkzeug.security` com salt),
os 3 pontos de N+1 (joins/agrupamento único em vez de query por item), a
duplicação/validação morta (helpers antes nunca importados agora são a única fonte
de validação), o tratamento de erro silencioso/inconsistente, as APIs depreciadas
(`datetime.utcnow()` → `utc_now()` naive-UTC consistente com as colunas do banco,
`Model.query.get()` → `db.session.get()`, `app.run(debug=True)` fixo → controlado por
`FLASK_DEBUG`), a lógica de "task atrasada" duplicada em 5 lugares (agora só em
`Task.is_overdue()`), e os nomes/números mágicos (loop vars renomeadas, prioridades
mapeadas via `PRIORITY_LABELS`). Como efeito colateral positivo, endpoints que antes
tinham serialização inconsistente (`overdue` ausente em alguns, `user_name`/
`category_name` ausentes em outros) passaram a ser consistentes — mudança aditiva
(nenhum campo removido/renomeado), sem impacto em clientes bem-formados.

**Os 3 itens antes adiados foram resolvidos a pedido explícito do usuário**, cada um
mudando o contrato para casos que antes eram inseguros (não são mais "requisições
bem-formadas" no sentido antigo — isso é a correção pretendida):

- **CRITICAL — Autenticação/autorização.** `auth/decorators.py` adiciona
  `login_required` (exige `Authorization: Bearer <token>` válido, expõe
  `flask.g.current_user`) e `admin_required` (`login_required` + `User.is_admin()`).
  Aplicados a toda rota de escrita: `POST/PUT/DELETE /tasks`, `POST/PUT/DELETE
  /categories`, `PUT /users/<id>` (`login_required`) e `DELETE /users/<id>`
  (`admin_required`, pois cascateia deletando as tasks do usuário). `POST /users`
  (cadastro) e `POST /login` continuam públicos — não há sessão antes de existir.
  Em `user_controller.update_user`, `is_admin()` também passou a ser usado de fato:
  só o próprio usuário ou um admin pode editar um perfil, e só um admin pode
  alterar `role` (sem isso, um usuário autenticado poderia editar a senha de
  qualquer outra conta ou se autopromover a admin).
- **HIGH — `NotificationService` nunca era chamado.** `NotificationService` passou a
  receber apenas valores primitivos (`user_email`, `task_title`, ...) em vez de
  objetos ORM — necessário porque agora é chamado a partir de uma `threading.Thread`
  em segundo plano (`task_controller._notify_assignment_async`), e uma sessão do
  SQLAlchemy não pode atravessar threads/tempo de vida da requisição sem risco de
  `DetachedInstanceError` ou corrida de dados. `create_task`/`update_task` disparam
  a notificação em background sempre que uma task é (re)atribuída a um `user_id` —
  a resposta HTTP não espera o SMTP, então nem uma configuração ausente nem um
  servidor lento adicionam latência à requisição (confirmado: POST /tasks com
  atribuição respondeu em ~15ms).
- **`User.to_dict()` não retorna mais `password`.** Removido de
  `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. Nada no
  código depende desse campo internamente (só era exposto na resposta).

**Validação executada nesta sessão (após as 3 correções):** app subiu sem erros
(porta 5050 por conflito local com AirPlay na 5000); `seed.py` populou o banco sem
warnings. Fluxos exercitados via `curl`:
- `POST /tasks`/`/categories`/`PUT /tasks/<id>` sem token → 401; com token → 200/201.
- Login como admin (`joao`) e como usuário comum (`maria`) com tokens distintos.
- `maria` editando o próprio perfil → 200; editando `joao` → 403; tentando virar
  `admin` → 403; deletando outro usuário → 403 (`admin_required`); `joao` (admin)
  deletando → 200.
- Token malformado em rota protegida → 401 "Token inválido ou expirado".
- `GET /tasks`, `/users/<id>`, etc. continuam públicos e sem `password` no payload.
- Notificação assíncrona confirmada no log do servidor ("SMTP not configured —
  skipping email to maria@email.com: Nova task atribuída: ...") sem atraso na
  resposta.

Todos os endpoints e casos de erro responderam com o status/formato esperado.
Servidor de validação encerrado e `tasks.db`/`__pycache__`/`.env.bak` locais
removidos ao final.
