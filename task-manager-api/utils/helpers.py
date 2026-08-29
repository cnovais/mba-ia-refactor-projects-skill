"""Generic, framework-agnostic helpers shared across models/validators/controllers.

Domain-shaped validation (which fields a task/user/category payload needs) lives in
`validators/`, which imports the constants and primitives defined here instead of
redefining them.
"""
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger("task_manager")


def utc_now():
    """Naive UTC timestamp — the direct, non-deprecated replacement for
    `datetime.utcnow()` that still compares correctly against the naive datetimes
    already stored in the database (SQLite has no timezone-aware datetime type)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    if email and re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
        return True
    return False


def sanitize_string(s):
    if s:
        return s.strip()
    return s


def parse_date(date_string):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_string, fmt)
        except (TypeError, ValueError):
            continue
    return None


def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False


def log_action(action, details=None):
    if details:
        logger.info("%s: %s", action, details)
    else:
        logger.info(action)


VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
PRIORITY_LABELS = {
    1: 'critical',
    2: 'high',
    3: 'medium',
    4: 'low',
    5: 'minimal',
}
HIGH_PRIORITY_THRESHOLD = 2
