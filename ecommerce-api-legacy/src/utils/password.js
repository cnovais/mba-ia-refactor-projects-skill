const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const PREFIX = 'scrypt';

// Formato armazenado: "scrypt:<salt hex>:<hash hex>"
async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const derived = await scrypt(password, salt, KEY_LENGTH);
    return `${PREFIX}:${salt.toString('hex')}:${derived.toString('hex')}`;
}

async function verifyPassword(password, stored) {
    if (typeof password !== 'string' || typeof stored !== 'string') return false;
    const [prefix, saltHex, hashHex] = stored.split(':');
    if (prefix !== PREFIX || !saltHex || !hashHex) return false;

    const expected = Buffer.from(hashHex, 'hex');
    if (expected.length !== KEY_LENGTH) return false;
    const derived = await scrypt(password, Buffer.from(saltHex, 'hex'), KEY_LENGTH);
    return crypto.timingSafeEqual(derived, expected);
}

module.exports = { hashPassword, verifyPassword };
