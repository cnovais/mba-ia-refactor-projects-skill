# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Variáveis de ambiente (veja `.env.example`):

- `PORT` — porta do servidor (padrão `3000`).
- `DB_PATH` — caminho do banco SQLite (padrão `:memory:`).
- `PAYMENT_GATEWAY_KEY` — chave do gateway de pagamento (opcional, não é mais logada).
- `ADMIN_TOKEN` — token exigido nas rotas administrativas. **Sem essa variável definida, as
  rotas administrativas ficam bloqueadas (403)** — não há acesso liberado por padrão.

## Rotas administrativas

`GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header
`x-admin-token: <ADMIN_TOKEN>`. Configure `ADMIN_TOKEN` no ambiente antes de chamá-las.

## Arquitetura

```
src/
├── app.js            # composition root: monta config, DB, models, controllers e rotas
├── config/           # leitura de variáveis de ambiente
├── db/                # conexão SQLite + wrapper com Promises
├── models/            # acesso a dados por entidade (User, Course, Enrollment, Payment, AuditLog, Report)
├── controllers/       # orquestração dos casos de uso (checkout, relatório financeiro, usuários)
├── routes/            # declaração das rotas Express
├── middlewares/       # error handler central, auth admin e wrapper async
└── utils/             # cache, hashing de senha e gateway de pagamento simulado
```
