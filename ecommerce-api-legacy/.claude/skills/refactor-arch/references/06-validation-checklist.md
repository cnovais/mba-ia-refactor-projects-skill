# Validation Checklist

This is the skill's own self-check. Fill it in as you complete each phase — don't leave it
for the very end, since the Phase 1/2 items are only honestly checkable right when those
phases finish, while your Phase 1/2 output is still fresh. Append the completed checklist
(with `[x]`/`[ ]`, not left as a bare template) to the **same** audit report file the
project uses (the file you write for Phase 2 output — e.g. `reports/audit-project-N.md`),
as its final section, titled `## Checklist de Validação`. Every project run through this
skill ends up with this checklist embedded in its report — that's what makes the report
close the loop instead of just being a snapshot of Phase 2.

Use this exact structure:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

## How to fill each box honestly

Don't check a box because the instructions asked you to do the thing — check it because
you verified the outcome. A checklist that's always fully checked regardless of what
actually happened is worse than no checklist.

- **Fase 1 items** — check right after printing the Phase 1 summary. "Número de arquivos
  analisados condiz com a realidade" means: you actually counted source files (excluding
  `node_modules`/`venv`/lockfiles/caches), not that you printed *a* number.
- **Fase 2 items** — check right after printing the audit report, before asking for
  confirmation.
  - "Mínimo de 5 findings identificados" — if you found fewer than 5, that's a signal you
    didn't check every catalog entry against the real code; go back through
    `02-antipattern-catalog.md` again rather than checking this box against reality that
    doesn't hold.
  - "Detecção de APIs deprecated incluída (se aplicável)" — check it when you ran the
    deprecated-API pass and either found and reported matches, or confirmed none of the
    catalog's deprecated patterns (or their equivalents in this stack) are present. Leave
    it unchecked only if you skipped the pass entirely — that's a real gap, not a
    "not applicable."
  - "Skill pausa e pede confirmação antes da Fase 3" — this one is about to happen (or
    just happened) at the moment you're filling this section in; check it once you've
    actually presented the [y/n] gate and are printing the report.
- **Fase 3 items** — these can only be honestly checked *after* Phase 3 finishes and you
  ran the validation steps in SKILL.md (booting the app, exercising the endpoints, and if
  applicable re-checking the app is using a config module, has models, etc.). If Phase 3
  was declined by the human (the confirmation gate answered "no"), leave the whole Fase 3
  section unchecked and add a one-line note explaining why ("Fase 3 não executada — humano
  optou por não prosseguir"), instead of deleting the section.

## Appending to the report file

After Phase 3 completes (or is declined), re-open the report file you wrote for this
project and append the filled checklist to its end, under `## Checklist de Validação`.
The report then documents the full lifecycle of the run — analysis, audit, human
decision, and (if it happened) the refactor outcome — in one file.
