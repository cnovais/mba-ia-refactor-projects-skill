'use strict';

const { Router } = require('express');
const { adminAuth } = require('../middlewares/adminAuth');

function userRoutes(userController) {
    const router = Router();
    router.delete('/users/:id', adminAuth, userController.remove);
    return router;
}

module.exports = { userRoutes };
