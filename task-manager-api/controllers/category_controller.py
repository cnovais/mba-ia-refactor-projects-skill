from sqlalchemy import func

import database
from database import db
from errors import ApiError
from models.category import Category
from models.task import Task
from validators.category_validator import validate_category_payload


def list_categories():
    categories = Category.query.all()

    # One aggregated query instead of one COUNT(*) per category (N+1).
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .group_by(Task.category_id)
        .all()
    )

    result = []
    for category in categories:
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    if not data:
        raise ApiError('Dados inválidos')

    cleaned, error = validate_category_payload(data, partial=False)
    if error:
        raise ApiError(error)

    category = Category(**cleaned)
    db.session.add(category)
    database.save()
    return category.to_dict()


def update_category(cat_id, data):
    category = db.session.get(Category, cat_id)
    if not category:
        raise ApiError('Categoria não encontrada', 404)

    if not data:
        raise ApiError('Dados inválidos')

    cleaned, error = validate_category_payload(data, partial=True)
    if error:
        raise ApiError(error)

    for field, value in cleaned.items():
        setattr(category, field, value)

    database.save()
    return category.to_dict()


def delete_category(cat_id):
    category = db.session.get(Category, cat_id)
    if not category:
        raise ApiError('Categoria não encontrada', 404)

    db.session.delete(category)
    database.save()
