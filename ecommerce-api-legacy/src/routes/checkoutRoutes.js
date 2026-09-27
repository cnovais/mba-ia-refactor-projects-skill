const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function checkoutRoutes(checkout) {
    const router = express.Router();
    router.post('/checkout', asyncHandler(checkout));
    return router;
};
