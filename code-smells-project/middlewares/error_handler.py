"""Tratamento de erro centralizado.

Antes, cada uma das ~15 funções de controllers.py repetia seu próprio
`except Exception as e: return jsonify({"erro": str(e)}), 500`, vazando a
mensagem crua da exceção Python (nomes de tabela, tipo de erro do driver
SQL) para o cliente. Agora as rotas/controllers não precisam de try/except
para o caso genérico — exceções não tratadas sobem até aqui, são logadas
com stack trace e viram uma resposta 500 padronizada, sem detalhes internos.

Erros HTTP "esperados" (404 de rota inexistente, 400 de JSON malformado
etc.) continuam com o comportamento padrão do Flask/Werkzeug — não são
convertidos em 500.
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
