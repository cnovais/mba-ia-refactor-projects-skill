"""Centralized error handling: one place that turns any exception raised by a
controller into a consistent JSON response, instead of every route repeating its own
try/except/print. See errors.ApiError for the "expected failure" case."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import ApiError

logger = logging.getLogger("task_manager")


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.exception("Erro interno não tratado")
        return jsonify({'error': 'Erro interno'}), 500
