import logging
import sys

from flask import Flask
from flask_cors import CORS

from config import ConfigError, load_settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService


def create_app(settings=None):
    settings = settings or load_settings()

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
        TOKEN_MAX_AGE_SECONDS=settings.token_max_age_seconds,
    )

    if settings.cors_origins:
        CORS(app, origins=list(settings.cors_origins))

    db.init_app(app)
    app.extensions['notification_service'] = NotificationService(
        settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password
    )

    register_error_handlers(app)
    for blueprint in (health_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    try:
        settings = load_settings()
    except ConfigError as err:
        sys.exit(f'Configuration error: {err}')
    create_app(settings).run(debug=settings.debug, host=settings.host, port=settings.port)
