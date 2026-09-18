import pytest
from datetime import date, datetime
from hopital.models import User, PatientProfil, Salle, Creneau, RendezVous, FileAttente, NoteConsultation


class TestUser:
    """Tests pour le modèle User"""
    
    def test_create_user(self, db_session):
        """Test la création d'un utilisateur"""
        user = User(
            nom='Dupont',
            prenom='Jean',
            email='jean.dupont@example.com',
            role='patient',
            contact='0123456789',
            compte_web=True
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == 'jean.dupont@example.com'
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_user_age(self, db_session):
        """Test le calcul de l'âge"""
        user = User(
            nom='Test',
            prenom='User',
            email='test2@example.com',
            role='patient',
            date_naissance=date(1990, 1, 1),
            compte_web=True
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        age = user.age
        assert age is not None
        assert age > 30  # En 2026, la personne née en 1990 a 36 ans
    
    def test_user_full_name(self, db_session):
        """Test le nom complet"""
        user = User(
            nom='Dupont',
            prenom='Jean',
            email='jean.dupont2@example.com',
            role='patient',
            compte_web=True
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        assert user.nom_complet == "Jean Dupont"


class TestPatientProfil:
    """Tests pour le modèle PatientProfil"""
    
    def test_create_patient_profil(self, db_session):
        """Test la création d'un profil patient"""
        user = User(
            nom='Test',
            prenom='Patient',
            email='patient@example.com',
            role='patient',
            compte_web=True
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        profil = PatientProfil(
            user_id=user.id,
            numero_dossier='DOS-000001',
            allergies='Pénicilline',
            antecedents='Diabète type 2'
        )
        db_session.add(profil)
        db_session.commit()
        
        assert profil.id is not None
        assert profil.numero_dossier == 'DOS-000001'
        assert profil.allergies == 'Pénicilline'


class TestSalle:
    """Tests pour le modèle Salle"""
    
    def test_create_salle(self, db_session):
        """Test la création d'une salle"""
        salle = Salle(
            numero='SALLE-001',
            nom='Salle de consultation A',
            disponible=True
        )
        db_session.add(salle)
        db_session.commit()
        
        assert salle.id is not None
        assert salle.numero == 'SALLE-001'
        assert salle.disponible is True


class TestCreneau:
    """Tests pour le modèle Creneau"""
    
    def test_create_creneau(self, db_session):
        """Test la création d'un créneau"""
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
        
        creneau = Creneau(
            medecin_id=medecin.id,
            date=date(2026, 9, 15),
            heure_debut=datetime.strptime('09:00', '%H:%M').time(),
            heure_fin=datetime.strptime('09:30', '%H:%M').time(),
            disponible=True
        )
        db_session.add(creneau)
        db_session.commit()
        
        assert creneau.id is not None
        assert creneau.disponible is True
        assert creneau.medecin_id == medecin.id


class TestRendezVous:
    """Tests pour le modèle RendezVous"""
    
    def test_create_rendez_vous(self, db_session):
        """Test la création d'un rendez-vous"""
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
        
        creneau = Creneau(
            medecin_id=medecin.id,
            date=date(2026, 9, 15),
            heure_debut=datetime.strptime('09:00', '%H:%M').time(),
            heure_fin=datetime.strptime('09:30', '%H:%M').time(),
            disponible=True
        )
        db_session.add(creneau)
        db_session.commit()
        
        rdv = RendezVous(
            patient_id=patient.id,
            medecin_id=medecin.id,
            creneau_id=creneau.id,
            date=date(2026, 9, 15),
            heure=datetime.strptime('09:00', '%H:%M').time(),
            statut='Confirmé',
            motif='Consultation générale'
        )
        db_session.add(rdv)
        db_session.commit()
        
        assert rdv.id is not None
        assert rdv.statut == 'Confirmé'
        assert rdv.motif == 'Consultation générale'


class TestFileAttente:
    """Tests pour le modèle FileAttente"""
    
    def test_create_file_attente(self, db_session):
        """Test la création d'une entrée dans la file d'attente"""
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
        
        medecin = User(
            nom='Test',
            prenom='Medecin',
            email='medecin4@example.com',
            role='medecin',
            specialite='Cardiologie',
            compte_web=True
        )
        medecin.set_password('password123')
        db_session.add(medecin)
        db_session.commit()
        
        creneau = Creneau(
            medecin_id=medecin.id,
            date=date(2026, 9, 15),
            heure_debut=datetime.strptime('09:00', '%H:%M').time(),
            heure_fin=datetime.strptime('09:30', '%H:%M').time(),
            disponible=True
        )
        db_session.add(creneau)
        db_session.commit()
        
        rdv = RendezVous(
            patient_id=patient.id,
            medecin_id=medecin.id,
            creneau_id=creneau.id,
            date=date(2026, 9, 15),
            heure=datetime.strptime('09:00', '%H:%M').time(),
            statut='Confirmé'
        )
        db_session.add(rdv)
        db_session.commit()
        
        file_entry = FileAttente(
            rendez_vous_id=rdv.id,
            patient_id=patient.id,
            medecin_id=medecin.id,
            date=date(2026, 9, 15),
            heure_rendezvous=datetime.strptime('09:00', '%H:%M').time(),
            statut_file='Non arrivé',
            ordre=1
        )
        db_session.add(file_entry)
        db_session.commit()
        
        assert file_entry.id is not None
        assert file_entry.statut_file == 'Non arrivé'
        assert file_entry.ordre == 1