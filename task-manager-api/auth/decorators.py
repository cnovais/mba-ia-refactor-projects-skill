"""Route-level authorization: verifies the bearer token issued by `POST /login` and
gates mutating endpoints behind it.

This is the enforcement half of the fix for the audit's CRITICAL finding "No
Authentication/Authorization on Any Mutating Endpoint" — issuing a real signed token
(`auth/tokens.py`) does nothing on its own unless something actually checks it, so
every route that creates/updates/deletes data is decorated with `login_required`
(and the handful the audit calls out as especially destructive/privileged with
`admin_required`, which additionally requires `User.is_admin()`).

Endpoints that were never meant to require a session — `POST /users` (registration)
and `POST /login` itself — are intentionally left undecorated; everything else that
mutates state now requires a valid token. This is a deliberate, expected behavior
change versus the pre-refactor code (every mutating route used to be wide open) and
not a break of the "preserve external behavior" contract: a well-formed authenticated
request still gets the exact same status/response shape as before.
"""
from functools import wraps

from flask import g, request

from auth.tokens import verify_token
from config import settings
from database import db
from errors import ApiError
from models.user import User


def _authenticate():
    header = request.headers.get('Authorization', '')
    token = header[len('Bearer '):].strip() if header.startswith('Bearer ') else None
    if not token:
        raise ApiError('Autenticação necessária', 401)

    user_id = verify_token(token, max_age=settings.TOKEN_MAX_AGE_SECONDS)
    if user_id is None:
        raise ApiError('Token inválido ou expirado', 401)

    user = db.session.get(User, user_id)
    if not user or not user.active:
        raise ApiError('Usuário inválido ou inativo', 401)

    return user


def login_required(fn):
    """Require a valid, non-expired bearer token. Exposes the caller as
    `flask.g.current_user` for handlers/controllers that need identity."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user = _authenticate()
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Require a valid token AND `User.is_admin()` — for the actions the audit
    singles out as needing to be admin-only (deleting a user, which cascades and
    deletes all of their tasks; promoting/demoting a role)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _authenticate()
        if not user.is_admin():
            raise ApiError('Acesso restrito a administradores', 403)
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper
