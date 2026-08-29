# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

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

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.

---

# Entrega do Desafio

Tudo a partir daqui é a minha entrega para este desafio: a análise manual dos três projetos, o processo de construção da skill `refactor-arch`, os resultados da execução nos três projetos e como reproduzir tudo. As evidências visuais (prints do terminal com as três fases rodando) estão na pasta [`imagens/`](./imagens) na raiz do repositório.

**IMPORTANTE: Todos os critérios abaixo devem ser atingidos nos 3 projetos, não apenas em um!**

| Critério | Requisito | Status |
|---|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) | ✅ 3/3 |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) | ✅ 3/3 (15, 16 e 14 findings) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) | ✅ 3/3 (todos com múltiplos CRITICAL e HIGH) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) | ✅ 3/3 (boot limpo + endpoints originais validados via curl) |

## Análise Manual

Antes de escrever qualquer linha da skill, separei um tempo só pra ler os três projetos com calma, sem IA no meio, anotando o que ia achando estranho. A ideia era simples: só dá pra ensinar um agente a caçar problema se eu souber exatamente qual problema eu quero que ele cace. Fui abrindo arquivo por arquivo, seguindo o fluxo das rotas mais sensíveis (login, checkout, exclusão de usuário) e prestando atenção especial em onde o código falava com o banco.

### Projeto 1 — code-smells-project (Python/Flask, API de E-commerce)

Esse foi o primeiro que abri, e também o mais cru dos três: só 4 arquivos, sem pasta nenhuma. Busquei por `SELECT`, `INSERT` e `senha` pra entender como o acesso a dados funcionava e fui marcando o que parecia errado.

- **[CRITICAL] SQL Injection generalizada** (`models.py`, praticamente todas as funções de acesso a dados) — toda query é montada concatenando string com o que vem direto da requisição, inclusive no login. Não é só má prática: dá pra logar como qualquer usuário sem saber a senha mandando algo como `' OR '1'='1` no campo de email. Um bug desses sozinho já bloquearia qualquer deploy.
- **[CRITICAL] Chave secreta hardcoded e devolvida pelo próprio `/health`** (`app.py`, `controllers.py`) — a `SECRET_KEY` está escrita no código-fonte e o endpoint de health-check devolve ela (e o flag de debug) no corpo da resposta. Não precisa nem vazar o repositório: basta chamar `/health` em produção.
- **[CRITICAL] `/admin/query` executa SQL arbitrário e `/admin/reset-db` apaga o banco inteiro, os dois sem autenticação** — dá pra derrubar a base inteira com um `curl`. Não existe cenário em que isso seja aceitável.
- **[MEDIUM] N+1 ao montar pedidos** (`models.py`) — pra cada pedido, uma query nova pra buscar os itens, e pra cada item, outra pra buscar o nome do produto. Com poucos registros não incomoda, mas a coisa cresce rápido.
- **[MEDIUM] Validação de produto duplicada entre criar e atualizar** (`controllers.py`) — o mesmo bloco de regras aparece copiado quase palavra por palavra duas vezes; se alguém corrigir uma regra num lugar só, os dois fluxos ficam divergentes sem ninguém perceber.
- **[LOW] Números soltos nos percentuais de desconto** (`models.py`, cálculo de faturamento) — `10000`, `5000`, `0.1`, `0.05` aparecem direto no meio de um `if/elif`, sem constante nenhuma explicando o que representam.
- **[LOW] Log via `print()` com concatenação de string** — funciona, mas não dá pra filtrar por nível nem redirecionar isso em produção.

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com fluxo de checkout)

Esse foi o mais rápido de ler (só 3 arquivos, ~180 linhas), mas escondia o bug mais sério dos três. `AppManager.js` faz literalmente tudo — abre o banco, monta as rotas, calcula pagamento — então segui o fluxo de `/api/checkout` linha por linha pra entender o que de fato acontecia ali dentro.

