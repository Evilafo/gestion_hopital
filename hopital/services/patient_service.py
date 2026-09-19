from typing import Optional, Tuple
from hopital.extensions import db
from hopital.models import User, PatientProfil


class PatientService:
    """Service pour la gestion des patients"""
    
    @staticmethod
    def ensure_patient_profile(user: User) -> Optional[PatientProfil]:
        """
        Assure qu'un patient a un profil patient, le crée si nécessaire
        
        Args:
            user: Utilisateur de type patient
            
        Returns:
            PatientProfil: Le profil du patient
        """
        if user.role != 'patient':
            return None
        
        if not user.profil_patient:
            profil = PatientProfil(
                user_id=user.id,
                numero_dossier=f"DOS-{user.id:06d}"
            )
            db.session.add(profil)
            db.session.commit()
            db.session.refresh(user)
        
        return user.profil_patient
    
    @staticmethod
    def update_patient_profile(user: User, data: dict) -> Tuple[bool, Optional[str]]:
        """
        Met à jour le profil d'un patient
        
        Args:
            user: Utilisateur patient
            data: Données à mettre à jour
            
        Returns:
            Tuple (success, error_message)
        """
        try:
            # Mise à jour des informations de base
            if 'nom' in data:
                user.nom = data['nom']
            if 'prenom' in data:
                user.prenom = data['prenom']
            if 'contact' in data:
                user.contact = data['contact']
            if 'date_naissance' in data and data['date_naissance']:
                from datetime import datetime
                user.date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
            
            # Mise à jour du mot de passe si fourni
            if 'password' in data and data['password']:
                if data.get('password') != data.get('password_confirm'):
                    return False, "Les mots de passe ne correspondent pas"
                user.set_password(data['password'])
                user.compte_web = True
            
            # Mise à jour du profil patient
            PatientService.ensure_patient_profile(user)
            if user.profil_patient:
                if 'allergies' in data:
                    user.profil_patient.allergies = data['allergies']
                if 'antecedents' in data:
                    user.profil_patient.antecedents = data['antecedents']
                if 'notes_internes' in data:
                    user.profil_patient.notes_internes = data['notes_internes']
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def search_patients(query: Optional[str] = None, page: int = 1, per_page: int = 12):
        """
        Recherche des patients avec pagination
        
        Args:
            query: Terme de recherche (nom, prénom, email, téléphone)
            page: Page actuelle
            per_page: Nombre d'éléments par page
            
        Returns:
            Pagination object
        """
        from sqlalchemy import or_
        
        q = User.query.filter_by(role='patient')
        
        if query and query.strip():
            like = f'%{query.strip()}%'
            q = q.filter(or_(
                User.nom.ilike(like),
                User.prenom.ilike(like),
                User.contact.ilike(like),
                User.email.ilike(like)
            ))
            
            # Recherche par date de naissance si format DD/MM/YYYY
            if query.count('/') == 2:
                try:
                    from datetime import datetime
                    dn = datetime.strptime(query, '%d/%m/%Y').date()
                    q = User.query.filter_by(role='patient', date_naissance=dn)
                except ValueError:
                    pass
        
        return q.order_by(User.nom, User.prenom).paginate(page=page, per_page=per_page, error_out=False)
