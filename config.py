import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-cle-secrete-changez-moi'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"mysql+pymysql://{os.environ.get('DB_USER', 'root')}:{os.environ.get('DB_PASSWORD', 'Azerty1234')}@{os.environ.get('DB_HOST', 'localhost')}/{os.environ.get('DB_NAME', 'hopital_db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration de la base de données
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'Azerty1234'
    DB_NAME = os.environ.get('DB_NAME') or 'hopital_db'
    
    # Configuration de l'application
    DEBUG = os.environ.get('DEBUG') == 'True'
    TESTING = False
    
    # Limites
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Timezone
    TIMEZONE = 'Europe/Paris'

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@hopital.local')

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    PER_PAGE = 12

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}"

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