- **[CRITICAL] Checkout de usuário existente não confere a senha** (`AppManager.js`) — quando o email já existe na base, o código chama direto a função que processa pagamento e matrícula, sem nunca comparar a senha enviada com a salva. Esse eu só peguei lendo com calma, não é um erro óbvio à primeira vista — mas é bypass de autenticação completo: quem souber o email de qualquer aluno consegue matricular e "pagar" em nome dele.
- **[CRITICAL] Chave de gateway de pagamento e credenciais de banco hardcoded** (`utils.js`) — tem até cara de chave de produção (`pk_live_...`) escrita direto no código, e ainda é impressa no console a cada checkout.
- **[CRITICAL] Relatório financeiro e exclusão de usuário sem autenticação nenhuma** — `GET /api/admin/financial-report` mostra faturamento e pagamento de todo mundo, `DELETE /api/users/:id` apaga qualquer conta, e nenhuma das duas rotas pede login.
- **[HIGH] "Hash" de senha caseiro** (`utils.js`) — a função que deveria proteger a senha só faz base64 e repete um pedaço da string; não é hashing de verdade. Marquei como HIGH e não CRITICAL porque, isolado, ainda depende de vazar o banco pra virar um problema prático — mas some junto com os outros itens de auth acima.
- **[MEDIUM] Cascata de queries no relatório financeiro** — uma query por curso e, dentro dela, mais duas por matrícula. É o mesmo problema de N+1 do projeto 1, só que em Node.
- **[MEDIUM] Callback dentro de callback dentro de callback no checkout**, com tratamento de erro inconsistente — tem callback que nem confere o `err` antes de seguir em frente. Isso deixa bug de produção quase impossível de rastrear pelo log.
- **[LOW] Nomes de variável de uma letra só** (`u`, `e`, `p`, `cid`, `cc`) — difícil revisar o código sem ficar voltando pra lembrar o que é cada coisa.

### Projeto 3 — task-manager-api (Python/Flask, Task Manager, já com alguma organização)

Esse é o único dos três que já chega com pastas (`models/`, `routes/`, `services/`, `utils/`), então o primeiro instinto foi achar que estava mais adiantado que os outros dois. Não é bem assim: a separação existe, mas boa parte da lógica escapou dela do mesmo jeito.

- **[CRITICAL] Nenhuma rota de escrita tem autenticação de verdade** — o login devolve um `'token': 'fake-jwt-token-' + id` que nenhuma outra rota valida. Existe até um `User.is_admin()` pronto no model, só que ele nunca é chamado em lugar nenhum. Na prática, qualquer um pode deletar qualquer usuário (o que cascateia deletando as tasks dele) ou editar qualquer conta.
- **[CRITICAL] Senha de SMTP e chave secreta do Flask hardcoded** (`app.py`, `services/notification_service.py`) — mesmo padrão do projeto 1, credenciais reais (ou com cara de reais) direto no código-fonte.
- **[HIGH] Hash de senha com MD5 sem salt** (`models/user.py`) — MD5 é rápido demais e sem salt pra proteger senha; um vazamento de banco vira lista de senha em texto claro com qualquer rainbow table pronta na internet.
- **[HIGH] A mesma regra de "task atrasada" reescrita em 5 lugares diferentes nas rotas**, em vez de chamar `Task.is_overdue()`, que já existe no model e nunca é usado. Achei esse interessante porque revela um padrão que se repete no projeto inteiro: tem código bom escrito, só que ele não é chamado de lugar nenhum.
- **[MEDIUM] N+1 ao listar tasks, categorias e no relatório de resumo** — mesmo padrão dos outros dois projetos, uma query por item dentro de um loop.
- **[MEDIUM] `utils/helpers.py` guarda uma terceira cópia de validação que ninguém importa** — dá pra ver que em algum momento centralizaram a validação ali, só que as rotas continuam com a lógica duplicada local e esse arquivo virou código morto.
- **[LOW] Variáveis de uma letra nas rotas** (`t`, `u`, `c`, `p`) — mesmo problema do projeto 2.
- **[LOW] Prioridade da task é um número de 1 a 5 sem nome** — o mapeamento pra "crítica", "alta" etc. só existe implícito na ordem das comparações, em mais de um arquivo.

