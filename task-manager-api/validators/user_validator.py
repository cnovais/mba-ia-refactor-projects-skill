"""Single source of truth for user-payload validation, reused by create and update."""
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, sanitize_string, validate_email


def validate_user_payload(data, partial=False):
    """Returns (cleaned_data, error_message); error_message is None on success."""
    cleaned = {}

    if 'name' in data:
        name = sanitize_string(data.get('name'))
        if not name:
            return None, 'Nome é obrigatório'
        cleaned['name'] = name
    elif not partial:
        return None, 'Nome é obrigatório'

    if 'email' in data:
        email = data['email']
        if not email:
            return None, 'Email é obrigatório'
        if not validate_email(email):
            return None, 'Email inválido'
        cleaned['email'] = email
    elif not partial:
        return None, 'Email é obrigatório'

    if 'password' in data:
        password = data['password']
        if not partial and not password:
            return None, 'Senha é obrigatória'
        if len(password or '') < MIN_PASSWORD_LENGTH:
            return None, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'
        cleaned['password'] = password
    elif not partial:
        return None, 'Senha é obrigatória'

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return None, 'Role inválido'
        cleaned['role'] = data['role']
    elif not partial:
        cleaned['role'] = 'user'

    if 'active' in data:
        cleaned['active'] = data['active']

    return cleaned, None
