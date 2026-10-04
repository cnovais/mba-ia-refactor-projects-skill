from flask import Blueprint, jsonify

from auth.decorators import require_auth
from controllers import report_controller

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
@require_auth
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@require_auth
def user_report(user_id):
    return jsonify(report_controller.user_report(user_id)), 200
