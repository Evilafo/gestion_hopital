from flask import Flask, g, request
import os
import uuid

from config import config
from hopital.extensions import db, login_manager, csrf, mail, migrate, limiter
from hopital.routes import register_routes
from hopital.services.services import ensure_schema
from hopital.security import SecurityConfig
from hopital.error_handlers import register_error_handlers
from hopital.logging_config import setup_logging


def create_app(config_name=None):
    app = Flask(__name__, template_folder='hopital/templates', static_folder='static')
    env = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[env])
    os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'static', 'uploads')), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Veuillez vous connecter pour continuer.'
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Configuration du logging
    setup_logging(app)
    
    # Enregistrement des handlers d'erreurs
    register_error_handlers(app)
    
    # Middleware pour le contexte de requête
    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())
        if hasattr(g, 'user') and g.user.is_authenticated:
            g.user_id = g.user.id
    
    @app.after_request
    def after_request(response):
        response.headers['X-Request-ID'] = g.get('request_id', '')
        return response
    
    # Configuration de sécurité
    app.config['SESSION_COOKIE_HTTPONLY'] = SecurityConfig.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = SecurityConfig.SESSION_COOKIE_SAMESITE
    app.config['PERMANENT_SESSION_LIFETIME'] = SecurityConfig.PERMANENT_SESSION_LIFETIME
    
    # Headers de sécurité
    @app.after_request
    def set_security_headers(response):
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    from hopital import models  # noqa: F401
    register_routes(app)

    with app.app_context():
        if not app.config.get('TESTING'):
            ensure_schema()

    return app


if __name__ == '__main__':
    application = create_app()
    from hopital.models import User
    from hopital.extensions import generate_secure_password
    with application.app_context():
        if User.query.filter_by(role='admin').count() == 0:
            # Générer un mot de passe sécurisé pour l'admin
            admin_password = generate_secure_password(16)
            admin = User(
                nom='Admin', prenom='Système', email='admin@hopital.com',
                role='admin', contact='0000000000', compte_web=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"⚠️  Compte admin créé avec mot de passe sécurisé: {admin_password}")
            print("⚠️  Changez ce mot de passe immédiatement après la première connexion !")
    debug = os.environ.get('FLASK_ENV') != 'production'
    application.run(debug=debug)
