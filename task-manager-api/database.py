from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def save():
    """Commit the current session; on failure, roll back and re-raise so the
    centralized error handler (middlewares/error_handler.py) logs it and returns a
    consistent error response, instead of every controller repeating try/except."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
