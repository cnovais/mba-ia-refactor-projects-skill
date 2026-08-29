"""Single source of truth for task-payload validation, reused by both create and
update so the rules can't drift between the two (they used to be copy-pasted)."""
from utils.helpers import (
    DEFAULT_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
    parse_date,
    sanitize_string,
)


def validate_task_payload(data, partial=False):
    """Validates a task create/update payload.

    `partial=False` (create) requires title/status/priority/user_id/category_id to be
    present (defaulting the optional ones), matching the original create_task
    contract. `partial=True` (update) only validates whatever key is present in
    `data`, leaving the rest untouched — matching the original update_task contract.

    Returns (cleaned_data, error_message); error_message is None on success.
    """
    cleaned = {}

    if 'title' in data:
        title = sanitize_string(data.get('title'))
        if not title:
            return None, 'Título não pode ser vazio' if partial else 'Título é obrigatório'
        if len(title) < MIN_TITLE_LENGTH:
            return None, 'Título muito curto'
        if len(title) > MAX_TITLE_LENGTH:
            return None, 'Título muito longo'
        cleaned['title'] = title
    elif not partial:
        return None, 'Título é obrigatório'

    if 'description' in data:
        cleaned['description'] = data['description']
    elif not partial:
        cleaned['description'] = ''

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return None, 'Status inválido'
        cleaned['status'] = data['status']
    elif not partial:
        cleaned['status'] = 'pending'

    if 'priority' in data:
        try:
            priority = int(data['priority'])
        except (TypeError, ValueError):
            return None, 'Prioridade inválida'
        if priority < 1 or priority > 5:
            return None, 'Prioridade deve ser entre 1 e 5'
        cleaned['priority'] = priority
    elif not partial:
        cleaned['priority'] = DEFAULT_PRIORITY

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if not parsed:
                return None, 'Formato de data inválido. Use YYYY-MM-DD'
            cleaned['due_date'] = parsed
        else:
            cleaned['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        cleaned['tags'] = ','.join(tags) if isinstance(tags, list) else tags

    if partial:
        if 'user_id' in data:
            cleaned['user_id'] = data['user_id']
        if 'category_id' in data:
            cleaned['category_id'] = data['category_id']
    else:
        cleaned['user_id'] = data.get('user_id')
        cleaned['category_id'] = data.get('category_id')

    return cleaned, None
