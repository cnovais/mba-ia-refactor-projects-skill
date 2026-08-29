"""Composition root / entry point da API da Loja.

Cria a app Flask, aplica config, inicializa o banco, registra o error
handler central e monta as rotas — nada de SQL, validação ou lógica de
negócio deve viver aqui.
"""

import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from db.connection import init_app as init_db
from middlewares.error_handler import register_error_handlers
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.sistema_routes import sistema_bp
from routes.usuario_routes import usuario_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["DATABASE_PATH"] = settings.DATABASE_PATH

    CORS(app)

    init_db(app)
    register_error_handlers(app)

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(sistema_bp)

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info(f"Rodando em http://{settings.HOST}:{settings.PORT}")
    logger.info("=" * 50)

    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
