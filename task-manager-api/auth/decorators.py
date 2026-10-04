from functools import wraps

from flask import g, request

from auth.tokens import verify_token
from errors import ForbiddenError, UnauthorizedError
from models.user import User


def _authenticated_user(required):
    header = request.headers.get('Authorization', '')
    if not header:
        if required:
            raise UnauthorizedError('Token de autenticação ausente')
        return None

    scheme, _, token = header.partition(' ')
    token = token.strip()
    if scheme.lower() != 'bearer' or not token:
        raise UnauthorizedError('Token inválido ou expirado')

    user_id = verify_token(token)
    user = User.get_by_id(user_id) if user_id is not None else None
    if not user or not user.active:
        raise UnauthorizedError('Token inválido ou expirado')
    return user


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = _authenticated_user(required=True)
        return view(*args, **kwargs)
    return wrapper


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = _authenticated_user(required=True)
        if not user.is_admin():
            raise ForbiddenError('Acesso restrito a administradores')
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper


def optional_auth(view):
    """Identifies the caller when a token is sent; an invalid token is still rejected."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = _authenticated_user(required=False)
        return view(*args, **kwargs)
    return wrapper
