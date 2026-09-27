const express = require('express');
const config = require('./config');
const createDb = require('./db/connection');
const Cache = require('./utils/cache');

const errorHandler = require('./middlewares/errorHandler');
const adminAuth = require('./middlewares/adminAuth');

const createUserModel = require('./models/userModel');
const createCourseModel = require('./models/courseModel');
const createEnrollmentModel = require('./models/enrollmentModel');
const createPaymentModel = require('./models/paymentModel');
const createAuditLogModel = require('./models/auditLogModel');
const createReportModel = require('./models/reportModel');

const createCheckoutController = require('./controllers/checkoutController');
const createFinancialReportController = require('./controllers/financialReportController');
const createUserController = require('./controllers/userController');

const checkoutRoutes = require('./routes/checkoutRoutes');
const financialReportRoutes = require('./routes/financialReportRoutes');
const userRoutes = require('./routes/userRoutes');

async function main() {
    const db = createDb(config.dbPath);
    await db.initDb();

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);
    const reportModel = createReportModel(db);
    const cache = new Cache();

    const checkout = createCheckoutController({ courseModel, userModel, enrollmentModel, paymentModel, auditLogModel, cache });
    const getFinancialReport = createFinancialReportController({ reportModel });
    const userController = createUserController({ userModel, enrollmentModel, paymentModel });

    const app = express();
    app.use(express.json());

    app.use('/api', checkoutRoutes(checkout));
    app.use('/api', userRoutes(userController, adminAuth(config)));
    app.use('/api/admin', adminAuth(config), financialReportRoutes(getFinancialReport));

    app.use(errorHandler);

    app.listen(config.port, () => {
        console.log(`ecommerce-api-legacy rodando na porta ${config.port}...`);
    });

    return app;
}

main().catch((err) => {
    console.error('Falha ao iniciar aplicação', err);
    process.exit(1);
});
