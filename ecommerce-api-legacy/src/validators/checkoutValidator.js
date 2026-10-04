const { HttpError } = require('../utils/httpError');
const { isNonEmptyString, parsePositiveInt } = require('./common');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d{12,19}$/;

// Converte o corpo legado (usr, eml, pwd, c_id, card) em nomes de domínio e valida.
function validateCheckout(body = {}) {
    const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card } = body;

    const errors = [];
    if (!isNonEmptyString(name)) errors.push('usr');
    if (!isNonEmptyString(email) || !EMAIL_PATTERN.test(email.trim())) errors.push('eml');
    if (!isNonEmptyString(password)) errors.push('pwd');
    const courseId = parsePositiveInt(rawCourseId);
    if (courseId === null) errors.push('c_id');
    const cardNumber = typeof card === 'string' ? card.replace(/[\s-]/g, '') : '';
    if (!CARD_PATTERN.test(cardNumber)) errors.push('card');

    if (errors.length > 0) {
        throw new HttpError(400, `Bad Request: campos inválidos ou ausentes (${errors.join(', ')})`);
    }

    return { name: name.trim(), email: email.trim().toLowerCase(), password, courseId, cardNumber };
}

module.exports = { validateCheckout };
