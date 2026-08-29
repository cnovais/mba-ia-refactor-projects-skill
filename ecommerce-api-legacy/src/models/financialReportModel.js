'use strict';

/**
 * Read-model for the admin financial report. A single LEFT JOIN replaces
 * the legacy N+1 cascade (one query per course, then one per enrollment,
 * then two more per enrollment for the student and payment).
 */
class FinancialReportModel {
    constructor(db) {
        this.db = db;
    }

    fetch() {
        return this.db.all(`
            SELECT
                c.id AS course_id,
                c.title AS course_title,
                e.id AS enrollment_id,
                u.name AS student_name,
                p.amount AS amount_paid,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id, e.id
        `);
    }
}

module.exports = { FinancialReportModel };
