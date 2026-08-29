"""Fluxo de aplicação (use cases) do domínio Pedido.

Efeitos colaterais (notificações) são disparados através de
`services.notification_service` em vez de `print` inline no controller.
"""

from flask import jsonify, request

from db.connection import get_db
from models import pedido_model
from services import notification_service

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens or len(itens) == 0:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    db = get_db()
    resultado = pedido_model.criar_pedido(db, usuario_id, itens)

    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    notification_service.notify_new_order(usuario_id, resultado["pedido_id"])

    return jsonify(
        {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}
    ), 201


def listar_pedidos_usuario(usuario_id):
    db = get_db()
    pedidos = pedido_model.get_pedidos_usuario(db, usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    db = get_db()
    pedidos = pedido_model.get_todos_pedidos(db)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    db = get_db()
    pedido_model.atualizar_status_pedido(db, pedido_id, novo_status)
    notification_service.notify_status_change(pedido_id, novo_status)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    db = get_db()
    relatorio = pedido_model.relatorio_vendas(db)
    return jsonify({"dados": relatorio, "sucesso": True}), 200
