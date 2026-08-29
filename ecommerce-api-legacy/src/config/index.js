'use strict';

try {
    // Node 20.12+/21.7+: loads variables from a local .env file into
    // process.env with no extra dependency. Fine to skip if the file
    // doesn't exist (plain env vars / defaults below still apply).
    if (typeof process.loadEnvFile === 'function') {
        process.loadEnvFile();
    }
} catch (err) {
    // No .env file present — nothing to do.
}

function readEnv(name, devDefault) {
    const value = process.env[name];
    if (value) return value;
    if (process.env.NODE_ENV === 'production') {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return devDefault;
}

// Every secret/connection value is read from the environment here — nothing
// outside this module should touch process.env directly. The dev defaults
// below are placeholders, never real credentials, so the app still boots
// out of the box in development.
const config = {
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    dbUser: process.env.DB_USER || 'dev_user',
    dbPass: readEnv('DB_PASS', 'dev_password_change_me'),
    paymentGatewayKey: readEnv('PAYMENT_GATEWAY_KEY', 'pk_test_dev_placeholder'),
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    // Left unset by default so the admin routes stay open for the demo
    // requests in api.http; set it to require the x-admin-api-key header.
    adminApiKey: process.env.ADMIN_API_KEY || null,
};

module.exports = { config };
