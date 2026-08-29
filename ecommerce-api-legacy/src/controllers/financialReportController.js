'use strict';

const { asyncHandler } = require('../utils/asyncHandler');
const { PAYMENT_STATUS } = require('../services/paymentGatewayService');

// Aggregates the flat join rows from FinancialReportModel into the same
// shape the legacy N+1 handler produced: one entry per course, with a
// running revenue total (PAID payments only) and a per-student list.
function buildReport(rows) {
    const coursesById = new Map();

    for (const row of rows) {
        if (!coursesById.has(row.course_id)) {
            coursesById.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }

        if (row.enrollment_id === null) continue; // course has no enrollments at all

        const courseData = coursesById.get(row.course_id);
        if (row.payment_status === PAYMENT_STATUS.PAID) {
            courseData.revenue += row.amount_paid;
        }
        courseData.students.push({
            student: row.student_name || 'Unknown',
            paid: row.amount_paid || 0,
        });
    }

    return Array.from(coursesById.values());
}

function makeFinancialReportController({ financialReportModel }) {
    return {
        get: asyncHandler(async (req, res) => {
            const rows = await financialReportModel.fetch();
            res.json(buildReport(rows));
        }),
    };
}

module.exports = { makeFinancialReportController, buildReport };
