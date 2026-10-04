// Cache em memória com limite de entradas (descarta a mais antiga ao estourar).
// Instanciado no composition root e injetado em quem precisa — sem estado global.
class BoundedCache {
    constructor(maxEntries = 1000) {
        this.maxEntries = maxEntries;
        this.entries = new Map();
    }

    set(key, value) {
        this.entries.delete(key);
        this.entries.set(key, value);
        if (this.entries.size > this.maxEntries) {
            const oldestKey = this.entries.keys().next().value;
            this.entries.delete(oldestKey);
        }
    }

    get(key) {
        return this.entries.get(key);
    }
}

module.exports = { BoundedCache };
