"""Signed, verifiable session tokens for the login flow.

This replaces the placeholder `'fake-jwt-token-' + str(user.id)` string the login
endpoint used to return (a value that looked like a token but was never actually
generated or checked anywhere). Issuance lives here; enforcement (checking the
token on every mutating route) lives in `auth/decorators.py`.
"""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_token(user_id):
    return _serializer().dumps({'user_id': user_id})


def verify_token(token, max_age=None):
    try:
        data = _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return data.get('user_id')
