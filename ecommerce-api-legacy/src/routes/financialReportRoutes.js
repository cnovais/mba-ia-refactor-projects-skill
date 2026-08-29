'use strict';

const { Router } = require('express');
const { adminAuth } = require('../middlewares/adminAuth');

function financialReportRoutes(financialReportController) {
    const router = Router();
    router.get('/admin/financial-report', adminAuth, financialReportController.get);
    return router;
}

module.exports = { financialReportRoutes };
