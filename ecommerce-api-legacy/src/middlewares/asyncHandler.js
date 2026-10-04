// Express 4 não captura rejeições de handlers async: encaminha para o error handler.
function asyncHandler(handler) {
    return (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
}

module.exports = { asyncHandler };
