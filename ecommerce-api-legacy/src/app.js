'use strict';

const express = require('express');

const { config } = require('./config');
const { createDatabase } = require('./db/connection');
const { createSchema } = require('./db/schema');
const { seed } = require('./db/seed');

const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { AuditLogModel } = require('./models/auditLogModel');
const { FinancialReportModel } = require('./models/financialReportModel');

const { makeCheckoutController } = require('./controllers/checkoutController');
const { makeFinancialReportController } = require('./controllers/financialReportController');
const { makeUserController } = require('./controllers/userController');

const { buildApiRouter } = require('./routes');
const { notFoundHandler, errorHandler } = require('./middlewares/errorHandler');
const { MemoryCache } = require('./utils/cache');

// Composition root: wires config, DB, models, controllers and routes
// together. Kept short and declarative — no SQL, no business rules, no
// route-path validation logic lives here.
async function createApp() {
    const db = createDatabase(config.dbPath);
    await createSchema(db);
    await seed(db);

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);
    const financialReportModel = new FinancialReportModel(db);
    const cache = new MemoryCache();

    const checkoutController = makeCheckoutController({
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        cache,
    });
    const financialReportController = makeFinancialReportController({ financialReportModel });
    const userController = makeUserController({ userModel });

    const app = express();
    app.use(express.json());
    app.use(buildApiRouter({ checkoutController, financialReportController, userController }));
    app.use(notFoundHandler);
    app.use(errorHandler);

    return { app, db };
}

async function start() {
    const { app } = await createApp();
    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        console.error('Falha ao iniciar a aplicação:', err);
        process.exit(1);
    });
}

module.exports = { createApp };
