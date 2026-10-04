# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

Requer Node.js 22.9+.

```bash
npm install
cp .env.example .env   # preencha PAYMENT_GATEWAY_KEY (e ADMIN_TOKEN para as rotas admin)
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Variáveis de ambiente (veja `.env.example`):

- `PORT` — porta do servidor (padrão `3000`).
- `DB_PATH` — caminho do banco SQLite (padrão `:memory:`).
- `PAYMENT_GATEWAY_KEY` — **obrigatória**. Sem ela a aplicação se recusa a iniciar; não há
  valor padrão no código, e a chave nunca é logada.
- `ADMIN_TOKEN` — token exigido nas rotas administrativas. **Sem essa variável definida, as
  rotas administrativas ficam bloqueadas (403)** — não há acesso liberado por padrão.

## Regras de acesso

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header
  `x-admin-token: <ADMIN_TOKEN>`.
- `POST /api/checkout` exige `pwd`. Se o e-mail já tem conta, a senha precisa conferir com
  a cadastrada — senha errada retorna `401` sem criar matrícula nem pagamento.
- Usuário do seed: `leonan@fullcycle.com.br` / senha `123`.

## Arquitetura

```
src/
├── app.js            # composition root: monta config, DB, models, controllers e rotas
├── config/           # única leitura de variáveis de ambiente
├── db/               # conexão SQLite com Promises, schema e seed
├── models/           # acesso a dados por entidade (User, Course, Enrollment, Payment, AuditLog, Report)
├── controllers/      # orquestração dos casos de uso (checkout, relatório financeiro, usuários)
├── routes/           # declaração das rotas Express
├── validators/       # validação de entrada
├── middlewares/      # error handler central, auth admin (fail closed) e wrapper async
└── utils/            # hashing de senha (scrypt), gateway de pagamento simulado, cache, HttpError
```
