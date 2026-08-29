'use strict';

class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findAll() {
        return this.db.all('SELECT * FROM courses');
    }

    findActiveById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

module.exports = { CourseModel };
