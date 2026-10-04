import re

from errors import ValidationError
from models.user import ROLE_USER, VALID_ROLES
from validators.common import require_body

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
MIN_PASSWORD_LENGTH = 4


def _validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError('Email inválido')


def _validate_password(password, error_message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(error_message)


def validate_role(role):
    if not isinstance(role, str) or role not in VALID_ROLES:
        raise ValidationError('Role inválido')


def validate_user_create(data):
    """Validates the fields of a new user; role is validated after the e-mail uniqueness check."""
    require_body(data)

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')

    _validate_email(email)
    _validate_password(password, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')

    return {'name': name, 'email': email, 'password': password, 'role': data.get('role', ROLE_USER)}


def validate_user_update(data):
    require_body(data)
    changes = {}

    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            raise ValidationError('Nome é obrigatório')
        changes['name'] = data['name']

    if 'email' in data:
        _validate_email(data['email'])
        changes['email'] = data['email']

    if 'password' in data:
        _validate_password(data['password'], 'Senha muito curta')
        changes['password'] = data['password']

    if 'role' in data:
        validate_role(data['role'])
        changes['role'] = data['role']

    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        changes['active'] = data['active']

    return changes


def validate_login(data):
    require_body(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')
    return email, password
