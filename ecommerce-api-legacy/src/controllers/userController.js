const { parsePositiveInt } = require('../validators/common');
const { HttpError } = require('../utils/httpError');

function createUserController({ runInTransaction, userModel, enrollmentModel, paymentModel }) {
    async function deleteUser(req, res) {
        const userId = parsePositiveInt(req.params.id);
        if (userId === null) throw new HttpError(400, 'Bad Request: id inválido');

        // Remove pagamentos e matrículas junto com o usuário, sem deixar órfãos.
        const deleted = await runInTransaction(async () => {
            if (!(await userModel.findById(userId))) return false;
            await paymentModel.deleteByUserId(userId);
            await enrollmentModel.deleteByUserId(userId);
            return userModel.deleteById(userId);
        });

        if (!deleted) throw new HttpError(404, 'Usuário não encontrado');
        res.send('Usuário deletado, junto com suas matrículas e pagamentos.');
    }

    return { deleteUser };
}

module.exports = { createUserController };
