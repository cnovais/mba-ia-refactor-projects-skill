const { HttpError } = require('../utils/httpError');

// Ponto único de tratamento de erros: erros esperados viram o status/mensagem do HttpError,
// o resto é logado e respondido como 500 sem vazar detalhes internos.
function errorHandler(err, req, res, next) {
    if (res.headersSent) return next(err);

    if (err instanceof HttpError) {
        return res.status(err.status).send(err.message);
    }
    if (err.type === 'entity.parse.failed') {
        return res.status(400).send('Bad Request: JSON inválido');
    }

    console.error(`[error] ${req.method} ${req.originalUrl}`, err);
    res.status(500).send('Erro interno');
}

module.exports = { errorHandler };
