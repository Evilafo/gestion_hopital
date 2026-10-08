"""Seed sample data for testing

Revision ID: 003
Revises: 002
Create Date: 2026-10-08

"""
from alembic import op
import sqlalchemy as sa
from datetime import date, timedelta, time
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key=True)
    nom = sa.Column(sa.String(100))
    prenom = sa.Column(sa.String(100))
    email = sa.Column(sa.String(120), unique=True)
    role = sa.Column(sa.String(50))
    contact = sa.Column(sa.String(20))
    specialite = sa.Column(sa.String(100))
    salle_id = sa.Column(sa.Integer)
    compte_web = sa.Column(sa.Boolean)
    date_naissance = sa.Column(sa.Date)


class Salle(Base):
    __tablename__ = 'salle'
    id = sa.Column(sa.Integer, primary_key=True)
    numero = sa.Column(sa.String(20), unique=True)
    nom = sa.Column(sa.String(100))


class PatientProfil(Base):
    __tablename__ = 'patient_profil'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, unique=True)
    numero_dossier = sa.Column(sa.String(40), unique=True)
    allergies = sa.Column(sa.Text)
    antecedents = sa.Column(sa.Text)


class Creneau(Base):
    __tablename__ = 'creneau'
    id = sa.Column(sa.Integer, primary_key=True)
    medecin_id = sa.Column(sa.Integer)
    date = sa.Column(sa.Date)
    heure_debut = sa.Column(sa.Time)
    heure_fin = sa.Column(sa.Time)
    disponible = sa.Column(sa.Boolean)


class RendezVous(Base):
    __tablename__ = 'rendez_vous'
    id = sa.Column(sa.Integer, primary_key=True)
    patient_id = sa.Column(sa.Integer)
    medecin_id = sa.Column(sa.Integer)
    creneau_id = sa.Column(sa.Integer)
    date = sa.Column(sa.Date)
    heure = sa.Column(sa.Time)
    statut = sa.Column(sa.String(50))
    motif = sa.Column(sa.String(255))


