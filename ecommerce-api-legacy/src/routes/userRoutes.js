const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = function userRoutes(userController, adminAuthMiddleware) {
    const router = express.Router();
    router.delete('/users/:id', adminAuthMiddleware, asyncHandler(userController.deleteUser));
    return router;
};
