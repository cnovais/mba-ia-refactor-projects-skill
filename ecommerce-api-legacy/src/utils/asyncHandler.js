'use strict';

/**
 * Wraps an async Express handler so a rejected promise is forwarded to
 * `next(err)` instead of crashing the process or hanging the request —
 * Express 4 does not do this automatically for async handlers.
 */
function asyncHandler(handler) {
    return (req, res, next) => {
        Promise.resolve(handler(req, res, next)).catch(next);
    };
}

module.exports = { asyncHandler };
