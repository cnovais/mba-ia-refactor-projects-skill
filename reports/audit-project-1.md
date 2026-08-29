================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — 4 arquivos sem separação real de camadas; controllers.py fala
               diretamente com models.py, que constrói SQL cru e mistura persistência,
               validação e regra de negócio para 4 domínios diferentes.
Source files:  4 files analyzed (app.py, controllers.py, database.py, models.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] God Class / God Module
File: models.py:1-314
Description: Um único arquivo contém acesso a dados, montagem de SQL, e regra de negócio (cálculo de desconto, baixa de estoque, composição de pedidos) para 4 domínios (produtos, usuários, pedidos, itens_pedido).
Impact: Impossível testar qualquer domínio isoladamente; uma mudança em lógica de pedidos pode quebrar produtos/usuários por estarem no mesmo arquivo.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`, cada um só com sua própria persistência.

### [CRITICAL] Hardcoded Credentials & Exposição de Segredo em Endpoint
File: app.py:7-8; controllers.py:285-290
Description: `SECRET_KEY` fixo em `"minha-chave-super-secreta-123"` e `DEBUG=True` hardcoded no código-fonte; o endpoint `/health` (controllers.py:285-290) devolve o mesmo `secret_key` e o flag `debug` no corpo da resposta JSON.
Impact: Qualquer pessoa com acesso ao repositório obtém a chave de sessão; qualquer cliente que chame `/health` também a recebe em produção, permitindo forjar sessões/cookies assinados.
Recommendation: Ler `SECRET_KEY`/`DEBUG` de variáveis de ambiente via módulo de config; nunca incluir segredos no corpo de uma resposta.

### [CRITICAL] SQL Injection via Concatenação de String
File: models.py:28, 48-50, 58-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 158-166, 174, 188, 192, 220, 279-280, 291-297
Description: Praticamente toda função de acesso a dados monta SQL concatenando strings com valores vindos direto da requisição (`"WHERE id = " + str(id)`, `"VALUES ('" + nome + "', ...)"`), inclusive no login (`models.py:109-111`), onde email e senha do usuário entram direto na query.
Impact: Qualquer parâmetro (id, nome, email, senha, termo de busca) pode ser usado para ler, alterar ou apagar dados fora do escopo pretendido, incluindo bypass de autenticação no login.
Recommendation: Trocar toda concatenação por queries parametrizadas (`cursor.execute("... WHERE id = ?", (id,))`) — ver playbook item 3.

### [CRITICAL] Endpoints Perigosos Sem Autenticação
File: app.py:47-57 (`/admin/reset-db`), app.py:59-78 (`/admin/query`)
Description: `/admin/reset-db` apaga todas as tabelas via POST sem nenhuma checagem de identidade; `/admin/query` executa qualquer SQL enviado no corpo da requisição (`dados.get("sql")`) diretamente no banco.
Impact: Qualquer requisição não autenticada pode apagar a base inteira ou executar SQL arbitrário (leitura, alteração, exclusão de qualquer tabela).
Recommendation: Remover `/admin/query` (não tem propósito de produto legítimo) e proteger `/admin/reset-db` atrás de autenticação/autorização de admin, se for mantido.

### [HIGH] Lógica de Negócio e Efeitos Colaterais Dentro do Controller
File: controllers.py:188-220 (`criar_pedido`)
Description: O handler de criação de pedido chama o model e, em seguida, dispara "notificações" (`print("ENVIANDO EMAIL...")`, `print("ENVIANDO SMS...")`, `print("ENVIANDO PUSH...")`) diretamente inline, sem nenhuma abstração de serviço de notificação.
Impact: Lógica de notificação não pode ser testada, reutilizada ou trocada (ex: por um serviço de e-mail real) sem editar o controller; qualquer novo canal exige duplicar o padrão em outros endpoints.
Recommendation: Extrair para um `notification_service` chamado pelo controller — ver playbook item 5.

### [HIGH] Estado Global Mutável para Conexão de Banco
File: database.py:4-11
Description: `db_connection` é uma variável de módulo reatribuída via `global` dentro de `get_db()`, funcionando como singleton implícito compartilhado por toda a aplicação.
Impact: Não é possível isolar testes (o mesmo banco/conexão vaza entre eles) nem trocar a implementação sem editar `database.py` diretamente; comportamento depende da ordem de chamadas.
Recommendation: Mover a conexão para o contexto de aplicação/requisição (`flask.g`) com `teardown_appcontext` — ver playbook item 7.

### [HIGH] Acoplamento Forte / Ausência de Injeção de Dependência
File: database.py:7-11; models.py (todas as 12 funções chamam `get_db()` diretamente)
Description: Toda função de `models.py` importa e chama `get_db()` do módulo global em vez de receber a conexão/sessão como parâmetro.
Impact: Impossível substituir o banco por um dublê de teste sem monkeypatching; qualquer refatoração de acesso a dados exige tocar em todas as 12 funções.
Recommendation: Injetar a conexão/sessão via parâmetro ou via composição no controller — ver playbook item 6.

### [HIGH] Senhas em Texto Puro (Sem Hash)
File: database.py:31 (coluna `senha` sem hashing); models.py:109-120 (`login_usuario` compara texto puro)
Description: A coluna `senha` armazena a senha exatamente como enviada, e o login compara `senha` em texto puro dentro da própria query SQL.
Impact: Um vazamento do banco expõe todas as senhas em claro; combinado com a injeção de SQL do login, um atacante nem precisa vazar o banco para comprometer contas.
Recommendation: Usar hashing salgado e lento (`werkzeug.security.generate_password_hash`/`check_password_hash`) — ver playbook item 8.

### [MEDIUM] Consultas N+1 ao Montar Pedidos
File: models.py:171-201 (`get_pedidos_usuario`), models.py:203-233 (`get_todos_pedidos`)
Description: Para cada pedido, o código abre um novo cursor e consulta `itens_pedido`, e para cada item abre outro cursor para buscar o nome do produto — uma query por item, dentro de um loop por pedido.
Impact: Tempo de resposta cresce linearmente com o número de pedidos × itens; listar "todos os pedidos" fica cada vez mais lento conforme a base cresce.
Recommendation: Buscar itens e nomes de produtos com um `JOIN`/`WHERE id IN (...)` único em vez de um cursor por item — ver playbook item 9.

### [MEDIUM] Validação Duplicada Entre Criação e Atualização
File: controllers.py:24-58 (`criar_produto`), controllers.py:64-96 (`atualizar_produto`)
Description: O mesmo bloco de validações (nome/preço/estoque obrigatórios, preço/estoque não-negativos) está copiado quase palavra por palavra nas duas funções.
Impact: Uma correção de regra de validação feita em uma função facilmente fica esquecida na outra, gerando comportamento inconsistente entre criar e atualizar.
Recommendation: Extrair um validador único (`validar_produto(dados)`) reutilizado pelos dois fluxos — ver playbook item 10.

### [MEDIUM] Tratamento de Erro Inconsistente e Vazamento de Detalhes Internos
File: controllers.py (todas as 15 funções, ex: linhas 10-12, 21-22, 60-62, 254-255)
Description: Todo handler repete seu próprio `except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo a mensagem crua da exceção Python para o cliente e usando `print` como "log".
Impact: Mensagens de exceção interna (nomes de tabela, tipos de erro do driver SQL) vazam para qualquer chamador; não há log estruturado para investigar incidentes em produção.
Recommendation: Centralizar em um error handler (`@app.errorhandler(Exception)`) com logging apropriado e resposta genérica — ver playbook item 12.