Depois de ler os três, ficou bem claro que os problemas se repetem em famílias parecidas — segredo hardcoded, query ineficiente, validação duplicada, ausência de autenticação — mesmo em stacks e níveis de organização diferentes. Foi basicamente esse padrão que virou a base do catálogo de anti-patterns da skill.

## Construção da Skill

### Decisões de design

O `SKILL.md` foi pensado como um roteiro de execução, não como uma lista solta de instruções: as três fases (Análise, Auditoria, Refatoração) são sequenciais e a fase 2 tem um gate de confirmação humana que o próprio SKILL.md descreve como "não opcional e não uma formalidade". Em vez de jogar todo o conhecimento de domínio dentro do próprio SKILL.md, dividi em 6 arquivos de referência sob `references/`, cada um amarrado a uma fase específica, e coloquei logo no topo do SKILL.md uma tabela dizendo qual arquivo ler em qual fase — a ideia é a skill só carregar o contexto que precisa no momento em que precisa, em vez de ler tudo de uma vez:

| Arquivo | Fase | Conteúdo |
|---|---|---|
| `01-project-analysis.md` | 1 | Heurísticas para detectar linguagem, framework, banco e arquitetura atual |
| `02-antipattern-catalog.md` | 2 | Catálogo de anti-patterns com sinais de detecção e severidade |
| `03-report-template.md` | 2 | Estrutura exata que o relatório de auditoria precisa seguir |
| `04-architecture-guidelines.md` | 3 | Regras do MVC alvo — o que pertence a Model, View/Routes e Controller |
| `05-refactoring-playbook.md` | 3 | Receitas de transformação, uma por família de anti-pattern, com código antes/depois |
| `06-validation-checklist.md` | 1-3 | O checklist de validação da própria skill, preenchido progressivamente e anexado ao relatório |

### Catálogo de anti-patterns

O catálogo tem 14 entradas, com severidade distribuída conforme a escala CRITICAL/HIGH/MEDIUM/LOW definida no enunciado:

- **CRITICAL:** God Class/God Module, Credenciais Hardcoded, SQL Injection, Endpoint Perigoso Sem Autenticação
- **HIGH:** Lógica de Negócio no Controller/Rota, Acoplamento Forte/Ausência de DI, Estado Global Mutável, Criptografia Caseira/Fraca
- **MEDIUM:** N+1 Queries, Validação Ausente/Duplicada, Callback Hell, Tratamento de Erro Inconsistente/Silencioso
- **LOW:** Nomenclatura Ruim/Magic Numbers
- **MEDIUM (transversal):** Uso de API Deprecated/Obsoleta

Essa lista não foi escolhida no vácuo — é quase um espelho da análise manual acima: cada família de problema que apareceu nos três projetos (segredo hardcoded, SQLi, N+1, validação duplicada, endpoint sem auth) virou uma entrada do catálogo, com sinais de detecção descritos em termos do que o código *faz* ("query montada por concatenação de string dentro de um handler de rota") em vez de sintaxe de uma linguagem específica. A detecção de APIs deprecated entrou como item obrigatório à parte — o enunciado pedia isso explicitamente, então virou um passo dedicado na Fase 2 em vez de ficar diluído dentro dos outros itens.

### Como garanti que a skill é agnóstica de tecnologia

Duas coisas, principalmente. Primeiro, todo sinal de detecção no catálogo e nas heurísticas de análise é descrito por comportamento ("um arquivo que abre conexão de banco, monta SQL e define rotas no mesmo lugar"), nunca por sintaxe ou nome de biblioteca de uma linguagem só — quando um sinal só faz sentido numa stack específica (como `datetime.utcnow()` ou o driver `sqlite3` de callback do Node), isso fica marcado como exemplo dentro do item, não como a regra em si. Segundo, o próprio SKILL.md tem uma seção final ("Notes on running this across multiple projects") avisando o próprio agente pra nunca hardcodar nome de tabela, rota ou arquivo do projeto onde a skill foi escrita — se algo assim aparecesse, seria sinal de que a instrução deveria estar na análise gerada em tempo de execução, não na skill.

