from datetime import datetime

from flask import Blueprint

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now())}


@health_bp.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
