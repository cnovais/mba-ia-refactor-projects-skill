// Fails closed: if ADMIN_TOKEN isn't configured, every request is denied
// instead of being let through (see refactor-arch playbook recipe #4).
module.exports = function adminAuth(config) {
    return function checkAdminToken(req, res, next) {
        const token = req.header('x-admin-token');
        if (!config.adminToken || token !== config.adminToken) {
            return res.status(403).json({ error: 'Não autorizado' });
        }
        next();
    };
};
