from datetime import datetime, timezone


def utcnow():
    """Current UTC time as a naive datetime, matching the values already stored in the DB."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
