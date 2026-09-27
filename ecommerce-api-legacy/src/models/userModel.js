module.exports = function userModel(db) {
    return {
        findByEmail(email) {
            return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
        },

        findById(id) {
            return db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
        },

        create({ name, email, passwordHash }) {
            return db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        },

        deleteById(id) {
            return db.run('DELETE FROM users WHERE id = ?', [id]);
        },
    };
};
