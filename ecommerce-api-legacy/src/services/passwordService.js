'use strict';

const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;

// Real, salted, slow password hashing (Node's built-in scrypt KDF) —
// replaces the legacy `badCrypto` function, which just repeated a base64
// slice 10,000 times and was trivially reversible.
async function hashPassword(plainPassword) {
    const salt = crypto.randomBytes(16).toString('hex');
    const derivedKey = await scrypt(plainPassword, salt, KEY_LENGTH);
    return `${salt}:${derivedKey.toString('hex')}`;
}

async function verifyPassword(plainPassword, storedHash) {
    if (!storedHash || !storedHash.includes(':')) return false;
    const [salt, hashHex] = storedHash.split(':');
    const derivedKey = await scrypt(plainPassword, salt, KEY_LENGTH);
    const storedKey = Buffer.from(hashHex, 'hex');
    if (storedKey.length !== derivedKey.length) return false;
    return crypto.timingSafeEqual(storedKey, derivedKey);
}

module.exports = { hashPassword, verifyPassword };
