import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from hopital.extensions import db
from hopital import models  # Import all models

# Make models available globally for tests
User = models.User
Creneau = models.Creneau
RendezVous = models.RendezVous
FileAttente = models.FileAttente
PatientProfil = models.PatientProfil
Salle = models.Salle
NoteConsultation = models.NoteConsultation
JournalAcces = models.JournalAcces


@pytest.fixture
def app():
    """Crée une application Flask de test"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Crée un client de test"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Crée une session de base de données de test"""
    with app.app_context():
        yield db.session
        db.session.remove()


@pytest.fixture
def test_user(db_session):
    """Crée un utilisateur de test"""
    user = User(
        nom='Test',
        prenom='User',
        email='test@example.com',
        role='patient',
        contact='0123456789',
        compte_web=True
    )
    user.set_password('TestPassword123!')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_admin(db_session):
    """Crée un administrateur de test"""
    admin = User(
        nom='Admin',
        prenom='Test',
        email='admin@example.com',
        role='admin',
        contact='0123456789',
        compte_web=True
    )
    admin.set_password('AdminPassword123!')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def test_medecin(db_session):
    """Crée un médecin de test"""
    medecin = User(
        nom='Medecin',
        prenom='Test',
        email='medecin@example.com',
        role='medecin',
        specialite='Cardiologie',
        contact='0123456789',
        compte_web=True
    )
    medecin.set_password('MedecinPassword123!')
    db_session.add(medecin)
    db_session.commit()
    return medecin


@pytest.fixture
def authenticated_client(client, test_user):
    """Crée un client authentifié"""
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
        session['_fresh'] = True
    return client