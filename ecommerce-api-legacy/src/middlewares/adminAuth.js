const crypto = require('crypto');

function tokensMatch(provided, expected) {
    const providedDigest = crypto.createHash('sha256').update(provided).digest();
    const expectedDigest = crypto.createHash('sha256').update(expected).digest();
    return crypto.timingSafeEqual(providedDigest, expectedDigest);
}

// Fail closed: sem ADMIN_TOKEN configurado, toda requisição é negada.
function createAdminAuth(adminToken) {
    return function adminAuth(req, res, next) {
        const provided = req.get('x-admin-token');
        if (!adminToken || typeof provided !== 'string' || !tokensMatch(provided, adminToken)) {
            return res.status(403).send('Acesso negado');
        }
        next();
    };
}

module.exports = { createAdminAuth };
