# Anti-Pattern Catalog

Used in Phase 2. Each entry lists **what to look for** (language-agnostic signals, plus
concrete syntax examples across a few common languages so you recognize the shape even in
a stack not explicitly listed) and its **severity**, per the scale below. Work through
every entry against the real codebase — don't stop at the first few matches, and don't
report an anti-pattern you didn't actually verify with a file:line.

## Severity scale

- **CRITICAL** — breaks correctness, exposes sensitive data, or fully collapses the
  separation of responsibilities (e.g. hardcoded credentials, SQL injection, a God Class
  mixing DB + business logic + routing in one file).
- **HIGH** — strong MVC/SOLID violations that make testing and maintenance hard (heavy
  business logic trapped in controllers, tight coupling with no dependency injection,
  mutable global state).
- **MEDIUM** — standardization problems, duplication, or moderate performance issues
  (N+1 queries, misused middleware, missing route-level validation).
- **LOW** — readability, naming, or magic numbers/strings.

---

## 1. God Class / God Module — CRITICAL

**Signal:** one file defines routing, request handling, business rules, and raw
database access together, or a single "model"/"manager" file exports functions for
every unrelated domain in the app (products *and* orders *and* users, all in one file).
Rule of thumb: if you can't describe the file's job in one sentence, it's a God file.

**Why CRITICAL:** nothing in it can be tested, changed, or reasoned about in isolation;
one file touching everything means one change can silently break everything else.

---

## 2. Hardcoded Credentials / Secrets — CRITICAL

**Signal:** a literal string assigned to something named `SECRET_KEY`, `password`,
`pwd`, `api_key`, `token`, `dbPass`, or similar, sitting directly in source rather than
read from environment/config. Examples:
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
```javascript
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_..." };
```
Also flag a secret echoed back in an API response (e.g. a `/health` endpoint that returns
`secret_key` in its JSON) — that's the same anti-pattern with an even worse blast radius.

**Why CRITICAL:** anyone with read access to the repo (or a leaked response body) gets
production credentials.

---

## 3. SQL Injection via String Concatenation — CRITICAL

