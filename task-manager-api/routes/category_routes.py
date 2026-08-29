"""Routing only for the category resource — split out of report_routes.py, where it
used to live purely because both were registered in the same blueprint file, with no
actual relationship to reporting. Same URL paths as before."""
from flask import Blueprint, jsonify, request

from auth.decorators import login_required
from controllers import category_controller

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    category = category_controller.create_category(request.get_json())
    return jsonify(category), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    category = category_controller.update_category(cat_id, request.get_json())
    return jsonify(category), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    category_controller.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