Na prática, a prova real foi copiar a pasta `.claude/skills/refactor-arch/` sem alterar uma linha para dentro do `ecommerce-api-legacy` (Node/Express, orientado a classe, callback-style) e do `task-manager-api` (Python/Flask, mas já parcialmente organizado em camadas) e rodar `/refactor-arch` nos dois. A skill se adaptou nas três execuções sem precisar de nenhum ajuste manual entre uma e outra.

### Desafios encontrados

- **Projeto parcialmente organizado (task-manager-api) exigia comportamento diferente do monolito.** Se a skill simplesmente reescrevesse tudo do zero toda vez, ela apagaria a separação de camadas que o projeto 3 já tinha. Resolvi adicionando uma instrução explícita na Fase 3 ("respeite o que já está bom, melhore em vez de reescrever do zero") e desenhando as receitas do playbook como itens independentes, aplicáveis um a um — só entra em ação a receita que aquele projeto específico realmente precisa.
- **Um dos CRITICAL do projeto 2 não dava pra fechar sem mudar o contrato da API.** As rotas de admin do `ecommerce-api-legacy` não tinham nenhuma autenticação, e o arquivo `api.http` original (usado como fonte de verdade dos endpoints) também não manda nenhuma credencial. Em vez de simplesmente ligar uma autenticação obrigatória e quebrar as requisições originais, a skill implementou um middleware `adminAuth` opt-in: some sem `ADMIN_API_KEY` configurada (mantendo o comportamento local/demo) e passa a exigir a chave assim que a variável é definida — documentado no relatório como mitigação, não como item fechado silenciosamente.
- **Ambiente local batendo com a stack (porta 5000 e AirPlay no macOS).** Na validação de um dos projetos a porta padrão do Flask conflitava com o AirPlay Receiver do macOS. Não é um problema da skill, mas precisou ficar documentado no relatório (porta alternativa usada na validação) pra não parecer que a aplicação não subiu.
- **Achar o equilíbrio certo pra não inflar severidade.** No começo dos testes a tentação era marcar tudo que "parecia ruim" como CRITICAL. O catálogo acabou ganhando uma frase direta ("don't inflate — a bad variable name is LOW, not MEDIUM, even if you found a lot of them") justamente pra manter o relatório útil e a distribuição de severidade honesta nos três projetos.

## Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | 4 | 4 | 4 | 3 | **15** |
| 2 — ecommerce-api-legacy | 4 | 5 | 5 | 2 | **16** |
| 3 — task-manager-api | 3 | 3 | 6 | 2 | **14** |

Relatórios completos em [`reports/audit-project-1.md`](./reports/audit-project-1.md), [`reports/audit-project-2.md`](./reports/audit-project-2.md) e [`reports/audit-project-3.md`](./reports/audit-project-3.md).

### Antes / depois da estrutura

**Projeto 1 — code-smells-project**

```
Antes                          Depois
app.py                         app.py (composition root)
controllers.py                 config/settings.py
database.py                    db/connection.py
models.py                      models/{produto,usuario,pedido}_model.py
                                controllers/{produto,usuario,pedido,sistema,admin}_controller.py
                                routes/{produto,usuario,pedido,sistema}_routes.py
                                services/notification_service.py
                                validators/produto_validator.py
                                middlewares/error_handler.py
```

**Projeto 2 — ecommerce-api-legacy**

