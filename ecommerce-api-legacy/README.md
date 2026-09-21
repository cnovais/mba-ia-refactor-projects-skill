# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

### Rotas administrativas

`GET /api/admin/financial-report` e `DELETE /api/users/:id` ficam **desabilitadas por padrão** (403) — o gate `adminAuth` falha fechado quando `ADMIN_API_KEY` não está definida em `.env`. Defina `ADMIN_API_KEY` e envie o mesmo valor no header `x-admin-api-key` para habilitá-las.
