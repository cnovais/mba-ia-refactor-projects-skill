'use strict';

const PAYMENT_STATUS = { PAID: 'PAID', DENIED: 'DENIED' };
const VISA_CARD_PREFIX = '4';

/**
 * Stand-in for a real payment gateway integration. Approves Visa-prefixed
 * card numbers, matching the original demo rule, but isolated from the
 * checkout flow so a real gateway client can replace it later without
 * touching the controller. Never logs the gateway credential itself
 * (the legacy code printed it on every request — see audit finding on
 * hardcoded secrets).
 */
function charge(cardNumber, amount) {
    const approved = cardNumber.startsWith(VISA_CARD_PREFIX);
    console.log(`Processando pagamento de ${amount} via gateway (aprovado: ${approved}).`);
    return { status: approved ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED };
}

module.exports = { charge, PAYMENT_STATUS };
