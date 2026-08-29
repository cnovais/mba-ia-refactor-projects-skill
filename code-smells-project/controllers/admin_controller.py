"""Endpoints administrativos perigosos.

`/admin/query` (executava SQL arbitrário vindo do corpo da requisição, sem
nenhuma autenticação) foi removido — não tem propósito de produto
legítimo, era um backdoor puro (playbook item 4).

`/admin/reset-db` foi mantido (apaga todas as tabelas), mas agora exige um
token de admin via header `X-Admin-Token`, comparado ao valor configurado em
`ADMIN_TOKEN`. Sem essa variável de ambiente definida, o endpoint fica
desabilitado por padrão (fail-safe) em vez de aberto por padrão.
"""

import logging

from flask import jsonify, request

from config import settings
from db.connection import get_db

logger = logging.getLogger(__name__)


def reset_database():
    token = request.headers.get("X-Admin-Token")
    if not settings.ADMIN_TOKEN or token != settings.ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    logger.warning("BANCO DE DADOS RESETADO")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
