function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim() !== '';
}

// Aceita número inteiro ou string numérica (ex.: parâmetro de rota); retorna null se inválido.
function parsePositiveInt(value) {
    const number = isNonEmptyString(value) && /^\d+$/.test(value.trim()) ? Number(value) : value;
    return Number.isInteger(number) && number > 0 ? number : null;
}

module.exports = { isNonEmptyString, parsePositiveInt };
