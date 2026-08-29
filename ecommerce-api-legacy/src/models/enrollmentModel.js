'use strict';

class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ userId, courseId }) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return { id: lastID, userId, courseId };
    }

    findByCourseId(courseId) {
        return this.db.all('SELECT * FROM enrollments WHERE course_id = ?', [courseId]);
    }
}

module.exports = { EnrollmentModel };
