const { PAYMENT_STATUS } = require('../utils/paymentGateway');

// Leitura agregada para o relatório financeiro: uma única query com JOIN no lugar do N+1.
class ReportModel {
    constructor(db) {
        this.db = db;
    }

    async financialReport() {
        const rows = await this.db.all(`
            SELECT c.id AS courseId, c.title AS courseTitle,
                   e.id AS enrollmentId,
                   u.name AS studentName,
                   p.amount AS paymentAmount, p.status AS paymentStatus
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.id = (
                SELECT MIN(id) FROM payments WHERE enrollment_id = e.id
            )
            ORDER BY c.id, e.id
        `);

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.courseId)) {
                byCourse.set(row.courseId, { course: row.courseTitle, revenue: 0, students: [] });
            }
            if (row.enrollmentId === null) continue;

            const courseData = byCourse.get(row.courseId);
            if (row.paymentStatus === PAYMENT_STATUS.PAID) {
                courseData.revenue += row.paymentAmount;
            }
            courseData.students.push({
                student: row.studentName ?? 'Unknown',
                paid: row.paymentAmount ?? 0,
            });
        }
        return [...byCourse.values()];
    }
}

module.exports = { ReportModel };
