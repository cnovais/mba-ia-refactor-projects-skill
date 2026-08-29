"""Abstração de notificações, extraída do controller de pedidos.

Antes, `criar_pedido`/`atualizar_status_pedido` em controllers.py disparavam
`print("ENVIANDO EMAIL...")` etc. diretamente inline. Isolar isso aqui
permite trocar por um serviço real de e-mail/SMS/push sem tocar no
controller, e permite testar o fluxo de pedido sem side effects de I/O.
"""

import logging

logger = logging.getLogger(__name__)


def notify_new_order(usuario_id, pedido_id):
    logger.info(f"ENVIANDO EMAIL: Pedido {pedido_id} criado para usuario {usuario_id}")
    logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
    logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")


def notify_status_change(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info(f"NOTIFICAÇÃO: Pedido {pedido_id} foi aprovado! Preparar envio.")
    if novo_status == "cancelado":
        logger.info(f"NOTIFICAÇÃO: Pedido {pedido_id} cancelado. Devolver estoque.")
