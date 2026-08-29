from utils.helpers import DEFAULT_COLOR, is_valid_color


def validate_category_payload(data, partial=False):
    """Returns (cleaned_data, error_message); error_message is None on success."""
    cleaned = {}

    if 'name' in data:
        name = data['name']
        if not name:
            return None, 'Nome é obrigatório'
        cleaned['name'] = name
    elif not partial:
        return None, 'Nome é obrigatório'

    if 'description' in data:
        cleaned['description'] = data['description']
    elif not partial:
        cleaned['description'] = ''

    if 'color' in data:
        color = data['color']
        if color and not is_valid_color(color):
            return None, 'Cor inválida. Use o formato hexadecimal, ex: #3498db'
        cleaned['color'] = color or DEFAULT_COLOR
    elif not partial:
        cleaned['color'] = DEFAULT_COLOR

    return cleaned, None
