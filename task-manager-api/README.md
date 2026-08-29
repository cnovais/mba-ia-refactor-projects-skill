# task-manager-api

API de Task Manager em Python/Flask, organizada em MVC:

- `models/` — persistência (SQLAlchemy) e invariantes de domínio (ex.: `Task.is_overdue()`).
- `controllers/` — os casos de uso: validam entrada, chamam os models, decidem status/payload.
- `routes/` — só roteamento: parse da request → chama o controller → devolve a resposta.
- `validators/` — regras de validação de payload, reaproveitadas por create e update.
- `config/` — toda config/segredo lido de variáveis de ambiente (`config/settings.py`).
- `middlewares/error_handler.py` — tratamento de erro centralizado (`errors.ApiError` + handler genérico).
- `services/notification_service.py` — envio de email, com host/usuário/senha injetados via config; disparado em background (thread) quando uma task é atribuída a um usuário, sem bloquear a resposta.
- `auth/tokens.py` — geração/verificação de token assinado usado pelo login.
- `auth/decorators.py` — `login_required`/`admin_required`, aplicados a toda rota de escrita.

## Autenticação

`POST /tasks`, `PUT/DELETE /tasks/<id>`, `POST/PUT/DELETE /categories`, `PUT
/users/<id>` e `DELETE /users/<id>` exigem um token válido. `POST /users`
(cadastro) e `POST /login` continuam públicos.

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Nova task"}'
```

Regras de autorização: um usuário só edita o próprio perfil (`PUT /users/<id>`),
exceto um admin, que pode editar qualquer um; só um admin pode alterar `role`; só
um admin pode deletar um usuário (`DELETE /users/<id>` cascateia para as tasks dele).

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # ajuste os valores se necessário; o padrão já funciona localmente

python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (ajustável via `FLASK_PORT` no `.env`). O
`seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de
exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar
listas vazias.

Consulte `../reports/audit-project-3.md` para o relatório de auditoria de
arquitetura e o checklist de validação desta refatoração.
