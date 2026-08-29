"""Fluxo de aplicação (use cases) do domínio Produto.

Cada função orquestra: validar entrada -> chamar o model -> decidir a
resposta. Nenhum SQL/acesso a dado direto aqui — isso é responsabilidade do
model. Sem try/except genérico: exceções não previstas sobem para o error
handler central (middlewares/error_handler.py).
"""

import logging

from flask import jsonify, request

from db.connection import get_db
from models import produto_model
from validators.produto_validator import validar_produto

logger = logging.getLogger(__name__)


def listar_produtos():
    db = get_db()
    produtos = produto_model.get_todos_produtos(db)
    logger.info(f"Listando {len(produtos)} produtos")
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    db = get_db()
    produto = produto_model.get_produto_por_id(db, id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    dados = request.get_json()

    erro = validar_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    db = get_db()
    id = produto_model.criar_produto(
        db,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    logger.info(f"Produto criado com ID: {id}")
    return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = request.get_json()
    db = get_db()

    produto_existente = produto_model.get_produto_por_id(db, id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    erro = validar_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.atualizar_produto(
        db,
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    db = get_db()
    produto = produto_model.get_produto_por_id(db, id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_model.deletar_produto(db, id)
    logger.info(f"Produto {id} deletado")
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    db = get_db()
    resultados = produto_model.buscar_produtos(db, termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
