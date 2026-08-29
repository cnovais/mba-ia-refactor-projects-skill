'use strict';

function notFoundHandler(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    console.error('[ERROR]', err);
    if (res.headersSent) return next(err);
    res.status(err.statusCode || 500).json({ error: err.publicMessage || 'Erro interno do servidor' });
}

module.exports = { notFoundHandler, errorHandler };
