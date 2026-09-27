const port = Number(process.env.PORT) || 3000;
const dbPath = process.env.DB_PATH || ':memory:';
const paymentGatewayKey = process.env.PAYMENT_GATEWAY_KEY || null;
const adminToken = process.env.ADMIN_TOKEN || null;

if (!adminToken) {
    console.warn('ADMIN_TOKEN não configurado — rotas administrativas ficarão bloqueadas até que seja definido.');
}

module.exports = { port, dbPath, paymentGatewayKey, adminToken };
