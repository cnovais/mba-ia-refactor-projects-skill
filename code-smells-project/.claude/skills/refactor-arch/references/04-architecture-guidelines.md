# Target Architecture Guidelines (MVC)

Used in Phase 3, alongside the refactoring playbook. This defines what each layer is
*for* — use it to decide where a given piece of code belongs, independent of language.
The folder names below are conventions, not requirements: adapt them to the idiom of the
stack you're refactoring (e.g. a Node/Express project reads naturally as
`models/ views/ controllers/`, while a Flask project might prefer `models/ routes/
controllers/` — both are the same three responsibilities).

## The three layers

### Models — data and domain rules

**Owns:** the shape of the data, how it's persisted/retrieved, and invariants that belong
to the data itself (a task's status must be one of a fixed set; a price can't be
negative). One model per business entity (`Produto`, `Usuario`, `Pedido`, not one
mega-model for all of them).

**Does NOT own:** HTTP concerns (no `request`/`response` objects in here), routing, or
orchestration across multiple entities (that's a controller's job — a model doesn't call
another model's persistence methods to "complete a checkout"). All SQL/ORM access lives
here, and every query must be parameterized.

### Views / Routes — the interface to the outside world

**Owns:** mapping an incoming request (HTTP method + path, or in a non-HTTP context, the
entry point of the interaction) to the controller action that handles it, and — where the
framework separates the two — the shape of the outgoing response. In a JSON API "view"
usually collapses into "route declarations plus response serialization", which is fine;
the point is this layer stays declarative.

**Does NOT own:** business logic, validation rules, or direct data access. A route
handler's body should be small enough to read as "parse → delegate to controller →
return what the controller gave back."

### Controllers — application flow

**Owns:** orchestrating one use case end to end — validate input, call the model(s)
needed, apply any cross-entity business rule, decide the response status/payload, and
trigger side effects (notifications, cache invalidation) through their own
abstraction rather than inline `print`/ad-hoc calls. This is where the logic that used to
be crammed into route handlers or a God file ends up.

**Does NOT own:** raw SQL/ORM calls (delegate to the model) or route-path declarations
(that's the views/routes layer's job). A controller talks to models and returns data; it
never talks to the database directly.

## Cross-cutting concerns (outside the M-V-C triangle, but part of "target architecture")

- **Config module** (`config/settings.py`, `config.js`, etc.): every secret, connection
  string, and environment-dependent value is read from environment variables here, with
  safe non-secret defaults where reasonable and no literal secret committed to source.
  Nothing outside this module reads `os.environ`/`process.env` directly — everything else
  imports from config.
- **Error handling middleware**: one centralized place that catches unhandled
  errors/exceptions, logs them properly (not `print`), and returns a consistent error
  response shape — instead of every controller/route repeating its own
  try/except-and-print.
- **Composition root / entry point**: one clear file (`app.py`, `app.js`, `main.py`) that
  wires everything together — creates the app instance, applies config, registers
  routes/blueprints, mounts the error handler, and starts listening. It should be short
  and mostly declarative; if it's doing real work (building SQL, validating request
  bodies), that work escaped from its proper layer.

## How much restructuring a given project actually needs

Not every project starts from a monolith, so Phase 3 isn't "always create these exact
folders from zero":

- A **single-file monolith** (routing + business logic + raw SQL in 1-4 files) needs the
  full split: extract models per domain, extract controllers per domain, move routes into
  their own layer, pull config and error handling out.
- A **project with ad-hoc layering** (files named `controllers.py`/`models.py` that don't
  actually respect the boundaries above) needs the same layers but the existing file
  names give you a head start — move code to where it belongs rather than renaming files
  and calling it done.
- A **partially organized project** (real `models/`, `routes/`, `services/`, `utils/`
  folders) may already satisfy the folder-level shape. Here Phase 3 is about pushing logic
  that leaked across boundaries back into the right layer — serialization duplicated in
  every route moves onto the model as a `to_dict()`/serializer method if it isn't already
  there and needs consolidating; a route computing business rules inline moves into a
  controller/service; missing config extraction and centralized error handling still
  apply even if the folders already look right. Don't invent unnecessary top-level
  reshuffling just to "look refactored" — the acceptance bar is that MVC responsibilities
  are actually respected, not that the diff is large.

Whichever starting point you have, the resulting structure must let you point at any file
and say, in one sentence, which of the three responsibilities above it owns.
