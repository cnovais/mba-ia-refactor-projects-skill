'use strict';

const { hashPassword } = require('../services/passwordService');

// Preserves the original demo data (same users/courses/enrollment/payment),
// except the seeded password is now a real salted hash instead of a plain
// '123' string — see services/passwordService.js.
async function seed(db) {
    const leonanPasswordHash = await hashPassword('123');
    const { lastID: leonanId } = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', leonanPasswordHash]
    );

    const { lastID: cleanArchId } = await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
        ['Clean Architecture', 997.0, 1]
    );
    await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
        ['Docker', 497.0, 1]
    );

    const { lastID: enrollmentId } = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [leonanId, cleanArchId]
    );
    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, 997.0, 'PAID']
    );
}

module.exports = { seed };
