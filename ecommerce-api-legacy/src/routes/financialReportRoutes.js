const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function financialReportRoutes(getFinancialReport) {
    const router = express.Router();
    router.get('/financial-report', asyncHandler(getFinancialReport));
    return router;
};
