const { validateCheckout } = require('../validators/checkoutValidator');
const { hashPassword, verifyPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../utils/paymentGateway');
const { HttpError } = require('../utils/httpError');

function createCheckoutController({ runInTransaction, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, cache }) {
    async function checkout(req, res) {
        const { name, email, password, courseId, cardNumber } = validateCheckout(req.body);

        const course = await courseModel.findActiveById(courseId);
        if (!course) throw new HttpError(404, 'Curso não encontrado');

        const { userId, enrollmentId } = await runInTransaction(async () => {
            const existingUser = await userModel.findByEmailWithPassword(email);
            // Conta existente: a senha é verificada antes de qualquer efeito colateral.
            if (existingUser && !(await verifyPassword(password, existingUser.passwordHash))) {
                throw new HttpError(401, 'Credenciais inválidas');
            }

            const status = paymentGateway.charge(cardNumber, course.price);
            if (status !== PAYMENT_STATUS.PAID) throw new HttpError(400, 'Pagamento recusado');

            const buyerId = existingUser
                ? existingUser.id
                : await userModel.create({ name, email, passwordHash: await hashPassword(password) });
            const newEnrollmentId = await enrollmentModel.create({ userId: buyerId, courseId: course.id });
            await paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
            await auditLogModel.record(`Checkout curso ${course.id} por ${buyerId}`);
            return { userId: buyerId, enrollmentId: newEnrollmentId };
        });

        cache.set(`last_checkout_${userId}`, course.title);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }

    return { checkout };
}

module.exports = { createCheckoutController };
