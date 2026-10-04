// Único módulo que lê process.env. Segredos não têm valor padrão no código.

function readOptional(name) {
    const value = process.env[name];
    return value && value.trim() !== '' ? value.trim() : null;
}

function readRequired(name, hint) {
    const value = readOptional(name);
    if (!value) {
        throw new Error(`Variável de ambiente ${name} é obrigatória. ${hint}`);
    }
    return value;
}

function readPort() {
    const raw = readOptional('PORT');
    if (raw === null) return 3000;
    const port = Number(raw);
    if (!Number.isInteger(port) || port <= 0 || port > 65535) {
        throw new Error(`PORT inválida: "${raw}"`);
    }
    return port;
}

function loadConfig() {
    return {
        port: readPort(),
        dbPath: readOptional('DB_PATH') || ':memory:',
        paymentGatewayKey: readRequired(
            'PAYMENT_GATEWAY_KEY',
            'Defina a chave do gateway de pagamento (veja .env.example).'
        ),
        // Opcional de propósito: sem ADMIN_TOKEN as rotas administrativas ficam bloqueadas (403).
        adminToken: readOptional('ADMIN_TOKEN'),
    };
}

module.exports = { loadConfig };
