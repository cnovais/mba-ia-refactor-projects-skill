"""Configuração central da aplicação.

Todo valor sensível ou dependente de ambiente é lido de variáveis de
ambiente aqui — nenhum outro módulo deve ler `os.environ` diretamente.
Veja `.env.example` para a lista de variáveis suportadas.
"""

import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _get_secret_key():
    value = os.environ.get("SECRET_KEY")
    if value:
        return value
    # Sem SECRET_KEY definida: gera uma chave aleatória válida apenas para
    # esta execução (nunca hardcoded no código-fonte) e avisa no log.
    # Em produção, SECRET_KEY deve sempre ser definida explicitamente para
    # que sessões/cookies assinados sobrevivam a um restart do processo.
    generated = secrets.token_hex(32)
    logger.warning(
        "SECRET_KEY não definida via variável de ambiente; usando valor "
        "gerado aleatoriamente válido apenas para esta execução. "
        "Defina SECRET_KEY em produção."
    )
    return generated


def _get_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


SECRET_KEY = _get_secret_key()
ENVIRONMENT = os.environ.get("FLASK_ENV", "development")
DEBUG = _get_bool("FLASK_DEBUG", default=False)
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

# Token exigido no header `X-Admin-Token` para acessar endpoints
# administrativos perigosos (ex: /admin/reset-db). Sem essa variável
# definida, esses endpoints ficam desabilitados por padrão (fail-safe).
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
