'use strict';

const { config } = require('../config');

/**
 * Gates admin/destructive routes behind a shared API key.
 *
 * Left permissive (a no-op, with a warning) when ADMIN_API_KEY isn't
 * configured, so the existing demo requests in api.http keep working
 * unchanged out of the box — see the audit report's deferred-items note.
 * Set ADMIN_API_KEY before exposing this API beyond local development.
 */
function adminAuth(req, res, next) {
    if (!config.adminApiKey) {
        console.warn(
            `[SECURITY] ADMIN_API_KEY não configurada — ${req.method} ${req.originalUrl} está aberta sem autenticação.`
        );
        return next();
    }

    const providedKey = req.get('x-admin-api-key');
    if (providedKey !== config.adminApiKey) {
        return res.status(401).json({ error: 'Não autorizado' });
    }

    return next();
}

module.exports = { adminAuth };
