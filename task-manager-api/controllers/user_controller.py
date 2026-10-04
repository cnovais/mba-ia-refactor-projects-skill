import logging

from auth.tokens import issue_token
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from models.task import Task
from models.user import ROLE_USER, User
from utils.helpers import utcnow
from validators.user_validator import validate_login, validate_role, validate_user_create, validate_user_update

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_available(email, current_user_id=None):
    existing = User.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def list_users():
    task_counts = Task.count_by_user()
    result = []
    for user in User.list_all():
        data = user.to_dict()
        data['task_count'] = task_counts.get(user.id, 0)
        result.append(data)
    return result


def get_user(user_id):
    user = _get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
    return data


def create_user(data, current_user):
    fields = validate_user_create(data)
    _ensure_email_available(fields['email'])
    validate_role(fields['role'])
    if fields['role'] != ROLE_USER and not (current_user and current_user.is_admin()):
        raise ForbiddenError('Apenas administradores podem atribuir este role')

    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    user.save()
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update_user(user_id, data, current_user):
    user = _get_user_or_404(user_id)
    if not current_user.is_admin() and current_user.id != user.id:
        raise ForbiddenError('Acesso negado')

    changes = validate_user_update(data)
    if ('role' in changes or 'active' in changes) and not current_user.is_admin():
        raise ForbiddenError('Apenas administradores podem alterar role ou status')
    if 'email' in changes:
        _ensure_email_available(changes['email'], current_user_id=user.id)

    password = changes.pop('password', None)
    if password is not None:
        user.set_password(password)
    for field, value in changes.items():
        setattr(user, field, value)
    user.save()
    return user.to_dict()


def delete_user(user_id):
    user = _get_user_or_404(user_id)
    Task.delete_by_user(user.id)
    user.delete()
    logger.info('Usuário deletado: %s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def get_user_tasks(user_id):
    _get_user_or_404(user_id)
    now = utcnow()
    return [task.to_user_task_dict(now) for task in Task.list_by_user(user_id)]


def login(data):
    email, password = validate_login(data)

    user = User.authenticate(email, password)
    if not user:
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user),
    }
