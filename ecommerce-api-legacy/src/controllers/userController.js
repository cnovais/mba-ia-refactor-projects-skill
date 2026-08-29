'use strict';

const { asyncHandler } = require('../utils/asyncHandler');

function makeUserController({ userModel }) {
    return {
        remove: asyncHandler(async (req, res) => {
            const { id } = req.params;
            const deleted = await userModel.deleteById(id);

            if (!deleted) {
                return res.status(404).send('Usuário não encontrado');
            }

            // Note: preserved from the legacy behavior — deleting a user
            // does not cascade to their enrollments/payments. Flagged in
            // the audit report; left as-is here to avoid changing the
            // response contract for a well-formed delete request.
            res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
        }),
    };
}

module.exports = { makeUserController };
