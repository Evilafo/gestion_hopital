#!/usr/bin/env python3
"""
Script de peuplement de la base de données avec des données de test
Ce script peut être exécuté indépendamment pour peupler une nouvelle base de données
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta, time
from werkzeug.security import generate_password_hash
from hopital.extensions import db
from hopital.models import User, Salle, PatientProfil, Creneau, RendezVous


def get_or_create(session, model, defaults=None, **kwargs):
    """Récupère ou crée un enregistrement de manière idempotente"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = {k: v for k, v in kwargs.items() if not isinstance(v, db.sql.expression.ClauseElement)}
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True


def seed_database():
    """Peuple la base de données avec les données de test"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
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
                salle, created = get_or_create(db.session, Salle, defaults={'nom': salle_data['nom']}, numero=salle_data['numero'])
                salles[salle_data['numero']] = salle
                if created:
                    print(f"   ✓ Salle {salle_data['numero']} créée")

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
                user = db.session.query(User).filter_by(email=sec_data['email']).first()
                if not user:
                    user = User(
                        nom=sec_data['nom'],
                        prenom=sec_data['prenom'],
                        email=sec_data['email'],
                        role=sec_data['role'],
                        contact=sec_data['contact'],
                        compte_web=sec_data['compte_web'],
                        password_hash=generate_password_hash('Secret1234')
                    )
                    db.session.add(user)
                    db.session.flush()
                    print(f"   ✓ Secrétaire {sec_data['prenom']} {sec_data['nom']} créé")

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
                user = db.session.query(User).filter_by(email=m_data['email']).first()
                if not user:
                    user = User(
                        nom=m_data['nom'],
                        prenom=m_data['prenom'],
                        email=m_data['email'],
                        role='medecin',
                        specialite=m_data['specialite'],
                        salle_id=salles[m_data['salle_num']].id,
                        contact=m_data['contact'],
                        compte_web=True,
                        password_hash=generate_password_hash('Medecin1234')
                    )
                    db.session.add(user)
                    db.session.flush()
                    print(f"   ✓ Médecin {m_data['prenom']} {m_data['nom']} créé")
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
                    'prenom': "N'Goran",
                    'email': 'ngoran.koffi@email.com',
                    'contact': '0790123456',
                    'date_naissance': date(1975, 3, 3),
                    'allergies': None,
                    'antecedents': 'Hypertension'
                },
                {
                    'nom': "N'Guessan",
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
                user = db.session.query(User).filter_by(email=p_data['email']).first()
                if not user:
                    user = User(
                        nom=p_data['nom'],
                        prenom=p_data['prenom'],
                        email=p_data['email'],
                        role='patient',
                        contact=p_data['contact'],
                        date_naissance=p_data['date_naissance'],
                        compte_web=True,
                        password_hash=generate_password_hash('Patient1234')
                    )
                    db.session.add(user)
                    db.session.flush()
                    print(f"   ✓ Patient {p_data['prenom']} {p_data['nom']} créé")
                patients.append(user)

                # Créer le profil patient
                profil, _ = get_or_create(db.session, PatientProfil, defaults={
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
                            creneau, created = get_or_create(db.session, Creneau, defaults={
                                'disponible': True
                            }, medecin_id=medecin.id, date=current_date, heure_debut=time(hour, 0), heure_fin=time(hour, 0, 30))
                            if created:
                                creneaux_count += 1

                        # Créneaux de l'après-midi (14h-18h)
                        for hour in range(14, 18):
                            creneau, created = get_or_create(db.session, Creneau, defaults={
                                'disponible': True
                            }, medecin_id=medecin.id, date=current_date, heure_debut=time(hour, 0), heure_fin=time(hour, 0, 30))
                            if created:
                                creneaux_count += 1

            print(f"   ✓ {creneaux_count} créneaux créés")

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
                creneau = db.session.query(Creneau).filter(
                    Creneau.medecin_id == medecin.id,
                    Creneau.date == rv_data['date'],
                    Creneau.heure_debut == rv_data['heure'],
                    Creneau.disponible == True
                ).first()

                if creneau:
                    rv, created = get_or_create(db.session, RendezVous, defaults={
                        'patient_id': patient.id,
                        'medecin_id': medecin.id,
                        'creneau_id': creneau.id,
                        'date': rv_data['date'],
                        'heure': rv_data['heure']
                    }, medecin_id=medecin.id, patient_id=patient.id, date=rv_data['date'], heure=rv_data['heure'])

                    if created:
                        rv.statut = 'Confirmé'
                        rv.motif = rv_data['motif']
                        creneau.disponible = False
                        rv_count += 1

            db.session.commit()

            print("✅ Peuplement terminé avec succès !")
            print(f"   - {len(salles)} salles")
            print(f"   - {len(medecins)} médecins")
            print(f"   - {len(patients)} patients")
            print(f"   - {creneaux_count} créneaux")
            print(f"   - {rv_count} rendez-vous")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors du peuplement: {e}")
            raise


if __name__ == '__main__':
    seed_database()
