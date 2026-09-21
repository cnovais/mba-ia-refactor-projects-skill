# Refactoring Playbook

Used in Phase 3. One recipe per anti-pattern from `02-antipattern-catalog.md`, numbered
to match. Each recipe is independent — apply only the ones a given project actually needs
(see the architecture guidelines' note on partially organized projects). The before/after
snippets show the *shape* of the transformation; adapt syntax to the actual language of
the project you're refactoring, don't transplant Python into a JS file or vice versa.

## 1. God Class / God Module → split by domain, one file per responsibility

**Before** (`models.py` doing everything for every domain):
```python
# models.py — 350 lines, produtos + usuarios + pedidos all mixed with raw SQL
def get_todos_produtos(): ...
def criar_usuario(nome, email, senha): ...
def criar_pedido(usuario_id, itens): ...
```

**After:**
```
models/
├── produto_model.py     # only product persistence
├── usuario_model.py      # only user persistence
└── pedido_model.py        # only order persistence
controllers/
├── produto_controller.py  # product use cases
├── usuario_controller.py
└── pedido_controller.py
```
Each new file exports only the functions/classes for its own domain. A change to order
logic can no longer accidentally break product logic because they no longer share a file.

## 2. Hardcoded Credentials → config module reading from environment

**Before:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**After:**
```python
# config/settings.py
import os
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

# app.py
from config import settings
app.config["SECRET_KEY"] = settings.SECRET_KEY
```
Add a `.env.example` documenting the required variables (with placeholder, never real
values) so the config contract is discoverable without exposing a real secret. Never log
or return a secret in an API response.

## 3. SQL Injection → parameterized queries everywhere

**Before:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**After:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```
Apply this to every query in the file, including `INSERT`/`UPDATE`/`DELETE` built with
string concatenation — there is no safe amount of user input concatenated into SQL.

## 4. Unauthenticated Dangerous Endpoint → remove or gate behind auth + explicit allowlisting

**Before:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)   # arbitrary SQL, no auth check
```

**After:** delete the endpoint if it has no legitimate product purpose (this one exists
purely as a backdoor); if an equivalent capability is genuinely needed (e.g. an internal
reporting query), replace free-form SQL with a fixed set of named, parameterized queries
behind an authentication + authorization check, never a raw SQL string from the request
body.

**The auth gate itself must fail closed.** When the check depends on a secret read from
config/environment (an admin token/API key), missing configuration must deny the request,
never let it through. A gate that no-ops and lets the request proceed whenever the secret
isn't set — even "temporarily, to keep an existing demo/collection working unchanged" —
reproduces the exact same CRITICAL under a new name, because an unset env var is the
out-of-the-box state most deployments start from (see `.env.example`/README defaults).

```python
# Anti-pattern: permissive no-op when the secret is unset
def reset_database():
    token = request.headers.get("X-Admin-Token")
    if not settings.ADMIN_TOKEN:
        logger.warning("ADMIN_TOKEN not set — allowing request unauthenticated")
        return do_reset()          # falls through to the dangerous action
    if token != settings.ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 403
    return do_reset()
```

```python
# Fail closed: missing config disables the route instead of opening it
def reset_database():
    token = request.headers.get("X-Admin-Token")
    if not settings.ADMIN_TOKEN or token != settings.ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 403   # 403 either way
    return do_reset()
```

If gating the route breaks an existing demo/collection request that never sent
credentials (e.g. `api.http`), that's the finding surfacing through the demo, not a
reason to leave the route open — update the demo request and document the new
credential requirement (`.env.example`, README) instead of loosening the gate.

## 5. Business Logic in Controllers/Routes → extract into the controller/service layer

**Before** (route handler doing validation, persistence, and notification fan-out inline):
```python
def criar_pedido():
    ...
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]))
    print("ENVIANDO SMS: ...")
    return jsonify(resultado), 201
```

**After:**
```python
# controllers/pedido_controller.py
def criar_pedido(usuario_id, itens):
    pedido = PedidoModel.criar(usuario_id, itens)
    notification_service.notify_new_order(pedido)
    return pedido

# routes/pedido_routes.py
@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido_route():
    dados = request.get_json()
    pedido = pedido_controller.criar_pedido(dados["usuario_id"], dados["itens"])
    return jsonify(pedido), 201
```
The route stays a thin adapter; the controller owns the use case; notification concerns
move into their own module instead of being three `print` calls.

## 6. Tight Coupling / No DI → inject dependencies instead of constructing them inline

**Before:**
```javascript
class AppManager {
    constructor() {
        this.db = new sqlite3.Database(':memory:'); // hardcoded, untestable
    }
}
```

**After:**
```javascript
class AppManager {
    constructor(db) {
        this.db = db; // caller decides real DB vs. test double
    }
}
// composition root:
const db = createDatabase(config.dbPath);
const manager = new AppManager(db);
```
The same idea applies in Python: pass a `db` connection/session into a model/repository's
constructor or function signature instead of importing a module-level global.

## 7. Mutable Global State → scope state to the request/app context

**Before:**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path)
    return db_connection
