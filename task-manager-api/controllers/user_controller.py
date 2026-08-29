import database
from auth.tokens import generate_token
from database import db
from errors import ApiError
from models.task import Task
from models.user import User
from utils.helpers import format_date, log_action
from validators.user_validator import validate_user_payload


def list_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'active': user.active,
            'created_at': format_date(user.created_at),
            'task_count': len(user.tasks),
        })
    return result


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    if not data:
        raise ApiError('Dados inválidos')

    cleaned, error = validate_user_payload(data, partial=False)
    if error:
        raise ApiError(error)

    if User.query.filter_by(email=cleaned['email']).first():
        raise ApiError('Email já cadastrado', 409)

    user = User()
    user.name = cleaned['name']
    user.email = cleaned['email']
    user.set_password(cleaned['password'])
    user.role = cleaned['role']

    db.session.add(user)
    database.save()
    log_action('Usuário criado', f'{user.id} - {user.name}')
    return user.to_dict()


def update_user(user_id, data, acting_user=None):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    if not data:
        raise ApiError('Dados inválidos')

    is_admin_actor = bool(acting_user and acting_user.is_admin())
    is_self = bool(acting_user and acting_user.id == user_id)

    # Editing someone else's account (password, email, active flag, ...) is only
    # for admins; editing your own is always allowed. Without this, any
    # authenticated user could take over any other account via this endpoint —
    # `login_required` alone only proves *someone* is logged in, not that they're
    # allowed to touch *this* record.
    if not (is_admin_actor or is_self):
        raise ApiError('Você só pode editar o seu próprio usuário', 403)

    cleaned, error = validate_user_payload(data, partial=True)
    if error:
        raise ApiError(error)

    # Role is a privilege, not a regular profile field: only an admin may change it
    # (this is the concrete use of User.is_admin() the audit's CRITICAL finding
    # asked for — otherwise a user could promote themself to admin on their own
    # account, which the self-or-admin check above would otherwise allow).
    if 'role' in cleaned and not is_admin_actor:
        raise ApiError('Apenas administradores podem alterar o role', 403)

    if 'email' in cleaned:
        existing = User.query.filter_by(email=cleaned['email']).first()
        if existing and existing.id != user_id:
            raise ApiError('Email já cadastrado', 409)
        user.email = cleaned['email']

    if 'name' in cleaned:
        user.name = cleaned['name']
    if 'password' in cleaned:
        user.set_password(cleaned['password'])
    if 'role' in cleaned:
        user.role = cleaned['role']
    if 'active' in cleaned:
        user.active = cleaned['active']

    database.save()
    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    for task in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(task)

    db.session.delete(user)
    database.save()
    log_action('Usuário deletado', str(user_id))


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    tasks = Task.query.filter_by(user_id=user_id).all()
    return [
        {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'created_at': format_date(task.created_at),
            'due_date': format_date(task.due_date),
            'overdue': task.is_overdue(),
        }
        for task in tasks
    ]


def login(data):
    if not data:
        raise ApiError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ApiError('Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise ApiError('Credenciais inválidas', 401)

    if not user.active:
        raise ApiError('Usuário inativo', 403)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user.id),
    }
