'use strict';

const sqlite3 = require('sqlite3').verbose();

function run(rawDb, sql, params = []) {
    return new Promise((resolve, reject) => {
        rawDb.run(sql, params, function callback(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(rawDb, sql, params = []) {
    return new Promise((resolve, reject) => {
        rawDb.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function all(rawDb, sql, params = []) {
    return new Promise((resolve, reject) => {
        rawDb.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

/**
 * Thin promise-based wrapper around the callback-style `sqlite3` driver.
 * Models receive an instance of this via constructor injection instead of
 * reaching for a module-level/global connection — swap in a different
 * implementation (or a test double) without touching model code.
 */
class Database {
    constructor(rawDb) {
        this.raw = rawDb;
    }

    run(sql, params) {
        return run(this.raw, sql, params);
    }

    get(sql, params) {
        return get(this.raw, sql, params);
    }

    all(sql, params) {
        return all(this.raw, sql, params);
    }

    close() {
        return new Promise((resolve, reject) => {
            this.raw.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

function createDatabase(dbPath) {
    return new Database(new sqlite3.Database(dbPath));
}

module.exports = { Database, createDatabase };
