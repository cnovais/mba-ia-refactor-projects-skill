'use strict';

const { Router } = require('express');

function checkoutRoutes(checkoutController) {
    const router = Router();
    router.post('/checkout', checkoutController.checkout);
    return router;
}

module.exports = { checkoutRoutes };