```
Antes                          Depois (dentro de src/)
src/app.js                     app.js
src/AppManager.js              config/index.js
src/utils.js                   db/{connection,schema,seed}.js
                                models/{user,course,enrollment,payment,auditLog,financialReport}Model.js
                                controllers/{checkout,financialReport,user}Controller.js
                                routes/{checkout,financialReport,user}Routes.js + index.js
                                services/{passwordService,paymentGatewayService}.js
                                middlewares/{adminAuth,errorHandler}.js
                                utils/{asyncHandler,cache}.js
```

**Projeto 3 — task-manager-api**

```
Antes                           Depois
app.py                          app.py
database.py                     config/settings.py
models/ (misturado com regra)   models/{task,user,category}.py (só persistência/invariantes)
routes/ (com lógica de negócio) controllers/{task,user,category,report}_controller.py
services/                       routes/{task,user,category,report}_routes.py (roteamento fino)
utils/                          validators/{task,user,category}_validator.py
                                 auth/{decorators,tokens}.py
                                 middlewares/error_handler.py
                                 errors.py (ApiError central)
```

O projeto 3 é o único que já entrava com pastas — mas repare que a diferença real não é "criar pastas que não existiam" e sim mover lógica que estava vazando pra dentro de `routes/` de volta pra `controllers/`/`models/`, e criar as camadas que realmente faltavam (`auth/`, `validators/`, `errors.py`).

### Checklist de validação

O checklist completo (Fase 1, 2 e 3) foi preenchido pela própria skill dentro de cada relatório em `reports/`, com todos os itens marcados nos três projetos — inclusive os itens de Fase 3 ("Aplicação inicia sem erros", "Endpoints originais respondem corretamente"), que só foram marcados depois de a skill efetivamente subir cada aplicação e testar os endpoints originais via `curl`. Resumo:

| Projeto | Fase 1 | Fase 2 | Fase 3 |
|---|---|---|---|
| 1 — code-smells-project | ✅ 4/4 | ✅ 6/6 | ✅ 9/9 |
| 2 — ecommerce-api-legacy | ✅ 4/4 | ✅ 6/6 | ✅ 9/9 |
| 3 — task-manager-api | ✅ 4/4 | ✅ 6/6 | ✅ 9/9 |

No projeto 2, um item ficou marcado como mitigado em vez de fechado por padrão (o gate de admin fica aberto sem `ADMIN_API_KEY` configurada, para não quebrar o contrato original de `api.http`) — documentado explicitamente no relatório em vez de simplesmente marcado como resolvido. No projeto 3, três pontos que a skill inicialmente havia deixado registrados como pendentes (autenticação/autorização real, `NotificationService` nunca chamado, e o campo `password` vazando na resposta da API) foram corrigidos numa segunda rodada, a pedido explícito, e revalidados via `curl` (rotas protegidas retornando 401/403 corretamente, notificação assíncrona confirmada em log).

### Aplicações rodando após a refatoração

Prints do terminal mostrando as três fases em execução (Fase 1 detectando a stack, Fase 2 gerando o relatório e parando no gate de confirmação, e Fase 3 refatorando os três projetos em paralelo e validando boot + endpoints) estão em [`imagens/`](./imagens):

![Fase 1 rodando em paralelo nos projetos 2 e 3](./imagens/Screenshot%202026-08-29%20at%2016.50.41.png)
*Fase 1 detectando Node/Express no projeto 2 e Python/Flask no projeto 3, cada stack corretamente identificada.*

![Fase 2 concluída para o projeto 2](./imagens/Screenshot%202026-08-29%20at%2016.50.51.png)
*Relatório da Fase 2 do `ecommerce-api-legacy` salvo em `reports/audit-project-2.md`, 16 findings, aguardando confirmação para a Fase 3.*

![Gate de confirmação da Fase 2 sendo testado](./imagens/Screenshot%202026-08-29%20at%2016.52.17.png)
*Teste do gate obrigatório: respondi "N" na confirmação do projeto 2 e a skill parou sem tocar em nenhum arquivo, só atualizando a nota do checklist — prova de que a Fase 3 não roda sem aprovação humana explícita.*

