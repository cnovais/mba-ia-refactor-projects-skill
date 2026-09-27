module.exports = function reportModel(db) {
    return {
        // Single joined query instead of the original N+1 fan-out
        // (one query per course, then per enrollment, then per payment).
        getCourseEnrollmentPayments() {
            return db.all(`
                SELECT
                    c.id AS course_id,
                    c.title AS course_title,
                    u.name AS student_name,
                    p.amount AS payment_amount,
                    p.status AS payment_status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.enrollment_id = e.id
                ORDER BY c.id
            `);
        },
    };
};
