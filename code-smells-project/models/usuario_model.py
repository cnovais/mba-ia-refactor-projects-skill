"""Persistência e invariantes do domínio Usuário.

Senhas nunca são armazenadas nem comparadas em texto puro: usamos hashing
salgado (werkzeug.security) tanto na criação quanto no login.
"""

from werkzeug.security import check_password_hash, generate_password_hash


def _serialize(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": row["senha"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos_usuarios(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_serialize(row) for row in cursor.fetchall()]


def get_usuario_por_id(db, id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _serialize(row) if row else None


def criar_usuario(db, nome, email, senha, tipo="cliente"):
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def login_usuario(db, email, senha):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }
    return None
