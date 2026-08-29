"""Routing only: parse the request, delegate to the controller, return what it gave
back. No business logic, no direct DB access — see controllers/task_controller.py."""
from flask import Blueprint, jsonify, request

from auth.decorators import login_required
from controllers import task_controller

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    result = task_controller.search_tasks(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.get_stats()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    task = task_controller.create_task(request.get_json())
    return jsonify(task), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = task_controller.update_task(task_id, request.get_json())
    return jsonify(task), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200
