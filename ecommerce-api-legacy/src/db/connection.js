const sqlite3 = require('sqlite3').verbose();

function createDb(dbPath) {
    const raw = new sqlite3.Database(dbPath);

    function run(sql, params = []) {
        return new Promise((resolve, reject) => {
            raw.run(sql, params, function callback(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    function get(sql, params = []) {
        return new Promise((resolve, reject) => {
            raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    function all(sql, params = []) {
        return new Promise((resolve, reject) => {
            raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    async function initDb() {
        await run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
        await run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        await run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        await run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        await run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

        const { lastID: userId } = await run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', '123']
        );
        await run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
            ['Clean Architecture', 997.0, 'Docker', 497.0]
        );
        const { lastID: enrollmentId } = await run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, 1]
        );
        await run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, 997.0, 'PAID']
        );
    }

    return { run, get, all, initDb };
}

module.exports = createDb;
