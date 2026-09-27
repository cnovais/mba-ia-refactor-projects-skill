module.exports = function financialReportController({ reportModel }) {
    return async function getFinancialReport(req, res) {
        const rows = await reportModel.getCourseEnrollmentPayments();

        const reportByCourseId = new Map();
        for (const row of rows) {
            if (!reportByCourseId.has(row.course_id)) {
                reportByCourseId.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }

            const courseReport = reportByCourseId.get(row.course_id);
            if (row.student_name) {
                if (row.payment_status === 'PAID') courseReport.revenue += row.payment_amount;
                courseReport.students.push({ student: row.student_name, paid: row.payment_amount || 0 });
            }
        }

        res.json(Array.from(reportByCourseId.values()));
    };
};
