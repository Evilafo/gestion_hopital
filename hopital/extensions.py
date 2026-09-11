from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets
import string

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "500 per hour"],
    storage_uri="memory://",
    enabled=True
)


def generate_secure_password(length=16):
    """Génère un mot de passe sécurisé"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password
