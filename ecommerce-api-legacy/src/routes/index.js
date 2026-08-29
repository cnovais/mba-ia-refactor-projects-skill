'use strict';

const { Router } = require('express');
const { checkoutRoutes } = require('./checkoutRoutes');
const { financialReportRoutes } = require('./financialReportRoutes');
const { userRoutes } = require('./userRoutes');

function buildApiRouter(controllers) {
    const router = Router();
    router.use('/api', checkoutRoutes(controllers.checkoutController));
    router.use('/api', financialReportRoutes(controllers.financialReportController));
    router.use('/api', userRoutes(controllers.userController));
    return router;
}

module.exports = { buildApiRouter };