**Signal:** SQL built by concatenating or interpolating request-derived values instead of
using parameterized queries/bind variables:
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('" + nome + "', ...)")
```
```javascript
db.all(`SELECT * FROM users WHERE name = '${name}'`)
```
Contrast with the safe form already used elsewhere in the same codebase (`"...WHERE id = ?", [id]`)
— when a project mixes both, that inconsistency is itself worth calling out.

**Why CRITICAL:** classic injection vector — a crafted `id` or `nome` can read, modify, or
destroy data outside the intended query.

---

## 4. Unauthenticated Dangerous Endpoint — CRITICAL

**Signal:** a route that executes arbitrary SQL (`request.get_json()["sql"]` piped
straight into `cursor.execute`), wipes tables, or performs another irreversible/high-blast
operation, reachable with no authentication or authorization check at all.

**Why CRITICAL:** this is a complete authorization bypass on top of whatever else is
wrong with the query itself — treat it as its own finding even when it overlaps with
finding #3.

---

## 5. Business Logic Trapped in Controllers/Routes — HIGH

**Signal:** a route handler doing more than "parse input → call a use case → shape the
response" — inline stock/price calculations, discount tiers, multi-step workflows,
cross-entity orchestration, or notification fan-out (`print("ENVIANDO EMAIL...")`, three
different "channels" logged inline) living directly in the handler body.

**Why HIGH:** business rules become untestable without spinning up the whole HTTP layer,
and the same rule tends to get duplicated the next time a similar endpoint is added.

---

## 6. Tight Coupling / No Dependency Injection — HIGH

**Signal:** a module reaches for a concrete global (a module-level DB connection, a
`new ConcreteClass()` built inline deep in a call chain) instead of receiving its
dependencies from the caller/composition root. A constructor that immediately does
`this.db = new sqlite3.Database(...)` with no way to substitute a test double is the
textbook case.

**Why HIGH:** you cannot unit test the module without a real database/network/filesystem,
and swapping an implementation means editing the module itself.

---

## 7. Mutable Global State — HIGH

**Signal:** a module-level variable that gets mutated from request handlers — a global
`db_connection` reassigned via `global`, a shared in-memory cache object mutated across
requests, a module-level counter/accumulator.

**Why HIGH:** concurrent requests race on the same state, tests bleed into each other,
and behavior depends on call order rather than inputs.

---

## 8. Weak / Homemade Cryptography — HIGH

**Signal:** passwords hashed with a fast general-purpose hash with no salt (`hashlib.md5`,
`hashlib.sha1`) instead of a slow, salted password hash (bcrypt/scrypt/argon2); or a
hand-rolled "encryption" function that isn't actually cryptographic at all, e.g.:
```javascript
function badCrypto(pwd) {
    let hash = "";
    for (let i = 0; i < 10000; i++) { hash += Buffer.from(pwd).toString('base64').substring(0, 2); }
    return hash.substring(0, 10);
}
```

**Why HIGH:** MD5/SHA1 are crackable at scale in seconds with rainbow tables; a homemade
scheme like the one above is reversible/guessable and gives no real protection at all.

---

## 9. N+1 Query Pattern — MEDIUM

**Signal:** a loop that issues one query per iteration instead of a single batched query
or a join/eager-load — most visibly, a query inside a `for` loop over another query's
results, or (in async/callback code) a `.forEach` that fires a new async DB call per item:
```python
for item in itens:
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
```
```javascript
enrollments.forEach(enr => { this.db.get("SELECT ... WHERE id = ?", [enr.user_id], ...) })
```

**Why MEDIUM:** scales linearly (or worse, with nested loops) with data volume and turns
a cheap endpoint into a slow one as soon as real data shows up.

---

## 10. Missing / Duplicated Route-Level Validation — MEDIUM

**Signal:** the same validation rules (required fields, length bounds, enum checks)
copy-pasted nearly verbatim across multiple handlers, or a handler that skips validation
present everywhere else (e.g. every other create/update route validates length but one
doesn't). Also flag validation that silently accepts malformed input because it isn't
enforced at all (no email format check, no type check on a numeric field before using it
in arithmetic).

**Why MEDIUM:** duplication means a rule fixed in one place stays broken in the others,
and gaps let bad data reach the database.

---

## 11. Callback Hell / Deeply Nested Async Flow — MEDIUM

**Signal:** callbacks nested three or more levels deep to sequence dependent async
operations (classic in older Node.js code using callback-style APIs instead of
Promises/async-await), especially when error handling is inconsistent across the levels.

**Why MEDIUM:** hard to read, easy to leak an unhandled error in one of the inner
callbacks, and hard to extend without nesting even deeper.

---

## 12. Inconsistent / Silent Error Handling — MEDIUM

**Signal:** bare `except:`/`catch {}` blocks that swallow the real error, `print()`-based
"logging" of errors instead of a logger, or error responses that leak internal exception
text (`str(e)`) straight to the client.

**Why MEDIUM:** makes production incidents nearly undebuggable and can leak internals
(stack traces, query text) to callers.

---

## 13. Poor Naming / Magic Numbers & Strings — LOW

**Signal:** single/double-letter identifiers for non-trivial values (`u`, `e`, `p`, `cid`,
`cc` for user/email/password/course-id/card-number), or bare numeric/string literals whose
meaning requires reading surrounding logic (`if faturamento > 10000: desconto = ...`,
`priority` compared against raw `1`–`5` with no named levels).

**Why LOW:** doesn't break anything today, but forces every future reader to
reverse-engineer intent instead of reading it directly.

---

## 14. Deprecated / Obsolete API Usage — MEDIUM

Check this as its own pass — it isn't a classic MVC violation, but the skill must catch
it and recommend the modern replacement. Common examples (recognize the *pattern*, not
just these exact calls — apply the same reasoning to whatever stack/version you find):

| Deprecated API | Why | Modern replacement |
|---|---|---|
| `datetime.utcnow()` / `datetime.utcfromtimestamp()` (Python) | Deprecated since Python 3.12 — naive, easy to mix up with local time | `datetime.now(timezone.utc)` |
| `Model.query.get(id)` (Flask-SQLAlchemy on SQLAlchemy 2.x) | Legacy `Query` API pending removal in favor of the 2.0-style API | `db.session.get(Model, id)` |
| Callback-style `sqlite3` driver calls chained by hand (Node `sqlite3` package) | No native Promise support, forces callback nesting (see #11) and error-prone manual sequencing | A promise-based driver/wrapper (`sqlite`, `better-sqlite3`) with `async/await` |
| Running the framework's built-in dev server in production (`app.run(debug=True)`, `flask run`) | Not designed for production traffic or security; debug mode can leak stack traces and enable the debugger console | A production WSGI/ASGI server (gunicorn/uvicorn) with debug off |
| Old pinned minor versions of a framework still on its dependency manifest without a stated reason | Misses security patches already released for that major version | Bump to the latest compatible patch/minor release |

Report each match the same way as any other finding — file:line, description, impact,
and recommendation (the "modern replacement" column above *is* the recommendation).
