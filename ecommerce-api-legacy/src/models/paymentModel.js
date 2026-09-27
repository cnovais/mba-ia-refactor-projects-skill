module.exports = function paymentModel(db) {
    return {
        create(enrollmentId, amount, status) {
            return db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
        },

        deleteByEnrollmentIds(enrollmentIds) {
            if (enrollmentIds.length === 0) return Promise.resolve({ changes: 0 });
            const placeholders = enrollmentIds.map(() => '?').join(',');
            return db.run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
        },
    };
};
