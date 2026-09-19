from datetime import datetime
from typing import Optional, Tuple
from flask_login import login_user
from hopital.extensions import db
from hopital.models import User
from hopital.services.patient_service import PatientService
from hopital.utils import generate_internal_email


class AuthService:
    """Service pour la gestion de l'authentification"""
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authentifie un utilisateur avec email et mot de passe
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe
            
        Returns:
            Tuple (User, error_message) - User si succès, None + message d'erreur sinon
        """
        user = User.query.filter_by(email=email.strip()).first()
        
        if not user:
            return None, "Identifiants incorrects"
        
        if not user.compte_web:
            return None, "Ce compte n'a pas d'accès web"
        
        if not user.check_password(password):
            return None, "Identifiants incorrects"
        
        return user, None
    
    @staticmethod
    def register_patient(data: dict) -> Tuple[Optional[User], Optional[str]]:
        """
        Enregistre un nouveau patient
        
        Args:
            data: Dictionnaire avec les données du patient
            
        Returns:
            Tuple (User, error_message) - User si succès, None + message d'erreur sinon
        """
        # Vérifier si l'email existe déjà
        if User.query.filter_by(email=data['email'].strip()).first():
            return None, "Cet email est déjà utilisé"
        
        # Valider la date de naissance
        try:
            date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            return None, "Date de naissance invalide"
        
        # Créer l'utilisateur
        user = User(
            nom=data['nom'].strip(),
            prenom=data['prenom'].strip(),
            email=data['email'].strip(),
            contact=data.get('contact', '').strip(),
            date_naissance=date_naissance,
            role='patient',
            compte_web=True
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Créer le profil patient
        PatientService.ensure_patient_profile(user)
        
        return user, None
    
    @staticmethod
    def create_default_admin():
        """Crée l'administrateur par défaut s'il n'existe pas"""
        if User.query.filter_by(role='admin').count() == 0:
            admin = User(
                nom='Admin', 
                prenom='Système', 
                email='admin@hopital.com',
                role='admin', 
                contact='0000000000', 
                compte_web=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            return admin
        return None
