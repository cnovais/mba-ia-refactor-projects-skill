"""Central place for every secret, connection string, and environment-dependent
value. Nothing outside this module should read `os.environ` directly.

Values fall back to safe, clearly-marked development defaults so `python app.py`
keeps working out of the box for local development (matching the project's README),
but every value is overridable via a real environment variable / `.env` file, and
none of them is a real secret committed to source control.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-not-for-production')

DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')

DEBUG = _bool_env('FLASK_DEBUG', True)
HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
PORT = int(os.environ.get('FLASK_PORT', '5000'))

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', str(60 * 60 * 24)))
