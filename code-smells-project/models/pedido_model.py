"""Persistência e invariantes do domínio Pedido (inclui itens_pedido).

Itens de pedido não têm ciclo de vida próprio fora de um pedido — são
mantidos junto do model de pedido como parte do mesmo agregado, em vez de
um model isolado, conforme o relatório de auditoria (models/pedido_model.py
concentra pedidos + itens_pedido).
"""

DISCOUNT_TIER_HIGH_THRESHOLD = 10000
DISCOUNT_TIER_HIGH_RATE = 0.10
DISCOUNT_TIER_MID_THRESHOLD = 5000
DISCOUNT_TIER_MID_RATE = 0.05
DISCOUNT_TIER_LOW_THRESHOLD = 1000
DISCOUNT_TIER_LOW_RATE = 0.02


def criar_pedido(db, usuario_id, itens):
    cursor = db.cursor()
    total = 0
    produtos_por_id = {}

    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        produtos_por_id[item["produto_id"]] = produto
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        produto = produtos_por_id[item["produto_id"]]
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def _montar_pedidos(db, where_clause=None, params=()):
    cursor = db.cursor()
    query = "SELECT * FROM pedidos"
    if where_clause:
        query += " WHERE " + where_clause
    cursor.execute(query, params)
    pedidos_rows = cursor.fetchall()
    if not pedidos_rows:
        return []

    # Busca todos os itens (com nome de produto via JOIN) de uma vez só,
    # em vez de um cursor por pedido e outro por item (N+1) como antes.
    pedido_ids = [row["id"] for row in pedidos_rows]
    placeholders = ",".join("?" for _ in pedido_ids)
    cursor.execute(
        f"""
        SELECT itens_pedido.pedido_id AS pedido_id,
               itens_pedido.produto_id AS produto_id,
               itens_pedido.quantidade AS quantidade,
               itens_pedido.preco_unitario AS preco_unitario,
               produtos.nome AS produto_nome
        FROM itens_pedido
        LEFT JOIN produtos ON produtos.id = itens_pedido.produto_id
        WHERE itens_pedido.pedido_id IN ({placeholders})
        """,
        pedido_ids,
    )
    itens_por_pedido = {}
    for item in cursor.fetchall():
        itens_por_pedido.setdefault(item["pedido_id"], []).append(
            {
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] else "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            }
        )

    pedidos = []
    for row in pedidos_rows:
        pedidos.append(
            {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": itens_por_pedido.get(row["id"], []),
            }
        )
    return pedidos


def get_pedidos_usuario(db, usuario_id):
    return _montar_pedidos(db, "usuario_id = ?", (usuario_id,))


def get_todos_pedidos(db):
    return _montar_pedidos(db)


def atualizar_status_pedido(db, pedido_id, novo_status):
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def relatorio_vendas(db):
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0]
    if faturamento is None:
        faturamento = 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = 0
    if faturamento > DISCOUNT_TIER_HIGH_THRESHOLD:
        desconto = faturamento * DISCOUNT_TIER_HIGH_RATE
    elif faturamento > DISCOUNT_TIER_MID_THRESHOLD:
        desconto = faturamento * DISCOUNT_TIER_MID_RATE
    elif faturamento > DISCOUNT_TIER_LOW_THRESHOLD:
        desconto = faturamento * DISCOUNT_TIER_LOW_RATE

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
