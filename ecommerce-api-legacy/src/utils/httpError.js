// Erro com status HTTP: controllers lançam, o error handler central responde.
class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

module.exports = { HttpError };
