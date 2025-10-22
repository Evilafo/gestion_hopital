import os
from dotenv import load_dotenv

# Charge les variables d'environnement depuis un fichier .env
# C'est utile pour le développement local afin de ne pas exposer les secrets dans le code.
load_dotenv()

class Config:
    """Configuration de base, partagée par tous les environnements."""
    # Clé secrète pour la sécurité des sessions et autres. Doit être complexe et unique.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-cle-secrete-changez-moi'
    
    # Chaîne de connexion à la base de données.
    # Utilise les variables d'environnement pour construire l'URI.
    # 'pymysql' est le driver Python pour se connecter à MySQL.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"mysql+pymysql://{os.environ.get('DB_USER', 'root')}:{os.environ.get('DB_PASSWORD', 'Azerty1234')}@{os.environ.get('DB_HOST', 'localhost')}/{os.environ.get('DB_NAME', 'hopital_db')}"
    # Désactive une fonctionnalité de Flask-SQLAlchemy qui n'est pas nécessaire et consomme des ressources.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Variables de base de données (utilisées pour construire l'URI ci-dessus)
    DB_HOST = os.environ.get('DB_HOST')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    
    # Configuration générale de l'application
    DEBUG = os.environ.get('DEBUG')
    TESTING = False
    
    # Limite la taille maximale des fichiers uploadés (par exemple, pour des dossiers médicaux)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Fuseau horaire (pour la gestion des dates et heures)
    TIMEZONE = 'UTC'

class DevelopmentConfig(Config):
    """Configuration pour l'environnement de développement."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}"

class ProductionConfig(Config):
    """Configuration pour l'environnement de production. Le mode DEBUG est désactivé pour la sécurité."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}"

class TestingConfig(Config):
    """Configuration pour les tests automatisés. Utilise une base de données en mémoire pour la rapidité."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
# Dictionnaire pour accéder facilement aux classes de configuration par leur nom.
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
