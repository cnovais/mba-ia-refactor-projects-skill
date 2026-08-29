# Audit Report Template

Used in Phase 2. Render the report in **exactly** this shape — the frame lines
(`====...`), heading levels, and field labels stay identical across every project so
reports are diffable and comparable across runs. Only the content changes.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project folder name>
Stack:   <language> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Anti-pattern name>
File: <relative/path.ext>:<line or line-range>
Description: <what is actually in the code — be specific, name the real variable/function/table>
Impact: <concrete consequence if left unfixed>
Recommendation: <what to do about it, one or two sentences — the "how" is in the refactoring playbook>

### [<SEVERITY>] <next finding>
...

================================
Total: <N> findings
================================

## Checklist de Validação
<filled in per references/06-validation-checklist.md — appended here, not in a separate file>
```

## Rules for filling it in

- **Order:** findings sorted CRITICAL → HIGH → MEDIUM → LOW. Within the same severity,
  order by the file they appear in (top of the project down) so the report reads like a
  walkthrough of the codebase rather than a random list.
- **File:line is mandatory and must be real.** Open the file, count the lines, cite the
  actual range (`models.py:1-350`, `app.js:28`). A finding you can't pin to a location
  doesn't belong in this report — go verify it or drop it.
- **Description says what's there, not what's wrong in the abstract.** "SECRET_KEY
  hardcoded as `'minha-chave-super-secreta-123'`" is useful; "bad security practice" is
  not — the reader should be able to open the file to that exact line and immediately see
  what you saw.
- **Impact is concrete.** Tie it to a real consequence: "an attacker can read/modify any
  row via a crafted `id`", "any change to product logic risks breaking user and order
  logic in the same file", "response time grows linearly with items per order". Avoid
  generic impact statements that could apply to any finding.
- **Recommendation is short and points at the fix**, not a full essay — the refactoring
  playbook (`references/05-refactoring-playbook.md`) is where the detailed before/after
  lives; the report just needs to say which direction to go, e.g. "parameterize the query"
  or "extract into `produto_controller.py`".
- **Total must match the sum of the summary line.** Recount before printing if they
  don't agree — a mismatch here undermines trust in the whole report.
- **Don't pad or shrink the count.** Report every genuine finding you verified, in every
  severity band you found evidence for; don't stop early once you clear a minimum, and
  don't invent findings to hit one either.

## After printing the report

Immediately follow it with the Phase 2 → Phase 3 confirmation gate defined in SKILL.md.
The report and the confirmation prompt are two separate outputs — don't merge them into
one block, so a reader (or a script capturing output) can cleanly split "the audit" from
"the question."

The `## Checklist de Validação` section (see `06-validation-checklist.md`) is part of
this same report file, appended after `Total: <N> findings`. It's filled in twice: once
right after Phase 2 (Fase 1 + Fase 2 boxes), and again after Phase 3 runs or is declined
(Fase 3 boxes). The report on disk should always reflect the checklist's true state at
whatever point the run stopped — never leave it as an unfilled template.
