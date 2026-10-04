// Gateway de pagamento simulado: cartões que começam com o prefixo abaixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

function maskCard(cardNumber) {
    return `****${cardNumber.slice(-4)}`;
}

class PaymentGateway {
    constructor(apiKey) {
        this.apiKey = apiKey;
    }

    charge(cardNumber, amount) {
        // Nunca loga a chave nem o número completo do cartão.
        console.log(`[payment] Processando cartão ${maskCard(cardNumber)} no valor de ${amount}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = { PaymentGateway, PAYMENT_STATUS };
