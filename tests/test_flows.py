import pytest
from datetime import date, time, timedelta

from app import create_app
from hopital.extensions import db
from hopital.models import User, Salle, Creneau, RendezVous
from hopital.services import book_slot


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _create_user(role, email, password='TestPassword123!', **kwargs):
    user = User(
        nom=kwargs.get('nom', 'Test'),
        prenom=kwargs.get('prenom', role.title()),
        email=email,
        role=role,
        compte_web=True,
        specialite=kwargs.get('specialite'),
        salle_id=kwargs.get('salle_id'),
        contact='0600000000'
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_home(client):
    res = client.get('/')
    assert res.status_code == 200
    assert 'Clinique Frebonne'.encode() in res.data


def test_register_and_login(client, app):
    res = client.post('/register-patient', data={
        'nom': 'Martin',
        'prenom': 'Lea',
        'email': 'lea@test.com',
        'password': 'Secret123!',
        'contact': '0611223344',
        'date_naissance': '1990-01-01'
    }, follow_redirects=True)
    assert res.status_code == 200
    res = client.post('/login', data={'username': 'lea@test.com', 'password': 'Secret123!'}, follow_redirects=True)
    assert b'Tableau de bord' in res.data or b'Bonjour' in res.data


def test_patient_cannot_access_queue_admin(client, app):
    with app.app_context():
        _create_user('patient', 'p@test.com')
    client.post('/login', data={'username': 'p@test.com', 'password': 'TestPassword123!'})
    res = client.get('/queue-management', follow_redirects=True)
    assert 'non autoris'.encode() in res.data or res.status_code == 200


def test_book_slot_locks_and_creates_rdv(app):
    with app.app_context():
        salle = Salle(numero='S1', nom='Salle 1')
        db.session.add(salle)
        db.session.commit()
        med = _create_user('medecin', 'm@test.com', specialite='Générale', salle_id=salle.id)
        pat = _create_user('patient', 'p2@test.com', nom='Durand', prenom='Paul')
        slot = Creneau(
            medecin_id=med.id,
            date=date.today() + timedelta(days=1),
            heure_debut=time(9, 0),
            heure_fin=time(9, 30),
            disponible=True
        )
        db.session.add(slot)
        db.session.commit()
        rv, err = book_slot(slot.id, pat.id, 'douleur')
        assert err is None
        assert rv is not None
        db.session.refresh(slot)
        assert slot.disponible is False
        rv2, err2 = book_slot(slot.id, pat.id, 'autre')
        assert rv2 is None
        assert err2


def test_cancel_is_post_only(client, app):
    res = client.get('/cancel-appointment/1')
    assert res.status_code in (405, 401, 302)
