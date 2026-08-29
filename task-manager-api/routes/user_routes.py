"""Routing only: parse the request, delegate to the controller, return what it gave
back. No business logic, no direct DB access — see controllers/user_controller.py."""
from flask import Blueprint, g, jsonify, request

from auth.decorators import admin_required, login_required
from controllers import user_controller

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(user_controller.get_user(user_id)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    # Intentionally public — this is the sign-up endpoint; there is no session yet
    # to require a token from.
    return jsonify(user_controller.create_user(request.get_json())), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    result = user_controller.update_user(user_id, request.get_json(), acting_user=g.current_user)
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    # Admin-only: deleting a user cascades to delete all of their tasks too.
    user_controller.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(user_controller.get_user_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    return jsonify(user_controller.login(request.get_json())), 200
