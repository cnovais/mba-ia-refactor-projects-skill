"""Endpoints de sistema: índice e health check.

`health_check` nunca mais devolve `secret_key`/segredo algum no corpo da
resposta (era um CRITICAL no relatório de auditoria) e reporta o estado real
de `debug`/`ambiente` a partir do módulo de config, em vez de valores
hardcoded.
"""

import logging

from flask import jsonify

from config import settings
from db.connection import get_db

logger = logging.getLogger(__name__)


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return (
            jsonify(
                {
                    "status": "ok",
                    "database": "connected",
                    "counts": {
                        "produtos": produtos,
                        "usuarios": usuarios,
                        "pedidos": pedidos,
                    },
                    "versao": "1.0.0",
                    "ambiente": settings.ENVIRONMENT,
                    "db_path": settings.DATABASE_PATH,
                    "debug": settings.DEBUG,
                }
            ),
            200,
        )
    except Exception as e:
        logger.exception("Falha no health check")
        return jsonify({"status": "erro", "detalhes": str(e)}), 500
