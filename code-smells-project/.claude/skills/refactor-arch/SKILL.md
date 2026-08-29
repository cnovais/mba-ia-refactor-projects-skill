---
name: refactor-arch
description: Analyzes, audits, and refactors any backend codebase (any language or framework — Python/Flask, Node.js/Express, etc.) into a clean MVC architecture. Detects the stack, catalogs anti-patterns and code smells with exact file:line references and CRITICAL/HIGH/MEDIUM/LOW severity, produces a structured audit report, and — after explicit human confirmation — restructures the project into Models/Views-Routes/Controllers, extracting config, centralizing error handling, and validating the app still boots and its endpoints still respond. Always use this skill when the user invokes "/refactor-arch", asks to audit or refactor a legacy project's architecture, wants a code-smell / anti-pattern report, or asks to "migrate this to MVC" — even if they don't name MVC explicitly, e.g. "this codebase is a mess, can you clean up the architecture" or "find the security and design problems in this API".
---

# refactor-arch

You are acting as an automated software architect. This skill turns an unstructured or
partially-structured backend project into a clean, technology-agnostic MVC codebase, in
three sequential phases. Never skip a phase and never collapse phases 2 and 3 — the whole
point of this skill is that a human reviews the audit before anything gets rewritten.

Read the reference files below **as you reach the phase they support** rather than all
upfront — each is scoped to one phase so you only pay for the context you need:

| Phase | Reference file | Purpose |
|---|---|---|
| 1 | `references/01-project-analysis.md` | Heuristics to detect language, framework, DB, domain, and current architecture |
| 2 | `references/02-antipattern-catalog.md` | Catalog of anti-patterns/code smells with detection signals and severity |
| 2 | `references/03-report-template.md` | Exact structure the audit report must follow |
| 3 | `references/04-architecture-guidelines.md` | Target MVC rules — what belongs in Models, Views/Routes, Controllers |
| 3 | `references/05-refactoring-playbook.md` | Concrete before/after transformation recipes, one per anti-pattern family |
| 1-3 | `references/06-validation-checklist.md` | The skill's own self-check — filled in progressively and appended to the report |

The skill is technology-agnostic by design: nothing below assumes Python, JavaScript, or
any specific framework. Every heuristic is phrased in terms of what the code *does*
(a file that opens a DB connection, builds SQL, and defines routes) rather than what
language it's written in. When you hit a stack you don't recognize, fall back to first
principles: read the entry point, follow the imports, look at what each file is
responsible for.

## Phase 1 — Analysis

Goal: understand the codebase well enough to describe it in a few lines, without changing
anything.

1. List the project's source files (skip `node_modules`, `venv`, `.git`, lockfiles,
   caches, and anything under `.claude/`). Note the count — you'll report it.
2. Follow `references/01-project-analysis.md` to detect: language, framework (+ version if
   pinned in a manifest), database/ORM, key dependencies, the application's business
   domain (infer it from route names, table names, and model fields — don't guess wildly,
   read the actual code), and the current architecture shape (how many layers exist today,
   if any, and where responsibilities are mixed).
3. Print a summary in this exact shape (adapt the field values, keep the frame and field
   names so output is consistent across runs and stacks):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language>
