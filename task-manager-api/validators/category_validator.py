import re

from errors import ValidationError
from models.category import DEFAULT_COLOR
from validators.common import require_body

COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def _validate_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')


def _validate_color(color):
    if not isinstance(color, str) or not COLOR_PATTERN.match(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')


def validate_category_create(data):
    require_body(data)
    _validate_name(data.get('name'))
    color = data.get('color', DEFAULT_COLOR)
    _validate_color(color)
    return {'name': data['name'], 'description': data.get('description', ''), 'color': color}


def validate_category_update(data):
    require_body(data)
    changes = {}
    if 'name' in data:
        _validate_name(data['name'])
        changes['name'] = data['name']
    if 'description' in data:
        changes['description'] = data['description']
    if 'color' in data:
        _validate_color(data['color'])
        changes['color'] = data['color']
    return changes
