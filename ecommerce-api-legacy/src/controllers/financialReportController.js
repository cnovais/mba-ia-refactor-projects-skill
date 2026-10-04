function createFinancialReportController({ reportModel }) {
    async function getFinancialReport(req, res) {
        res.json(await reportModel.financialReport());
    }

    return { getFinancialReport };
}

module.exports = { createFinancialReportController };
