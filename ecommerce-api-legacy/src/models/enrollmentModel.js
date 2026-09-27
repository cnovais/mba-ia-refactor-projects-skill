module.exports = function enrollmentModel(db) {
    return {
        create(userId, courseId) {
            return db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
        },

        findByUserId(userId) {
            return db.all('SELECT * FROM enrollments WHERE user_id = ?', [userId]);
        },

        deleteByUserId(userId) {
            return db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
        },
    };
};
