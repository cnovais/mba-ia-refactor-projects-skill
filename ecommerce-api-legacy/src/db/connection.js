const sqlite3 = require('sqlite3');

// Wrapper com Promises sobre o driver sqlite3 (callback-style), para uso com async/await.
class Database {
    constructor(rawDb) {
        this.rawDb = rawDb;
        this.queue = Promise.resolve();
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.rawDb.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.rawDb.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.rawDb.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.rawDb.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    // Transações são enfileiradas: há uma única conexão, então duas transações
    // concorrentes não podem se intercalar.
    transaction(work) {
        const result = this.queue.then(async () => {
            await this.run('BEGIN IMMEDIATE');
            try {
                const value = await work();
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        });
        this.queue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => {
            this.rawDb.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

function openDatabase(path) {
    return new Promise((resolve, reject) => {
        const rawDb = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(new Database(rawDb))));
    });
}

module.exports = { openDatabase };
