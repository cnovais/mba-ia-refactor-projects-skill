from errors import ValidationError


def require_body(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def optional_id(value, field):
    if not value:
        return None
    if not is_int(value):
        raise ValidationError(f'{field} inválido')
    return value


def optional_int_param(args, name):
    raw = args.get(name, '')
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')
