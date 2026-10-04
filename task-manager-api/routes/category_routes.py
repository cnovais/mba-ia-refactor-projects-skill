from flask import Blueprint, jsonify, request

from auth.decorators import require_admin, require_auth
from controllers import category_controller

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
@require_admin
def create_category():
    return jsonify(category_controller.create_category(request.get_json(silent=True))), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require_admin
def update_category(cat_id):
    return jsonify(category_controller.update_category(cat_id, request.get_json(silent=True))), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_admin
def delete_category(cat_id):
    return jsonify(category_controller.delete_category(cat_id)), 200