![Fase 3 rodando em paralelo nos três projetos](./imagens/Screenshot%202026-08-29%20at%2016.58.39.png)
*Refatoração em andamento nos três projetos ao mesmo tempo, criando models, config e constantes nomeadas em cada stack.*

![Resumo final com os três projetos validados](./imagens/Screenshot%202026-08-29%20at%2017.15.15.png)
*Status final: os três projetos marcados como concluídos, com o detalhe das correções de autenticação aplicadas no projeto 3 e a validação via curl das rotas protegidas.*

### Observações sobre o comportamento da skill em stacks diferentes

- A mesma pasta `refactor-arch/`, copiada sem alteração nenhuma, funcionou nas três combinações de stack/nível de organização propostas no desafio (Python monolítico, Node.js orientado a classe/callback, Python parcialmente organizado).
- A Fase 1 nunca confundiu stack nem framework — inclusive detectou corretamente versões pinadas em `requirements.txt`/`package.json` e dependências declaradas mas nunca usadas (`marshmallow`, `python-dotenv` no projeto 3).
- O formato do relatório da Fase 2 saiu idêntico nos três projetos (mesmo template, mesma ordenação por severidade), mesmo com o conteúdo sendo completamente diferente — o que era o objetivo de ter um `03-report-template.md` separado do catálogo.
- A Fase 3 se comportou de forma visivelmente diferente entre o monolito (projetos 1 e 2, onde quase tudo foi criado do zero) e o projeto parcialmente organizado (projeto 3, onde a skill reorganizou e criou só as camadas que faltavam) — confirmando que a instrução de "respeitar o que já está bom" no SKILL.md realmente mudou o comportamento em tempo de execução, e não só na teoria.
- Em nenhum dos três projetos a skill precisou de correção manual nos arquivos de referência para atingir o mínimo de findings ou fechar a Fase 3 — a primeira execução completa já bateu os critérios de aceite nos três.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude login`) — foi a ferramenta escolhida para este desafio.
- Python 3.11+ e `pip` para os projetos 1 (`code-smells-project`) e 3 (`task-manager-api`).
- Node.js 18+ e `npm` para o projeto 2 (`ecommerce-api-legacy`).
- A skill já está commitada em `.claude/skills/refactor-arch/` dentro de cada um dos três projetos — não é necessário copiar nada manualmente para reproduzir a auditoria.

### Executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS com checkout)
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager, parcialmente organizado)
cd ../task-manager-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
claude "/refactor-arch"
```

Em cada execução: a Fase 1 imprime o resumo da stack, a Fase 2 gera o relatório de auditoria e para no prompt `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` — só depois de responder `y` a Fase 3 toca em qualquer arquivo.

### Como validar que a refatoração funcionou

1. **Conferir o relatório salvo em `reports/audit-project-{1,2,3}.md`** — cada um já traz, no final, o checklist de validação preenchido pela própria skill (Fase 1, 2 e 3).
2. **Subir cada aplicação já refatorada e testar os endpoints originais:**

```bash
# Projeto 1
cd code-smells-project && python app.py
curl http://localhost:5000/produtos

# Projeto 2
cd ecommerce-api-legacy && node src/app.js
curl http://localhost:3000/api/courses    # ver api.http para os demais endpoints

# Projeto 3
cd task-manager-api && python app.py
curl http://localhost:5000/tasks
```

3. **Checar que nenhum segredo continua hardcoded** — `grep -rn "SECRET_KEY\s*=\s*['\"]" .` e equivalentes não devem mais retornar literais no código-fonte de nenhum dos três projetos, só leitura de variável de ambiente (ver `config/settings.py` / `src/config/index.js` e os respectivos `.env.example`).
4. **Rodar de novo a Fase 2 (auditoria) sobre o código já refatorado** é a forma mais direta de confirmar que os findings da rodada anterior não aparecem mais — os relatórios em `reports/` já documentam esse re-scan feito pela própria skill ao final da Fase 3, projeto a projeto.