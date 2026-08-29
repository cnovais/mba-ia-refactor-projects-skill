"""Rotas de sistema: índice, health check, relatório de vendas e admin."""

from flask import Blueprint

from controllers import admin_controller, pedido_controller, sistema_controller

sistema_bp = Blueprint("sistema", __name__)

sistema_bp.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
sistema_bp.add_url_rule("/health", "health_check", sistema_controller.health_check, methods=["GET"])
sistema_bp.add_url_rule(
    "/relatorios/vendas", "relatorio_vendas", pedido_controller.relatorio_vendas, methods=["GET"]
)
sistema_bp.add_url_rule(
    "/admin/reset-db", "reset_database", admin_controller.reset_database, methods=["POST"]
)
