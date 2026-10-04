from errors import NotFoundError
from models.category import Category
from models.task import Task
from validators.category_validator import validate_category_create, validate_category_update


def _get_category_or_404(category_id):
    category = Category.get_by_id(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    task_counts = Task.count_by_category()
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    fields = validate_category_create(data)
    return Category(**fields).save().to_dict()


def update_category(category_id, data):
    category = _get_category_or_404(category_id)
    for field, value in validate_category_update(data).items():
        setattr(category, field, value)
    category.save()
    return category.to_dict()


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    Task.detach_category(category.id)
    category.delete()
    return {'message': 'Categoria deletada'}
