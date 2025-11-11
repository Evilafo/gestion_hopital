#!/usr/bin/env python3
"""
Script de démarrage pour l'application de gestion hospitalière
"""

import os
from app import app, db, User, Salle

def create_admin_user():
    """Crée un utilisateur administrateur par défaut s'il n'existe pas"""
    admin_exists = User.query.filter_by(role='admin').first()
    if not admin_exists:
        admin = User(
            nom='Admin',
            prenom='Système',
            email='admin@hopital.com',
            role='admin',
            contact='0000000000'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("Utilisateur administrateur créé (admin@hopital.com / admin123)")
    
    # Créer quelques salles par défaut
    if Salle.query.count() == 0:
        salles = [
            Salle(numero='S001', nom='Salle de Consultation 1'),
            Salle(numero='S002', nom='Salle de Consultation 2'),
            Salle(numero='S003', nom='Salle de Consultation 3'),
            Salle(numero='S004', nom='Salle de Consultation 4'),
        ]
        for salle in salles:
            db.session.add(salle)
        print("Salles par défaut créées")
    
    db.session.commit()

def create_sample_medecin():
    """Crée un médecin de test s'il n'existe pas"""
    medecin_exists = User.query.filter_by(role='medecin').first()
    if not medecin_exists:
        salle = Salle.query.first()
        medecin = User(
            nom='Dupont',
            prenom='Jean',
            email='jean.dupont@hopital.com',
            role='medecin',
            contact='0123456789',
            specialite='Médecine Générale',
            salle_id=salle.id if salle else None
        )
        medecin.set_password('medecin123')
        db.session.add(medecin)
        print("Médecin de test créé (jean.dupont@hopital.com / medecin123)")
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        # Créer toutes les tables
        db.create_all()
        print("Base de données initialisée")
        
        # Créer les utilisateurs par défaut
        create_admin_user()
        create_sample_medecin()
        
        print("\n" + "="*50)
        print("APPLICATION DE GESTION HOSPITALIÈRE")
        print("="*50)
        print("Accès administrateur: admin@hopital.com / admin123")
        print("Accès médecin test: jean.dupont@hopital.com / medecin123")
        print("URL: http://localhost:5002")
        print("="*50 + "\n")
    
    # Démarrer l'application
    app.run(debug=True, host='0.0.0.0', port=5002)
