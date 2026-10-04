const express = require('express');
const { loadConfig } = require('./config');
const { openDatabase } = require('./db/connection');
const { initSchema } = require('./db/schema');
const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { AuditLogModel } = require('./models/auditLogModel');
const { ReportModel } = require('./models/reportModel');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createFinancialReportController } = require('./controllers/financialReportController');
const { createUserController } = require('./controllers/userController');
const { checkoutRoutes } = require('./routes/checkoutRoutes');
const { financialReportRoutes } = require('./routes/financialReportRoutes');
const { userRoutes } = require('./routes/userRoutes');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { errorHandler } = require('./middlewares/errorHandler');
const { PaymentGateway } = require('./utils/paymentGateway');
const { BoundedCache } = require('./utils/cache');

async function main() {
    const config = loadConfig();

    const db = await openDatabase(config.dbPath);
    await initSchema(db);

    const runInTransaction = (work) => db.transaction(work);
    const userModel = new UserModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);

    const checkoutController = createCheckoutController({
        runInTransaction,
        userModel,
        courseModel: new CourseModel(db),
        enrollmentModel,
        paymentModel,
        auditLogModel: new AuditLogModel(db),
        paymentGateway: new PaymentGateway(config.paymentGatewayKey),
        cache: new BoundedCache(),
    });
    const financialReportController = createFinancialReportController({ reportModel: new ReportModel(db) });
    const userController = createUserController({ runInTransaction, userModel, enrollmentModel, paymentModel });

    if (!config.adminToken) {
        console.warn('[config] ADMIN_TOKEN não definido — rotas administrativas bloqueadas (403).');
    }
    const adminAuth = createAdminAuth(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes(checkoutController));
    app.use(financialReportRoutes(financialReportController, adminAuth));
    app.use(userRoutes(userController, adminAuth));
    app.use(errorHandler);

    app.listen(config.port, () => {
        console.log(`LMS API rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    console.error(`[startup] Falha ao iniciar a aplicação: ${err.message}`);
    process.exit(1);
});
