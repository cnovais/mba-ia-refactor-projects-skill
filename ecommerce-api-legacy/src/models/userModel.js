class UserModel {
    constructor(db) {
        this.db = db;
    }

    findById(id) {
        return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    }

    // Inclui o hash da senha: uso restrito à verificação de credenciais.
    findByEmailWithPassword(email) {
        return this.db.get('SELECT id, name, email, pass AS passwordHash FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        return lastID;
    }

    async deleteById(id) {
        const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
        return changes > 0;
    }
}

module.exports = { UserModel };
