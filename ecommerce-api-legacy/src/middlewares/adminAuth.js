'use strict';

const { config } = require('../config');

/**
 * Gates admin/destructive routes behind a shared API key.
 *
 * Fails closed when ADMIN_API_KEY isn't configured: the route is disabled
 * (403) instead of left open, mirroring the /admin/reset-db gate in
 * code-smells-project. Set ADMIN_API_KEY to actually enable these routes.
 */
function adminAuth(req, res, next) {
    if (!config.adminApiKey) {
        console.warn(
            `[SECURITY] ADMIN_API_KEY não configurada — ${req.method} ${req.originalUrl} está desabilitada.`
        );
        return res.status(403).json({ error: 'Endpoint administrativo desabilitado: ADMIN_API_KEY não configurada' });
    }

    const providedKey = req.get('x-admin-api-key');
    if (providedKey !== config.adminApiKey) {
        return res.status(401).json({ error: 'Não autorizado' });
    }

    return next();
}

module.exports = { adminAuth };
