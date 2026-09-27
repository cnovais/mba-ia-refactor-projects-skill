// Simulated gateway (no real processor integrated): cards starting with this
// prefix are treated as approved, everything else is declined.
const APPROVED_CARD_PREFIX = '4';

function charge(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? 'PAID' : 'DENIED';
}

module.exports = { charge };
