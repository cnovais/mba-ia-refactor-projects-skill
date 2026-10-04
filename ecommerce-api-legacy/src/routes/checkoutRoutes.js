const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function checkoutRoutes(checkoutController) {
    const router = express.Router();
    router.post('/api/checkout', asyncHandler(checkoutController.checkout));
    return router;
}

module.exports = { checkoutRoutes };
