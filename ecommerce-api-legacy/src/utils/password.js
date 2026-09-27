const crypto = require('crypto');

const KEY_LENGTH = 64;

function hashPassword(password) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(16).toString('hex');
        crypto.scrypt(password, salt, KEY_LENGTH, (err, derivedKey) => {
            if (err) return reject(err);
            resolve(`${salt}:${derivedKey.toString('hex')}`);
        });
    });
}

function verifyPassword(password, stored) {
    return new Promise((resolve, reject) => {
        const [salt, key] = stored.split(':');
        crypto.scrypt(password, salt, KEY_LENGTH, (err, derivedKey) => {
            if (err) return reject(err);
            resolve(crypto.timingSafeEqual(Buffer.from(key, 'hex'), derivedKey));
        });
    });
}

module.exports = { hashPassword, verifyPassword };