### [MEDIUM] Servidor de Desenvolvimento em Modo Debug Usado Como Produção
File: app.py:8, app.py:88
Description: `app.config["DEBUG"] = True` e `app.run(..., debug=True)` — o servidor embutido de desenvolvimento do Flask, com debugger interativo habilitado, é o que sobe a aplicação.
Impact: O debugger do Werkzeug pode expor um console de execução de código arbitrário se acessível externamente, e o servidor de dev não é dimensionado para tráfego real.
Recommendation: Usar um servidor WSGI de produção (gunicorn/uvicorn+wsgi adapter) com debug desligado fora de ambiente local — ver catálogo, seção de APIs obsoletas.

### [LOW] Magic Numbers nos Percentuais de Desconto
File: models.py:256-262
Description: Os limiares de faturamento (`10000`, `5000`, `1000`) e as taxas de desconto (`0.1`, `0.05`, `0.02`) aparecem como literais soltos dentro de `if/elif`.
Impact: Ninguém consegue alterar a política de desconto com confiança sem ler e re-interpretar a função inteira.
Recommendation: Extrair para constantes nomeadas (`DISCOUNT_TIER_HIGH_THRESHOLD`, etc.) — ver playbook item 13.

### [LOW] Logging via print() com Concatenação de String
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Mensagens de log usam `print("texto " + str(variavel) + "...")` em vez de f-strings ou um logger configurado.
Impact: Sem níveis de log, timestamps ou destino configurável; dificulta filtrar/enviar logs em produção.
Recommendation: Adotar `logging` padrão do Python com f-strings, nível apropriado (`info`/`error`) por mensagem.