Framework:     <framework + version if known>
Dependencies:  <notable deps, comma-separated>
Domain:        <one line describing what the app does, in business terms>
Architecture:  <one line: monolithic single-file / ad-hoc layers / partially layered, etc.>
Source files:  <N> files analyzed
DB tables:     <table/collection names, if a DB is present>
================================
```

Do not ask for confirmation here — Phase 1 is read-only and cheap. Move straight into
Phase 2.

Open `references/06-validation-checklist.md` and mentally check off its "Fase 1" items
now, honestly — you'll write them into the report at the end of Phase 2.

## Phase 2 — Audit

Goal: cross-reference the code against the anti-pattern catalog and produce a report a
human can act on. Still zero file writes in this phase.

1. Work through `references/02-antipattern-catalog.md` entry by entry. For each
   anti-pattern, actually search the codebase for its detection signals (grep for string
   concatenation into SQL, scan for hardcoded secrets, look for business logic inside
   route handlers, etc.) — don't pattern-match on the examples in this SKILL.md, they're
   illustrative, not the target code.
2. For every match, capture the **exact file and line number(s)** — open the file and cite
   real numbers, never approximate. A finding without a precise location is not usable by
   whoever reads the report.
3. Also check for deprecated/obsolete API usage as its own pass (the catalog has a
   dedicated section for this) — flag it even though it's not a classic MVC violation,
   since "uses an obsolete API" is part of this skill's job.
4. Assign severity per finding using the CRITICAL/HIGH/MEDIUM/LOW scale defined in the
   catalog. Don't inflate — a bad variable name is LOW, not MEDIUM, even if you found a
   lot of them.
5. Render the report using **exactly** the structure in `references/03-report-template.md`
   — findings sorted CRITICAL → HIGH → MEDIUM → LOW, each with file:line, description,
   impact, and recommendation. Aim for genuine coverage of what's actually wrong; most
   real legacy projects surface well beyond the 5-finding floor once you check every
   catalog entry.
6. Append the `## Checklist de Validação` section from
   `references/06-validation-checklist.md` to the bottom of the same report file, with
   its Fase 1 and Fase 2 boxes checked based on what you actually did (not blindly
   checked) and the Fase 3 boxes still unchecked — they can only be verified once Phase 3
   runs. This makes the report on disk carry the checklist from the moment Phase 2 exists,
   even if the human never approves Phase 3.
7. Print the report, then **stop and ask the human to confirm before proceeding**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

   This confirmation is not optional and not a formality — it is the one hard gate in this
   skill. Do not touch a single file until you get an explicit yes. If the answer is no,
   stop entirely and leave the codebase untouched; the human may want to adjust scope or
   revisit the report first.

## Phase 3 — Refactoring

Goal: restructure the project into MVC per `references/04-architecture-guidelines.md`,
using the transformation recipes in `references/05-refactoring-playbook.md`, without
breaking anything that currently works.

1. **Plan the target layout before moving anything.** Decide the MVC folder structure for
   *this* project's stack and domain (see the architecture guidelines for the shape) —
   don't copy a Python layout onto a Node project verbatim, translate the idiom.
2. **Respect what's already good.** If a project already has some separation (e.g. a
   `models/` folder that's genuinely just models), improve and reorganize it rather than
   discarding and rewriting from scratch — the guidelines note in project analysis
   references what "partially organized" looks like. The playbook entries are written as
   independent recipes for this reason: apply only the ones a given project actually needs.
3. **Work anti-pattern by anti-pattern**, using the matching playbook recipe: extract
   config/secrets into a config module reading from environment variables, split god
   files into per-domain models and controllers, move routing into a dedicated
   views/routes layer, parameterize every SQL query, centralize error handling into
   middleware, replace deprecated APIs with their modern equivalent, etc.
4. **Preserve external behavior.** Every original endpoint (same path, method, and
   response shape) must keep working — this is a structural refactor, not a rewrite of
   business rules. If you fix a genuine bug (e.g. SQL injection) the fix must not change
   the contract for a well-formed request.
5. **Validate before declaring done:**
   - Install/verify dependencies, then boot the application and confirm it starts without
     errors (check the process output/logs, not just "the file has no syntax errors").
   - Exercise the original endpoints (curl, the project's `.http` file, or equivalent) and
     confirm each still responds with the expected status/shape.
   - Re-scan against the anti-pattern catalog and confirm the findings from Phase 2 are
     resolved (or explicitly note any that were deliberately deferred and why).
   - Stop the server process you started for validation once checks pass.
6. Go back to the report file and check off the remaining "Fase 3" boxes from
   `references/06-validation-checklist.md` — each one only after you actually verified it
   (e.g. don't check "Aplicação inicia sem erros" unless you watched it boot in this run).
   If the human declined Phase 3 at the gate above, skip this step entirely and leave the
   Fase 3 section unchecked with a one-line note explaining why, per the checklist file's
   guidance.
7. Print a closing summary:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the new layout>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining (or: N deferred, listed above)
================================
```

## Notes on running this across multiple projects

This skill folder is meant to be copied as-is into other backend projects to prove it's
stack-agnostic — nothing in it should be specific to the project it was first written
against. If you find yourself wanting to hardcode a table name, route path, or file name
from the original codebase into these instructions, stop: that belongs in the analysis you
produce at runtime, not in the skill itself.
