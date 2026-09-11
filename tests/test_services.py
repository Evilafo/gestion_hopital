import pytest
from datetime import date, datetime
from hopital.services.patient_service import PatientService
from hopital.services.appointment_service import AppointmentService
from hopital.services.queue_service import QueueService
from hopital.services.auth_service import AuthService
from hopital import models
User = models.User
Creneau = models.Creneau
RendezVous = models.RendezVous
FileAttente = models.FileAttente


class TestAuthService:
    """Tests pour le service d'authentification"""
    
    def test_authenticate_user_success(self, db_session, test_user):
        """Test l'authentification réussie"""
        user, error = AuthService.authenticate_user(test_user.email, 'TestPassword123!')
        assert user is not None
        assert error is None
        assert user.email == test_user.email
    
    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Test l'authentification avec mauvais mot de passe"""
        user, error = AuthService.authenticate_user(test_user.email, 'wrongpassword')
        assert user is None
        assert error is not None
        assert "incorrects" in error
    
    def test_authenticate_user_nonexistent(self, db_session):
        """Test l'authentification avec utilisateur inexistant"""
        user, error = AuthService.authenticate_user('nonexistent@example.com', 'password')
        assert user is None
        assert error is not None
    
    def test_register_patient_success(self, db_session):
        """Test l'inscription réussie"""
        data = {
            'nom': 'Nouveau',
            'prenom': 'Patient',
            'email': 'nouveau@example.com',
            'password': 'SecurePass123!',
            'contact': '0123456789',
            'date_naissance': '1990-01-01'
        }
        user, error = AuthService.register_patient(data)
        assert user is not None
        assert error is None
        assert user.email == 'nouveau@example.com'
    
    def test_register_patient_duplicate_email(self, db_session, test_user):
        """Test l'inscription avec email déjà utilisé"""
        data = {
            'nom': 'Nouveau',
            'prenom': 'Patient',
            'email': test_user.email,
            'password': 'SecurePass123!',
            'contact': '0123456789',
            'date_naissance': '1990-01-01'
        }
        user, error = AuthService.register_patient(data)
        assert user is None
        assert error is not None
        assert "déjà utilisé" in error


class TestPatientService:
    """Tests pour le service patient"""
    
    def test_ensure_patient_profile(self, db_session, test_user):
        """Test la création automatique du profil patient"""
        profil = PatientService.ensure_patient_profile(test_user)
        assert profil is not None
        assert profil.user_id == test_user.id
        assert profil.numero_dossier is not None
    
    def test_update_patient_profile(self, db_session, test_user):
        """Test la mise à jour du profil patient"""
        data = {
            'nom': 'NouveauNom',
            'prenom': 'NouveauPrenom',
            'contact': '0987654321',
            'allergies': 'Aucune',
            'antecedents': 'Aucun'
        }
        success, error = PatientService.update_patient_profile(test_user, data)
        assert success is True
        assert error is None
        assert test_user.nom == 'NouveauNom'
        assert test_user.contact == '0987654321'
    
    def test_search_patients(self, db_session, test_user):
        """Test la recherche de patients"""
        results = PatientService.search_patients('Test', page=1, per_page=10)
        assert len(results.items) > 0
        assert any(p.email == test_user.email for p in results.items)


class TestAppointmentService:
    """Tests pour le service de rendez-vous"""
    
    def test_book_slot_success(self, db_session):
        """Test la réservation réussie d'un créneau"""
        medecin = User(
            nom='Test',
            prenom='Medecin',
            email='medecin@example.com',
            role='medecin',
            specialite='Cardiologie',
            compte_web=True
        )
        medecin.set_password('password123')
        db_session.add(medecin)
        db_session.commit()
        
        patient = User(
            nom='Test',
            prenom='Patient',
            email='patient@example.com',
            role='patient',
            compte_web=True
        )
        patient.set_password('password123')
        db_session.add(patient)
        db_session.commit()
        
        creneau = Creneau(
            medecin_id=medecin.id,
            date=date(2026, 9, 20),
            heure_debut=datetime.strptime('10:00', '%H:%M').time(),
            heure_fin=datetime.strptime('10:30', '%H:%M').time(),
            disponible=True
        )
        db_session.add(creneau)
        db_session.commit()
        
        rv, error = AppointmentService.book_slot(creneau.id, patient.id, 'Consultation')
        assert rv is not None
        assert error is None
        assert rv.statut == 'Confirmé'
        assert creneau.disponible is False
    
    def test_book_slot_unavailable(self, db_session):
        """Test la réservation d'un créneau indisponible"""
        medecin = User(
            nom='Test',
            prenom='Medecin',
            email='medecin2@example.com',
            role='medecin',
            specialite='Cardiologie',
            compte_web=True
        )
        medecin.set_password('password123')
        db_session.add(medecin)
        db_session.commit()
        
        patient = User(
            nom='Test',
            prenom='Patient',
            email='patient2@example.com',
            role='patient',
            compte_web=True
        )
        patient.set_password('password123')
        db_session.add(patient)
        db_session.commit()
        
        creneau = Creneau(
            medecin_id=medecin.id,
            date=date(2026, 9, 20),
            heure_debut=datetime.strptime('10:00', '%H:%M').time(),
            heure_fin=datetime.strptime('10:30', '%H:%M').time(),
            disponible=False
        )
        db_session.add(creneau)
        db_session.commit()
        
        rv, error = AppointmentService.book_slot(creneau.id, patient.id, 'Consultation')
        assert rv is None
        assert error is not None
        assert "disponible" in error.lower()


class TestQueueService:
    """Tests pour le service de file d'attente"""
    
    def test_sync_file_du_jour(self, db_session):
        """Test la synchronisation de la file d'attente"""
        medecin = User(
            nom='Test',
            prenom='Medecin',
            email='medecin3@example.com',
            role='medecin',
            specialite='Cardiologie',
            compte_web=True
        )
        medecin.set_password('password123')
        db_session.add(medecin)
        db_session.commit()
        
        patient = User(
            nom='Test',
            prenom='Patient',
            email='patient3@example.com',
            role='patient',
            compte_web=True
        )
        patient.set_password('password123')
        db_session.add(patient)
        db_session.commit()
        
        creneau = Creneau(
            medecin_id=medecin.id,
            date=date.today(),
            heure_debut=datetime.strptime('10:00', '%H:%M').time(),
            heure_fin=datetime.strptime('10:30', '%H:%M').time(),
            disponible=True
        )
        db_session.add(creneau)
        db_session.commit()
        
        rv = RendezVous(
            patient_id=patient.id,
            medecin_id=medecin.id,
            creneau_id=creneau.id,
            date=date.today(),
            heure=datetime.strptime('10:00', '%H:%M').time(),
            statut='Confirmé'
        )
        db_session.add(rv)
        db_session.commit()
        
        QueueService.sync_file_du_jour(date.today())
        
        file_entry = FileAttente.query.filter_by(rendez_vous_id=rv.id).first()
        assert file_entry is not None
        assert file_entry.statut_file == 'Non arrivé'