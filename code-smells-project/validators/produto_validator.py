"""Validação de produto compartilhada entre criação e atualização.

Antes, `criar_produto` e `atualizar_produto` em controllers.py repetiam
quase o mesmo bloco de validações (e a versão de atualização estava
incompleta, sem checar tamanho de nome nem categoria). Esta função única é
reusada pelos dois fluxos para que a regra de validação nunca divirja entre
criar e atualizar.
"""

from models.produto_model import CATEGORIAS_VALIDAS


def validar_produto(dados):
    """Retorna a primeira mensagem de erro encontrada, ou None se válido."""
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return "Preço não pode ser negativo"
    if estoque < 0:
        return "Estoque não pode ser negativo"
    if len(nome) < 2:
        return "Nome muito curto"
    if len(nome) > 200:
        return "Nome muito longo"
    if categoria not in CATEGORIAS_VALIDAS:
        return "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)

    return None
