module.exports = function userController({ userModel, enrollmentModel, paymentModel }) {
    return {
        async deleteUser(req, res) {
            const id = Number(req.params.id);
            if (!Number.isInteger(id) || id <= 0) {
                return res.status(400).json({ error: 'id inválido' });
            }

            // Cascade the delete instead of leaving orphaned enrollments/payments behind.
            const enrollments = await enrollmentModel.findByUserId(id);
            const enrollmentIds = enrollments.map((enrollment) => enrollment.id);
            await paymentModel.deleteByEnrollmentIds(enrollmentIds);
            await enrollmentModel.deleteByUserId(id);
            const { changes } = await userModel.deleteById(id);

            if (changes === 0) return res.status(404).json({ error: 'Usuário não encontrado' });

            res.json({ message: 'Usuário e dados relacionados removidos com sucesso' });
        },
    };
};
