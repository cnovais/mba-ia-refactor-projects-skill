# Project Analysis Heuristics

Used in Phase 1. The goal is a fast, accurate fingerprint of the codebase — language,
framework, database, domain, and current architecture — using signals that generalize
across stacks instead of stack-specific special-casing.

## 1. Language detection

Look at file extensions and manifest files, in this priority order (first match wins if
several are present, since a repo can contain incidental files from other tools):

| Signal | Language |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python |
| `package.json`, `*.js`/`*.mjs`/`*.cjs` | JavaScript (Node.js) |
| `tsconfig.json`, `*.ts` | TypeScript |
| `go.mod`, `*.go` | Go |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `Gemfile`, `*.rb` | Ruby |
| `composer.json`, `*.php` | PHP |

## 2. Framework detection

Read the manifest's dependency list — don't guess from folder names alone, a folder named
`controllers/` doesn't imply any particular framework.

- **Python**: `flask` → Flask; `django` → Django; `fastapi` → FastAPI. Get the pinned
  version from `requirements.txt`/`pyproject.toml` (e.g. `flask==3.1.1`).
- **Node.js**: check `dependencies` in `package.json` — `express` → Express,
  `fastify` → Fastify, `koa` → Koa, `@nestjs/core` → NestJS. Version comes from the
  same block (`^4.18.2` etc. — report the declared range, note it's a range not a pin if
  relevant).
- Note any framework-adjacent libraries worth calling out in the "Dependencies" line
  (e.g. `flask-cors`, `flask-sqlalchemy`, `sqlite3`, `pg`, `mongoose`) — these hint at the
  DB layer and cross-cutting concerns (CORS, sessions) you'll need to preserve when you
  restructure in Phase 3.

## 3. Database detection

- Grep for connection setup: `sqlite3.connect`, `sqlite3.Database`, `psycopg2.connect`,
  `mysql.connector`, `mongoose.connect`, `SQLAlchemy()`, `createPool`, etc.
- Identify tables/collections either from `CREATE TABLE` statements (raw SQL) or from ORM
  model classes (`db.Model`, `Schema(...)`, `@Entity`). List every table/collection name
  you find — this becomes the "DB tables" line in the Phase 1 summary and later maps
  directly to the Models you'll create in Phase 3.
- Note whether the DB is file-based/in-memory (fine for a demo, but flag file-based
  ":memory:" or a bare `.db` file with no migrations as a signal the project has no real
  persistence strategy — that's useful context for the audit, not a finding by itself).

## 4. Domain detection

Infer what the application actually *does* in business terms — this is not a technical
fact, it's read from the shape of the data and routes:

- List the route paths and HTTP methods (or RPC handlers). Group them by resource
  (`/produtos`, `/pedidos`, `/usuarios` → an e-commerce domain with products, orders,
  users; `/tasks`, `/categories` → a task-management domain).
- Cross-check against table/model field names — a `courses` + `enrollments` + `payments`
  set of tables describing checkout is a very different domain from `tasks` +
  `categories` + `priority`, even if both are "just a CRUD API".
- Write one line describing the domain in plain business language, e.g. "E-commerce API
  (products, orders, users)" or "LMS API with a course-checkout flow". Avoid restating the
  framework here — that already has its own line.

## 5. Architecture mapping

Describe how responsibilities are currently distributed — this sets up Phase 2's search
for separation-of-concerns violations:

- **Monolithic / single-file**: one or two files contain routing, business logic, and data
  access together. Call this out explicitly — it's the strongest signal of the God
  Class/God Method anti-pattern.
- **Ad-hoc layering**: files are split (e.g. `controllers.py`, `models.py`) but the split
  doesn't map to real responsibilities — a "models" file that builds raw SQL strings and
  does request-shaped validation, or a "controller" that also touches the DB directly,
  still counts as ad-hoc, not layered.
- **Partially organized**: real folders exist (`models/`, `routes/`, `services/`,
  `utils/`) and mostly hold what their name suggests, but MVC responsibilities still leak
  across boundaries (e.g. serialization logic duplicated in every route instead of living
  on the model, or a route handler computing business rules inline). Say so — "partially
  organized" is a legitimate, common answer and Phase 3 should improve rather than
  bulldoze this kind of project (see the architecture guidelines' note on incremental
  refactors).
- Count the source files that make up the app itself (exclude config/lockfiles/tests
  fixtures/seed scripts if they're clearly not part of the runtime app) — this is the
  "Source files: N analyzed" figure.

## 6. Producing the Phase 1 summary

Fill in every field of the template in SKILL.md Phase 1 using what you found above. Keep
each line to one fact — the summary is meant to be skimmable, the detail goes in the
Phase 2 report, not here.
