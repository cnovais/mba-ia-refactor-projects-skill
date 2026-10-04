from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

from errors import UnauthorizedError
from validators.common import is_int

_TOKEN_SALT = 'auth-token'


def _serializer():
    secret_key = current_app.config.get('SECRET_KEY')
    if not secret_key:
        # Fail closed: without a signing key no token can be issued or accepted.
        raise UnauthorizedError('Autenticação indisponível')
    return URLSafeTimedSerializer(secret_key, salt=_TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({'uid': user.id})


def verify_token(token):
    """Returns the user id carried by a valid, unexpired token, or None."""
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except BadSignature:  # also covers SignatureExpired
        return None
    user_id = payload.get('uid') if isinstance(payload, dict) else None
    return user_id if is_int(user_id) else None
