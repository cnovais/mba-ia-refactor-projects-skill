"""Composition root: build the app, wire config/db/blueprints/error handling, run.
Deliberately thin — anything that looks like real work belongs in a lower layer."""
from datetime import datetime, timezone

from flask import Flask
from flask_cors import CORS

from config import settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)

    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
