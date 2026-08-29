"""Fluxo de aplicação (use cases) do domínio Usuário (inclui login)."""

import logging

from flask import jsonify, request

from db.connection import get_db
from models import usuario_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    db = get_db()
    usuarios = usuario_model.get_todos_usuarios(db)
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    db = get_db()
    usuario = usuario_model.get_usuario_por_id(db, id)
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado"}), 404


def criar_usuario():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    db = get_db()
    id = usuario_model.criar_usuario(db, nome, email, senha)
    logger.info(f"Usuário criado: {email}")
    return jsonify({"dados": {"id": id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    db = get_db()
    usuario = usuario_model.login_usuario(db, email, senha)
    if usuario:
        logger.info(f"Login bem-sucedido: {email}")
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    logger.info(f"Login falhou: {email}")
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