### [LOW] Lista de Categorias Válidas Inline
File: controllers.py:52
Description: `categorias_validas = ["informatica", "moveis", ...]` é declarada dentro da função em vez de ser uma constante/config compartilhada.
Impact: Se outro endpoint precisar da mesma lista, ela será recriada e pode divergir com o tempo.
Recommendation: Mover para uma constante de módulo ou para o model de produto.

================================
Total: 15 findings
================================

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python, via `requirements.txt` + sintaxe)
- [x] Framework detectado corretamente (Flask 3.1.1, pinado em `requirements.txt`)
- [x] Domínio da aplicação descrito corretamente (E-commerce: produtos, pedidos, usuários — inferido das rotas e tabelas)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos: app.py, controllers.py, database.py, models.py — confirmado com `wc -l`)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido em `references/03-report-template.md`
- [x] Cada finding tem arquivo e linhas exatos (verificados abrindo cada arquivo)
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (15 encontrados)
- [x] Detecção de APIs deprecated incluída — verificada (nenhuma API deprecated clássica como `datetime.utcnow()`/`Query.get()` está em uso neste projeto; o único achado da categoria é o servidor de dev do Flask em modo debug, reportado acima como MEDIUM)
- [x] Skill pausa e pede confirmação antes da Fase 3 (aguardando decisão do humano abaixo)

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (`config/`, `db/`, `models/`, `validators/`, `services/`, `controllers/`, `routes/`, `middlewares/`, `app.py`)
- [x] Configuração extraída para módulo de config (sem hardcoded) — `config/settings.py` lê `SECRET_KEY`, `FLASK_DEBUG`, `DATABASE_PATH`, `ADMIN_TOKEN` etc. de variáveis de ambiente; `SECRET_KEY` nunca mais é um literal no código
- [x] Models criados para abstrair dados — `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py` (inclui `itens_pedido`, mesmo agregado que `pedidos`), cada um só com sua persistência, conexão injetada por parâmetro, todo SQL parametrizado
- [x] Views/Routes separadas para visualização ou roteamento — `routes/produto_routes.py`, `usuario_routes.py`, `pedido_routes.py`, `sistema_routes.py`, só declaração de rota -> controller
- [x] Controllers concentram o fluxo da aplicação — `controllers/produto_controller.py`, `usuario_controller.py`, `pedido_controller.py`, `sistema_controller.py`, `admin_controller.py`
- [x] Error handling centralizado — `middlewares/error_handler.py` (`@app.errorhandler(Exception)`), controllers não têm mais try/except genérico
- [x] Entry point claro — `app.py` só cria a app, aplica config, inicializa o banco, registra o error handler e monta os blueprints (composition root)
- [x] Aplicação inicia sem erros — testado via `python app.py` (venv com `pip install -r requirements.txt`), log de boot limpo, sem exceptions
- [x] Endpoints originais respondem corretamente — todos os 16 endpoints originais exercitados via curl (ver detalhe abaixo), mesmo path/método/formato de resposta preservado para requisição bem-formada

#### Detalhe da validação de endpoints (Fase 3)

