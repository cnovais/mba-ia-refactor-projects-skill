from flask import Blueprint, g, jsonify, request

from auth.decorators import optional_auth, require_admin, require_auth
from controllers import user_controller

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@require_auth
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    return jsonify(user_controller.get_user(user_id)), 200


@user_bp.route('/users', methods=['POST'])
@optional_auth
def create_user():
    return jsonify(user_controller.create_user(request.get_json(silent=True), g.current_user)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    return jsonify(user_controller.update_user(user_id, request.get_json(silent=True), g.current_user)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    return jsonify(user_controller.delete_user(user_id)), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@require_auth
def get_user_tasks(user_id):
    return jsonify(user_controller.get_user_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    return jsonify(user_controller.login(request.get_json(silent=True))), 200
