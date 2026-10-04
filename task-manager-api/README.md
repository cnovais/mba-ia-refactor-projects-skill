# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC (models / routes / controllers) com configuração por variáveis de ambiente, autenticação por token assinado e tratamento de erros centralizado.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env
# preencha SECRET_KEY no .env (obrigatório — a aplicação não sobe sem ele):
python -c "import secrets; print(secrets.token_hex(32))"
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (ajuste com `HOST`/`PORT`). O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**. Usuários do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd`, `pedro@email.com` / `pass`.

Em produção, rode com um servidor WSGI, por exemplo `gunicorn "app:create_app()"`, com `FLASK_DEBUG` desligado.

## Variáveis de ambiente

Veja `.env.example`. Apenas `SECRET_KEY` é obrigatória; `CORS_ORIGINS` (lista separada por vírgulas) libera acesso cross-origin, vazio = nenhum. Notificações por e-mail só são enviadas se `SMTP_HOST`, `SMTP_USER` e `SMTP_PASSWORD` estiverem definidos.

## Autenticação

`POST /login` devolve `token`; envie-o como `Authorization: Bearer <token>` (expira após `TOKEN_MAX_AGE_SECONDS`, padrão 8h).

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /health`, `POST /login`, `POST /users` (cadastro com role `user`) |
| Usuário autenticado | `/tasks*`, `GET /users*`, `GET /categories`, `/reports/*`, `PUT /users/<id>` (apenas o próprio cadastro, sem alterar `role`/`active`) |
| Admin | `DELETE /users/<id>`, `POST/PUT/DELETE /categories*`, criar usuários com role `admin`/`manager`, alterar `role`/`active` ou outros usuários |

Sem token (ou com token inválido/expirado) a resposta é `401`; sem permissão, `403`. As respostas não incluem mais o hash da senha.