| Endpoint | Teste | Resultado |
|---|---|---|
| `GET /` | básico | 200, mesmo payload de boas-vindas |
| `GET /health` | básico | 200, **sem** `secret_key` no corpo (CRITICAL corrigido); `debug`/`ambiente` refletem config real |
| `GET /produtos`, `GET /produtos/<id>`, `GET /produtos/busca` | básico + 404 | 200 / 404 preservados |
| `POST /produtos` | válido, campo faltando, tentativa de SQL injection no `nome` | 201 / 400 / 201 (payload gravado como dado literal, tabela não afetada — SQLi neutralizado) |
| `PUT /produtos/<id>`, `DELETE /produtos/<id>` | básico | 200 preservados |
| `GET /usuarios`, `GET /usuarios/<id>` | básico | 200 preservados |
| `POST /usuarios` | criação | 201, senha gravada com hash |
| `POST /login` | credencial correta, incorreta, tentativa de SQL injection (`x' OR '1'='1`) | 200 / 401 / 401 — bypass de autenticação via SQLi que existia antes foi eliminado |
| `POST /pedidos` | criação com 2 itens | 201, total calculado correto, notificações logadas via `notification_service` |
| `GET /pedidos`, `GET /pedidos/usuario/<id>` | listagem | 200, itens montados via JOIN único (sem N+1) |
| `PUT /pedidos/<id>/status` | válido e status inválido | 200 / 400 preservados; notificação de aprovado/cancelado logada |
| `GET /relatorios/vendas` | básico | 200, cálculo de desconto preservado (constantes nomeadas) |
| `POST /admin/reset-db` | sem token, token errado, token correto | 403 / 403 / 200 — endpoint agora protegido (antes era público) |
| `POST /admin/query` | qualquer chamada | 404 — endpoint removido (backdoor sem propósito legítimo, conforme recomendação) |
| `GET /rota-inexistente` | rota não mapeada | 404 padrão do Flask preservado (não convertido em 500 pelo error handler central) |
| Erro inesperado (`preco_min=abc` não numérico) | força `ValueError` | 500 com `{"erro": "Erro interno do servidor"}` — antes vazava a mensagem crua da exceção Python; agora resposta genérica + stack trace no log do servidor |

Servidor de validação foi encerrado (`kill`) após todos os checks acima passarem.

#### Findings da Fase 2 — status após Fase 3

Todos os 15 findings do relatório foram corrigidos nesta refatoração:

- CRITICAL God Class/Module → resolvido (split em `models/` e `controllers/` por domínio)
- CRITICAL Hardcoded Credentials/segredo no `/health` → resolvido (`config/settings.py`, `secret_key` removido da resposta)
- CRITICAL SQL Injection → resolvido (100% das queries parametrizadas ou literais fixas, sem interpolação de dado de usuário)
- CRITICAL Endpoints admin sem autenticação → resolvido (`/admin/query` removido; `/admin/reset-db` exige `X-Admin-Token`)
- HIGH Lógica de negócio/efeitos colaterais no controller → resolvido (`services/notification_service.py`)
- HIGH Estado global mutável de conexão → resolvido (`flask.g` + `teardown_appcontext` em `db/connection.py`)
- HIGH Acoplamento forte / sem DI → resolvido (toda função de model recebe a conexão por parâmetro)
- HIGH Senhas em texto puro → resolvido (`werkzeug.security.generate_password_hash`/`check_password_hash`)
- MEDIUM Consultas N+1 → resolvido (`_montar_pedidos` usa um único `JOIN`/`WHERE id IN (...)`)
- MEDIUM Validação duplicada criar/atualizar → resolvido (`validators/produto_validator.py` reusado pelos dois fluxos — nota: isso torna `atualizar_produto` mais estrito do que antes, passando a exigir também tamanho de nome e categoria válida, alinhado ao comportamento de `criar_produto`; mudança deliberada, recomendada pelo próprio finding)
- MEDIUM Tratamento de erro inconsistente / vazamento de detalhes internos → resolvido (`middlewares/error_handler.py`)
- MEDIUM Servidor de dev em modo debug como produção → resolvido (`DEBUG` default `false`, lido de `FLASK_DEBUG`; documentado usar WSGI de produção fora do ambiente local)
- LOW Magic numbers de desconto → resolvido (constantes nomeadas em `models/pedido_model.py`)
- LOW Logging via `print()` → resolvido (módulo `logging` padrão em todos os módulos)
- LOW Lista de categorias inline → resolvido (`CATEGORIAS_VALIDAS` em `models/produto_model.py`)

Nenhum finding foi deliberadamente adiado — os 15/15 foram corrigidos nesta Fase 3.
