const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function userRoutes(userController, adminAuth) {
    const router = express.Router();
    router.delete('/api/users/:id', adminAuth, asyncHandler(userController.deleteUser));
    return router;
}

module.exports = { userRoutes };
