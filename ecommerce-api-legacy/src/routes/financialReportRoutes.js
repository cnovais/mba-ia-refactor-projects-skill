const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function financialReportRoutes(financialReportController, adminAuth) {
    const router = express.Router();
    router.get('/api/admin/financial-report', adminAuth, asyncHandler(financialReportController.getFinancialReport));
    return router;
}

module.exports = { financialReportRoutes };
