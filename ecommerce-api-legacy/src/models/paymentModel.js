'use strict';

class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ enrollmentId, amount, status }) {
        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return { id: lastID, enrollmentId, amount, status };
    }

    findByEnrollmentId(enrollmentId) {
        return this.db.get('SELECT * FROM payments WHERE enrollment_id = ?', [enrollmentId]);
    }
}

module.exports = { PaymentModel };
