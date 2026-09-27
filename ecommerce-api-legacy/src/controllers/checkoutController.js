const { hashPassword } = require('../utils/password');
const { charge } = require('../utils/paymentGateway');

module.exports = function checkoutController({ courseModel, userModel, enrollmentModel, paymentModel, auditLogModel, cache }) {
    return async function checkout(req, res) {
        const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

        if (!username || !email || !password || !courseId || !cardNumber) {
            return res.status(400).json({ error: 'Bad Request' });
        }

        const course = await courseModel.findActiveById(courseId);
        if (!course) return res.status(404).json({ error: 'Curso não encontrado' });

        let user = await userModel.findByEmail(email);
        if (!user) {
            const passwordHash = await hashPassword(password);
            const { lastID } = await userModel.create({ name: username, email, passwordHash });
            user = { id: lastID };
        }

        const paymentStatus = charge(cardNumber);
        if (paymentStatus === 'DENIED') {
            return res.status(400).json({ error: 'Pagamento recusado' });
        }

        const { lastID: enrollmentId } = await enrollmentModel.create(user.id, courseId);
        await paymentModel.create(enrollmentId, course.price, paymentStatus);
        await auditLogModel.create(`Checkout curso ${courseId} por ${user.id}`);

        cache.set(`last_checkout_${user.id}`, course.title);

        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    };
};
