'use strict';

const { asyncHandler } = require('../utils/asyncHandler');
const { hashPassword, verifyPassword } = require('../services/passwordService');
const paymentGateway = require('../services/paymentGatewayService');

const DEFAULT_NEW_USER_PASSWORD = '123456';
const EMAIL_FORMAT = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_NUMBER_FORMAT = /^\d{12,19}$/;

/**
 * Orchestrates the checkout use case end to end: validate input, verify or
 * create the user, charge the card, record the enrollment/payment/audit
 * log, and shape the response. Talks only to models and services — no raw
 * SQL and no route-path knowledge live here.
 */
function makeCheckoutController({ userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, cache }) {
    return {
        checkout: asyncHandler(async (req, res) => {
            const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

            if (!username || !email || !courseId || !cardNumber) {
                return res.status(400).send('Bad Request');
            }

            // Format validation (previously only presence was checked, so a
            // malformed email/card reached business logic unchecked).
            if (!EMAIL_FORMAT.test(email) || !CARD_NUMBER_FORMAT.test(String(cardNumber))) {
                return res.status(400).send('Bad Request');
            }

            const course = await courseModel.findActiveById(courseId);
            if (!course) {
                return res.status(404).send('Curso não encontrado');
            }

            let user = await userModel.findByEmail(email);

            if (user) {
                // Fixes a broken-authentication bug from the legacy code:
                // an existing user's password was never checked before
                // enrolling/charging their account.
                const passwordMatches = await verifyPassword(password || '', user.pass);
                if (!passwordMatches) {
                    return res.status(401).send('Senha inválida');
                }
            } else {
                const passwordHash = await hashPassword(password || DEFAULT_NEW_USER_PASSWORD);
                user = await userModel.create({ name: username, email, passwordHash });
            }

            const { status } = paymentGateway.charge(cardNumber, course.price);
            if (status === paymentGateway.PAYMENT_STATUS.DENIED) {
                return res.status(400).send('Pagamento recusado');
            }

            const enrollment = await enrollmentModel.create({ userId: user.id, courseId: course.id });
            await paymentModel.create({ enrollmentId: enrollment.id, amount: course.price, status });
            await auditLogModel.create(`Checkout curso ${course.id} por ${user.id}`);

            cache.set(`last_checkout_${user.id}`, course.title);

            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollment.id });
        }),
    };
}

module.exports = { makeCheckoutController };
