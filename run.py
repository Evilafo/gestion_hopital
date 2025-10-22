#!/usr/bin/env python3
"""
Script de démarrage pour l'application de gestion d'hôpital
"""

import os
from app import app, db, User, Salle

# --- Fonctions d'initialisation des données ---
def create_admin_user():
    """Crée un utilisateur administrateur par défaut et des salles s'ils n'existent pas."""
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
    
    # Crée quelques salles de consultation par défaut si la table est vide
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
    """Crée un médecin de test par défaut s'il n'en existe aucun."""
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

# --- Point d'entrée principal du script ---
if __name__ == '__main__':
    # 'app.app_context()' est nécessaire pour que Flask et SQLAlchemy sachent à quelle application
    # les opérations de base de données se rapportent.
    with app.app_context():
        # Crée toutes les tables définies dans les modèles SQLAlchemy (User, Salle, etc.)
        # si elles n'existent pas déjà dans la base de données. C'est la commande
        # qui transforme vos modèles Python en structure de base de données réelle.
        db.create_all()
        print("Base de données initialisée")
        
        # Appelle les fonctions pour créer les données initiales (admin, médecin, salles)
        create_admin_user()
        create_sample_medecin()
        
        # Affiche des informations utiles dans la console au démarrage
        print("\n" + "="*50)
        print("APPLICATION DE GESTION D'HOPITAL")
        print("="*50)
        print("Accès administrateur: admin@hopital.com / admin123")
        print("Accès médecin test: jean.dupont@hopital.com / medecin123")
        print("URL: http://localhost:5003")
        print("="*50 + "\n")
    
    # Démarre le serveur de développement Flask, accessible sur toutes les interfaces réseau (0.0.0.0)
    app.run(debug=True, host='0.0.0.0', port=5003)
