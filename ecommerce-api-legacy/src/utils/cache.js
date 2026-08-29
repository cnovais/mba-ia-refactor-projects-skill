'use strict';

/**
 * Small in-memory store, instantiated once at the composition root and
 * passed to whoever needs it (constructor injection) — replaces the old
 * module-level `globalCache` object every request mutated directly, and
 * drops the `totalRevenue` global that was exported/imported but never
 * actually read or incremented anywhere.
 */
class MemoryCache {
    constructor() {
        this.store = new Map();
    }

    set(key, value) {
        console.log(`[LOG] Salvando no cache: ${key}`);
        this.store.set(key, value);
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = { MemoryCache };