def get_or_create(session, model, defaults=None, **kwargs):
    """Récupère ou crée un enregistrement de manière idempotente"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = {k: v for k, v in kwargs.items() if not isinstance(v, sa.sql.expression.ClauseElement)}
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True


def upgrade():
    connection = op.get_bind()
    Session = sessionmaker(bind=connection)
    session = Session()

    try:
        # Créer les salles si elles n'existent pas
        print("🏥 Création des salles...")
        salles_data = [
            {'numero': 'S101', 'nom': 'Consultation Générale'},
            {'numero': 'S102', 'nom': 'Consultation Cardiologie'},
            {'numero': 'S103', 'nom': 'Consultation Dermatologie'},
            {'numero': 'S104', 'nom': 'Consultation Pédiatrie'},
            {'numero': 'S105', 'nom': 'Consultation ORL'},
        ]

        salles = {}
        for salle_data in salles_data:
            salle, created = get_or_create(session, Salle, defaults={'nom': salle_data['nom']}, numero=salle_data['numero'])
            salles[salle_data['numero']] = salle

        # Créer les secrétaires si ils n'existent pas
        print("👤 Création des secrétaires...")
        secretaires_data = [
            {
                'nom': 'Dupont',
                'prenom': 'Marie',
                'email': 'marie.dupont@cliniquebodo.com',
                'role': 'secretaire',
                'contact': '0601020304',
                'compte_web': True
            },
            {
                'nom': 'Martin',
                'prenom': 'Jean',
                'email': 'jean.martin@cliniquebodo.com',
                'role': 'secretaire',
                'contact': '0605060708',
                'compte_web': True
            }
        ]

        for sec_data in secretaires_data:
            user, created = get_or_create(session, User, defaults={
                'nom': sec_data['nom'],
                'prenom': sec_data['prenom'],
                'role': sec_data['role'],
                'contact': sec_data['contact'],
                'compte_web': sec_data['compte_web']
            }, email=sec_data['email'])
            if created:
                # Hasher le mot de passe avec Werkzeug
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash('Secret1234')

        # Créer les médecins si ils n'existent pas
        print("👨‍⚕️ Création des médecins...")
        medecins_data = [
            {
                'nom': 'Bernard',
                'prenom': 'Pierre',
                'email': 'pierre.bernard@cliniquebodo.com',
                'specialite': 'Médecine Générale',
                'salle_num': 'S101',
                'contact': '0612345678'
            },
            {
                'nom': 'Lefevre',
                'prenom': 'Sophie',
                'email': 'sophie.lefevre@cliniquebodo.com',
                'specialite': 'Cardiologie',
                'salle_num': 'S102',
                'contact': '0623456789'
            },
            {
                'nom': 'Moreau',
                'prenom': 'Lucas',
                'email': 'lucas.moreau@cliniquebodo.com',
                'specialite': 'Dermatologie',
                'salle_num': 'S103',
                'contact': '0634567890'
            },
            {
                'nom': 'Petit',
                'prenom': 'Emma',
                'email': 'emma.petit@cliniquebodo.com',
                'specialite': 'Pédiatrie',
                'salle_num': 'S104',
                'contact': '0645678901'
            },
            {
                'nom': 'Robert',
                'prenom': 'Thomas',
                'email': 'thomas.robert@cliniquebodo.com',
                'specialite': 'ORL',
                'salle_num': 'S105',
                'contact': '0656789012'
            }
        ]

        medecins = []
        for m_data in medecins_data:
            user, created = get_or_create(session, User, defaults={
                'nom': m_data['nom'],
                'prenom': m_data['prenom'],
                'role': 'medecin',
                'specialite': m_data['specialite'],
                'salle_id': salles[m_data['salle_num']].id,
                'contact': m_data['contact'],
                'compte_web': True
            }, email=m_data['email'])
            if created:
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash('Medecin1234')
            medecins.append(user)

        # Créer les patients si ils n'existent pas
        print("👥 Création des patients...")
        patients_data = [
            {
                'nom': 'Kouassi',
                'prenom': 'Aya',
                'email': 'aya.kouassi@email.com',
                'contact': '0701020304',
                'date_naissance': date(1985, 5, 15),
                'allergies': 'Pénicilline',
                'antecedents': 'Hypertension légère'
            },
            {
                'nom': 'Koné',
                'prenom': 'Yao',
                'email': 'yao.kone@email.com',
                'contact': '0705060708',
                'date_naissance': date(1972, 8, 22),
                'allergies': None,
                'antecedents': 'Diabète type 2'
            },
            {
                'nom': 'Touré',
                'prenom': 'Adjoua',
                'email': 'adjoua.toure@email.com',
                'contact': '0709080706',
                'date_naissance': date(1990, 3, 10),
                'allergies': 'Araignées',
                'antecedents': None
            },
            {
                'nom': 'Bakayoko',
                'prenom': 'Kouamé',
                'email': 'kouame.bakayoko@email.com',
                'contact': '0712345678',
                'date_naissance': date(1988, 11, 5),
                'allergies': None,
                'antecedents': 'Asthme'
            },
            {
                'nom': 'Diallo',
                'prenom': 'Aminata',
                'email': 'aminata.diallo@email.com',
                'contact': '0723456789',
                'date_naissance': date(1995, 7, 20),
                'allergies': 'Pollens',
                'antecedents': None
            },
            {
                'nom': 'Cissé',
                'prenom': 'Ibrahim',
                'email': 'ibrahim.cisse@email.com',
                'contact': '0734567890',
                'date_naissance': date(1965, 2, 14),
                'allergies': None,
                'antecedents': 'Cholestérol élevé'
            },
            {
                'nom': 'Ouattara',
                'prenom': 'Fatou',
                'email': 'fatou.ouattara@email.com',
                'contact': '0745678901',
                'date_naissance': date(1992, 9, 8),
                'allergies': 'Latex',
                'antecedents': None
            },
            {
                'nom': 'Coulibaly',
                'prenom': 'Kouadio',
                'email': 'kouadio.coulibaly@email.com',
                'contact': '0756789012',
                'date_naissance': date(1978, 4, 30),
                'allergies': None,
                'antecedents': 'Arthrite'
            },
            {
                'nom': 'Yao',
                'prenom': 'Koffi',
                'email': 'koffi.yao@email.com',
                'contact': '0767890123',
                'date_naissance': date(1980, 6, 12),
                'allergies': 'Fruits de mer',
                'antecedents': 'Migraines'
            },
            {
                'nom': 'Diomandé',
                'prenom': 'Mariam',
                'email': 'mariam.diomande@email.com',
                'contact': '0778901234',
                'date_naissance': date(1987, 1, 25),
                'allergies': None,
                'antecedents': 'Gastrite'
            },
            {
                'nom': 'Dosso',
                'prenom': 'Sylla',
                'email': 'sylla.dosso@email.com',
                'contact': '0789012345',
                'date_naissance': date(1993, 8, 17),
                'allergies': 'Noix',
                'antecedents': None
            },
            {
                'nom': 'Koffi',
                'prenom': 'N\'Goran',
                'email': 'ngoran.koffi@email.com',
                'contact': '0790123456',
                'date_naissance': date(1975, 3, 3),
                'allergies': None,
                'antecedents': 'Hypertension'
            },
            {
                'nom': 'N\'Guessan',
                'prenom': 'Euphrasie',
                'email': 'euphrasie.nguessan@email.com',
                'contact': '0801234567',
                'date_naissance': date(1982, 11, 28),
                'allergies': 'Poussière',
                'antecedents': 'Allergies respiratoires'
            },
            {
                'nom': 'Bamba',
                'prenom': 'Jean-Yves',
                'email': 'jeanyves.bamba@email.com',
                'contact': '0812345678',
                'date_naissance': date(1990, 4, 14),
                'allergies': None,
                'antecedents': None
            },
            {
                'nom': 'Gbaka',
                'prenom': 'Aya',
                'email': 'aya.gbaka@email.com',
                'contact': '0823456789',
                'date_naissance': date(1970, 9, 9),
                'allergies': 'Pénicilline',
                'antecedents': 'Diabète'
            },
            {
                'nom': 'Traoré',
                'prenom': 'Lassina',
                'email': 'lassina.traore@email.com',
                'contact': '0834567890',
                'date_naissance': date(1989, 2, 20),
                'allergies': None,
                'antecedents': 'Tension artérielle'
            }
        ]

        patients = []
        for i, p_data in enumerate(patients_data):
            user, created = get_or_create(session, User, defaults={
                'nom': p_data['nom'],
                'prenom': p_data['prenom'],
                'role': 'patient',
                'contact': p_data['contact'],
                'date_naissance': p_data['date_naissance'],
                'compte_web': True
            }, email=p_data['email'])
            if created:
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash('Patient1234')
            patients.append(user)

            # Créer le profil patient
            profil, _ = get_or_create(session, PatientProfil, defaults={
                'numero_dossier': f'PAT{20240001 + i:06d}',
                'allergies': p_data['allergies'],
                'antecedents': p_data['antecedents']
            }, user_id=user.id)

        # Créer des créneaux pour les médecins (prochaines 2 semaines)
        print("📅 Création des créneaux...")
        today = date.today()
        creneaux_count = 0

        for medecin in medecins:
            for day_offset in range(14):  # 14 jours
                current_date = today + timedelta(days=day_offset)
                if current_date.weekday() < 5:  # Du lundi au vendredi
                    # Créneaux de la matinée (8h-12h)
                    for hour in range(8, 12):
                        creneau, created = get_or_create(session, Creneau, defaults={
                            'disponible': True
                        }, medecin_id=medecin.id, date=current_date, heure_debut=time(hour, 0), heure_fin=time(hour, 0, 30))
                        if created:
                            creneaux_count += 1

                    # Créneaux de l'après-midi (14h-18h)
                    for hour in range(14, 18):
                        creneau, created = get_or_create(session, Creneau, defaults={
                            'disponible': True
                        }, medecin_id=medecin.id, date=current_date, heure_debut=time(hour, 0), heure_fin=time(hour, 0, 30))
                        if created:
                            creneaux_count += 1

        # Créer quelques rendez-vous pour aujourd'hui
        print("📝 Création des rendez-vous...")
        rendez_vous_data = [
            {
                'patient_idx': 0,
                'medecin_idx': 0,
                'date': today,
                'heure': time(9, 0),
                'motif': 'Consultation de routine'
            },
            {
                'patient_idx': 1,
                'medecin_idx': 1,
                'date': today,
                'heure': time(9, 0),
                'motif': 'Suivi cardiaque'
            },
            {
                'patient_idx': 2,
                'medecin_idx': 2,
                'date': today,
                'heure': time(9, 0),
                'motif': 'Éruption cutanée'
            },
            {
                'patient_idx': 3,
                'medecin_idx': 3,
                'date': today,
                'heure': time(9, 0),
                'motif': 'Visite pédiatrique'
            },
            {
                'patient_idx': 4,
                'medecin_idx': 4,
                'date': today,
                'heure': time(9, 0),
                'motif': 'Douleurs oreilles'
            },
            {
                'patient_idx': 5,
                'medecin_idx': 0,
                'date': today,
                'heure': time(10, 0),
                'motif': 'Bilan de santé'
            },
            {
                'patient_idx': 6,
                'medecin_idx': 1,
                'date': today,
                'heure': time(10, 0),
                'motif': 'Électrocardiogramme'
            },
            {
                'patient_idx': 7,
                'medecin_idx': 2,
                'date': today,
                'heure': time(10, 0),
                'motif': 'Examen dermatologique'
            },
            {
                'patient_idx': 8,
                'medecin_idx': 3,
                'date': today,
                'heure': time(11, 0),
                'motif': 'Vaccination'
            },
            {
                'patient_idx': 9,
                'medecin_idx': 4,
                'date': today,
                'heure': time(11, 0),
                'motif': 'Contrôle ORL'
            }
        ]

        rv_count = 0
        for rv_data in rendez_vous_data:
            patient = patients[rv_data['patient_idx']]
            medecin = medecins[rv_data['medecin_idx']]

            # Trouver un créneau disponible
            creneau = session.query(Creneau).filter(
                Creneau.medecin_id == medecin.id,
                Creneau.date == rv_data['date'],
                Creneau.heure_debut == rv_data['heure'],
                Creneau.disponible == True
            ).first()

            if creneau:
                rv, created = get_or_create(session, RendezVous, defaults={
                    'patient_id': patient.id,
                    'medecin_id': medecin.id,
                    'creneau_id': creneau.id,
                    'date': rv_data['date'],
                }, medecin_id=medecin.id, patient_id=patient.id, date=rv_data['date'], heure=rv_data['heure'])

                if created:
                    rv.statut = 'Confirmé'
                    rv.motif = rv_data['motif']
                    creneau.disponible = False
                    rv_count += 1

        session.commit()

        print("✅ Migration terminée avec succès !")
        print(f"   - {len(salles)} salles")
        print(f"   - {len(medecins)} médecins")
        print(f"   - {len(patients)} patients")
        print(f"   - {creneaux_count} créneaux créés")
        print(f"   - {rv_count} rendez-vous créés")

    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de la migration: {e}")
        raise
    finally:
        session.close()


def downgrade():
    """Supprime les données de test basées sur les emails"""
    connection = op.get_bind()
    Session = sessionmaker(bind=connection)
    session = Session()

    try:
        print("🗑️  Suppression des données de test...")

        # Supprimer les rendez-vous de test
        test_emails = [
            'aya.kouassi@email.com',
            'yao.kone@email.com',
            'adjoua.toure@email.com',
            'kouame.bakayoko@email.com',
            'aminata.diallo@email.com',
            'ibrahim.cisse@email.com',
            'fatou.ouattara@email.com',
            'kouadio.coulibaly@email.com',
            'koffi.yao@email.com',
            'mariam.diomande@email.com',
            'sylla.dosso@email.com',
            'ngoran.koffi@email.com',
            'euphrasie.nguessan@email.com',
            'jeanyves.bamba@email.com',
            'aya.gbaka@email.com',
            'lassina.traore@email.com'
        ]

        # Récupérer les IDs des patients de test
        patient_ids = [u.id for u in session.query(User).filter(User.email.in_(test_emails)).all()]

        # Supprimer les rendez-vous
        session.query(RendezVous).filter(RendezVous.patient_id.in_(patient_ids)).delete(synchronize_session=False)

        # Supprimer les profils patients
        session.query(PatientProfil).filter(PatientProfil.user_id.in_(patient_ids)).delete(synchronize_session=False)

        # Supprimer les patients
        session.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)

        # Supprimer les médecins de test
        medecin_emails = [
            'pierre.bernard@cliniquebodo.com',
            'sophie.lefevre@cliniquebodo.com',
            'lucas.moreau@cliniquebodo.com',
            'emma.petit@cliniquebodo.com',
            'thomas.robert@cliniquebodo.com'
        ]
        medecin_ids = [u.id for u in session.query(User).filter(User.email.in_(medecin_emails)).all()]

        # Supprimer les créneaux des médecins de test
        session.query(Creneau).filter(Creneau.medecin_id.in_(medecin_ids)).delete(synchronize_session=False)

        # Supprimer les médecins
        session.query(User).filter(User.email.in_(medecin_emails)).delete(synchronize_session=False)

        # Supprimer les secrétaires de test
        secretaire_emails = [
            'marie.dupont@cliniquebodo.com',
            'jean.martin@cliniquebodo.com'
        ]
        session.query(User).filter(User.email.in_(secretaire_emails)).delete(synchronize_session=False)

        # Supprimer les salles de test
        session.query(Salle).filter(Salle.numero.in_(['S101', 'S102', 'S103', 'S104', 'S105'])).delete(synchronize_session=False)

        session.commit()
        print("✅ Données de test supprimées avec succès !")

    except Exception as e:
        session.rollback()
        print(f"❌ Erreur lors de la suppression: {e}")
        raise
    finally:
        session.close()
