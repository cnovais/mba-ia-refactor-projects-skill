"""Persistência e invariantes do domínio Produto.

A conexão de banco é sempre recebida por parâmetro (injeção de dependência)
em vez de importada de um módulo global — quem chama decide qual conexão
usar, o que também torna essas funções testáveis com um dublê de banco.
Toda query é parametrizada; nenhuma monta SQL por concatenação de string.
"""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


def _serialize(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_todos_produtos(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_serialize(row) for row in cursor.fetchall()]


def get_produto_por_id(db, id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _serialize(row) if row else None


def criar_produto(db, nome, descricao, preco, estoque, categoria):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(db, id, nome, descricao, preco, estoque, categoria):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    db.commit()
    return True


def deletar_produto(db, id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    return True


def buscar_produtos(db, termo, categoria=None, preco_min=None, preco_max=None):
    cursor = db.cursor()
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []

    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor.execute(query, params)
    return [_serialize(row) for row in cursor.fetchall()]