```

**After (Flask idiom — app/request-scoped resource):**
```python
from flask import g
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```
For a plain cache/counter (like a Node `globalCache` object), scope it inside a class
instance created at the composition root and passed to whoever needs it, instead of a
bare module-level mutable object every request can reach into.

## 8. Weak / Homemade Cryptography → real password hashing library

**Before:**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**After:**
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)  # salted, slow hash (scrypt/pbkdf2)
# ...
check_password_hash(self.password, candidate_pwd)
```
For the Node.js "badCrypto" case, replace it entirely with `bcrypt.hash`/`bcrypt.compare`
(or `argon2`) — there is no salvageable part of a hand-rolled hash loop.

## 9. N+1 Queries → batch/join instead of per-item queries

**Before:**
```python
for item in itens:
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
```

**After:**
```python
ids = [item["produto_id"] for item in itens]
placeholders = ",".join("?" for _ in ids)
cursor.execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids)
produtos_by_id = {row["id"]: row for row in cursor.fetchall()}
```
For nested-callback Node code doing the same thing per row, replace the per-row query with
one `SELECT ... WHERE id IN (...)` (or a proper `JOIN`) executed once, and build the
response from the joined result.

## 10. Missing/Duplicated Validation → one schema/validator reused by every route

**Before:** the same 6-line block of `if "nome" not in dados: return ...` copy-pasted into
`criar_produto` and `atualizar_produto`.

**After:**
```python
# validators/produto_validator.py
def validar_produto(dados):
    errors = []
    if not dados.get("nome") or len(dados["nome"]) < 2:
        errors.append("Nome inválido")
    if dados.get("preco", -1) < 0:
        errors.append("Preço não pode ser negativo")
    return errors

# used identically in both create and update controllers
```
(A library like `marshmallow`/`pydantic`/`joi`/`zod` is an even better fit once one is
already a project dependency — reuse what's there before adding a new one.)

## 11. Callback Hell → async/await (or Promise chaining) with a single error path

**Before:**
```javascript
this.db.get(sql1, [id], (err, a) => {
    this.db.get(sql2, [a.id], (err, b) => {
        this.db.run(sql3, [b.id], (err) => { res.json(...) });
    });
});
```

**After:**
```javascript
const a = await dbGet(sql1, [id]);
const b = await dbGet(sql2, [a.id]);
await dbRun(sql3, [b.id]);
res.json(...);
```
(`dbGet`/`dbRun` are thin promise-returning wrappers around the callback-style driver, or
come for free if you switch driver per recipe #14.) One `try/catch` around the sequence
replaces one bespoke error branch per nesting level.

## 12. Inconsistent/Silent Error Handling → centralized error-handling middleware

**Before:** every route has its own `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500`.

**After:**
```python
# middlewares/error_handler.py
@app.errorhandler(Exception)
def handle_error(e):
    app.logger.exception("Unhandled error")
    return jsonify({"erro": "Erro interno"}), 500
```
Route/controller code raises normally; it no longer needs its own try/except for the
generic case (keep specific `except` blocks only where you handle a particular error
differently, e.g. a 404 for "not found").

## 13. Poor Naming / Magic Numbers → descriptive names and named constants

**Before:**
```javascript
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cc = req.body.card;
```
```python
if faturamento > 10000: desconto = faturamento * 0.1
```

**After:**
```javascript
const { username, email, password, cardNumber } = req.body;
```
```python
DISCOUNT_TIER_HIGH_THRESHOLD = 10000
DISCOUNT_TIER_HIGH_RATE = 0.10
if faturamento > DISCOUNT_TIER_HIGH_THRESHOLD:
    desconto = faturamento * DISCOUNT_TIER_HIGH_RATE
```

## 14. Deprecated/Obsolete API Usage → swap in the modern equivalent

**Before:**
```python
criado_em = datetime.utcnow()
task = Task.query.get(task_id)
```

**After:**
```python
from datetime import datetime, timezone
criado_em = datetime.now(timezone.utc)
task = db.session.get(Task, task_id)
```
```javascript
// before: raw callback-style sqlite3
db.get(sql, params, (err, row) => { ... });
// after: promise-based wrapper + async/await
const row = await db.get(sql, params);
```
Cross-check every match against the table in the anti-pattern catalog's deprecated-API
section — the fix is always "the modern replacement" column for that row, applied
consistently everywhere the old call appears, not just the first occurrence.
