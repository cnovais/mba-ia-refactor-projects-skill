# code-smells-project

API de E-commerce em Python/Flask, organizada em arquitetura MVC.

## Estrutura

```
app.py                 # entry point / composition root
config/settings.py     # config lida de variáveis de ambiente
db/connection.py        # conexão SQLite (flask.g) + schema + seed
models/                # persistência por domínio (produto, usuario, pedido)
validators/             # validação de entrada reusável
services/                # efeitos colaterais (notificações)
controllers/             # fluxo de aplicação (use cases) por domínio
routes/                   # declaração de rotas -> controller
middlewares/              # error handler central
```

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas de seed com hash).

## Configuração

Veja `.env.example` para as variáveis de ambiente suportadas (`SECRET_KEY`, `FLASK_DEBUG`, `DATABASE_PATH`, `ADMIN_TOKEN`, etc). Nenhuma é obrigatória para rodar localmente — os defaults são seguros.

`/admin/reset-db` exige o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`; sem essa variável definida, o endpoint fica desabilitado.
