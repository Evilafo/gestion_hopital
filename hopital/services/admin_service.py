import csv
import io
from datetime import datetime, date
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import func
from hopital.extensions import db
from hopital.models import User, Salle, RendezVous, FileAttente
from hopital.services.patient_service import PatientService
from hopital.services.queue_service import QueueService


class AdminService:
    """Service pour la gestion administrative"""
    
    @staticmethod
    def add_personnel(data: dict) -> tuple[User, str]:
        """
        Ajoute un membre du personnel
        
        Args:
            data: Données du personnel
            
        Returns:
            Tuple (User, error_message)
        """
        # Vérifier si l'email existe déjà
        if User.query.filter_by(email=data['email']).first():
            return None, "Cet email est déjà utilisé"
        
        user = User(
            nom=data['nom'],
            prenom=data['prenom'],
            email=data['email'],
            role=data['role'],
            contact=data.get('contact'),
            specialite=data.get('specialite') if data['role'] == 'medecin' else None,
            salle_id=(data.get('salle_id') or None) if data['role'] == 'medecin' else None,
            compte_web=True
        )
        
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return user, None
    
    @staticmethod
    def update_personnel(user_id: int, data: dict) -> tuple[bool, str]:
        """
        Met à jour un membre du personnel
        
        Args:
            user_id: ID de l'utilisateur
            data: Données à mettre à jour
            
        Returns:
            Tuple (success, error_message)
        """
        user = User.query.get_or_404(user_id)
        
        # Vérifier l'email
        new_email = data['email']
        if new_email != user.email and User.query.filter_by(email=new_email).first():
            return False, "Ce nouvel email est déjà utilisé"
        
        user.nom = data['nom']
        user.prenom = data['prenom']
        user.email = new_email
        user.contact = data.get('contact')
        
        if user.role != 'admin':
            user.role = data['role']
        
        if user.role == 'medecin':
            user.specialite = data.get('specialite')
            user.salle_id = data.get('salle_id') or None
        else:
            user.specialite = None
            user.salle_id = None
        
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        return True, None
    
    @staticmethod
    def delete_personnel(user_id: int, current_user_id: int) -> tuple[bool, str]:
        """
        Supprime un membre du personnel
        
        Args:
            user_id: ID de l'utilisateur à supprimer
            current_user_id: ID de l'utilisateur connecté
            
        Returns:
            Tuple (success, error_message)
        """
        user = User.query.get_or_404(user_id)
        
        if user_id == current_user_id:
            return False, "Vous ne pouvez pas supprimer votre propre compte"
        
        if user.role == 'medecin' and RendezVous.query.filter_by(medecin_id=user_id).first():
            return False, "Impossible de supprimer ce médecin car il a des rendez-vous associés"
        
        db.session.delete(user)
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def get_personnel():
        """
        Récupère tout le personnel (médecins, secrétaires, admins)
        
        Returns:
            Query de personnel
        """
        return User.query.filter(User.role.in_(['medecin', 'secretaire', 'admin'])).options(
            joinedload(User.salle_ref)
        ).all()
    
    @staticmethod
    def add_salle(data: dict) -> tuple[Salle, str]:
        """
        Ajoute une salle
        
        Args:
            data: Données de la salle (numero, nom)
            
        Returns:
            Tuple (Salle, error_message)
        """
        numero = data['numero'].strip()
        
        if Salle.query.filter_by(numero=numero).first():
            return None, "Ce numéro de salle existe déjà"
        
        salle = Salle(
            numero=numero,
            nom=data.get('nom'),
            disponible=True
        )
        
        db.session.add(salle)
        db.session.commit()
        
        return salle, None
    
    @staticmethod
    def update_salle(salle_id: int, data: dict) -> tuple[bool, str]:
        """
        Met à jour une salle
        
        Args:
            salle_id: ID de la salle
            data: Données à mettre à jour
            
        Returns:
            Tuple (success, error_message)
        """
        salle = Salle.query.get_or_404(salle_id)
        
        salle.numero = data['numero']
        salle.nom = data.get('nom')
        
        db.session.commit()
        return True, None
    
    @staticmethod
    def delete_salle(salle_id: int) -> tuple[bool, str]:
        """
        Supprime une salle
        
        Args:
            salle_id: ID de la salle
            
        Returns:
            Tuple (success, error_message)
        """
        salle = Salle.query.get_or_404(salle_id)
        
        if salle.medecins:
            return False, "Impossible de supprimer une salle assignée"
        
        db.session.delete(salle)
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def get_salles():
        """
        Récupère toutes les salles
        
        Returns:
            Query de salles
        """
        return Salle.query.options(joinedload(Salle.medecins)).all()
    
    @staticmethod
    def get_stats() -> dict:
        """
        Récupère les statistiques pour le dashboard admin
        
        Returns:
            Dict avec toutes les statistiques
        """
        today = date.today()
        
        total_patients = User.query.filter_by(role='patient').count()
        rdv_today = RendezVous.query.filter_by(date=today).count()
        rdv_confirmes = RendezVous.query.filter_by(date=today, statut='Confirmé').count()
        en_attente = FileAttente.query.filter_by(date=today, statut_file='En Attente').count()
        en_consult = FileAttente.query.filter_by(date=today, statut_file='En Consultation').count()
        absents = FileAttente.query.filter_by(date=today, statut_file='Absent').count()
        
        total_file = FileAttente.query.filter(FileAttente.date == today).count() or 1
        no_show = round(100 * absents / max(total_file, 1), 1)
        
        salles_libres = Salle.query.filter_by(disponible=True).count()
        salles_total = Salle.query.count()
        
        # Statistiques par spécialité
        Medecin = aliased(User)
        par_specialite = db.session.query(
            Medecin.specialite, func.count(RendezVous.id)
        ).join(Medecin, RendezVous.medecin_id == Medecin.id).group_by(Medecin.specialite).all()
        
        # Occupation des salles
        occupation = []
        for salle in Salle.query.all():
            medecin_ids = [m.id for m in salle.medecins]
            occupee = False
            if medecin_ids:
                occupee = FileAttente.query.filter(
                    FileAttente.date == today,
                    FileAttente.medecin_id.in_(medecin_ids),
                    FileAttente.statut_file == 'En Consultation'
                ).count() > 0
            occupation.append({'salle': salle, 'occupee': occupee})
        
        return {
            'total_patients': total_patients,
            'rdv_today': rdv_today,
            'rdv_confirmes': rdv_confirmes,
            'en_attente': en_attente,
            'en_consult': en_consult,
            'absents': absents,
            'no_show': no_show,
            'salles_libres': salles_libres,
            'salles_total': salles_total,
            'par_specialite': par_specialite,
            'occupation': occupation,
            'date': today,
        }
    
    @staticmethod
    def export_patients() -> str:
        """
        Exporte la liste des patients en CSV
        
        Returns:
            Contenu CSV
        """
        patients = User.query.filter_by(role='patient').order_by(User.nom).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Nom', 'Prénom', 'Email', 'Téléphone', 'Naissance'])
        
        for p in patients:
            writer.writerow([p.nom, p.prenom, p.email, p.contact or '', p.date_naissance or ''])
        
        return output.getvalue()
    
    @staticmethod
    def export_appointments() -> str:
        """
        Exporte la liste des rendez-vous en CSV
        
        Returns:
            Contenu CSV
        """
        Patient = aliased(User)
        Medecin = aliased(User)
        
        rows = db.session.query(
            RendezVous, Patient, Medecin
        ).join(Patient, RendezVous.patient_id == Patient.id).join(
            Medecin, RendezVous.medecin_id == Medecin.id
        ).order_by(RendezVous.date.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Heure', 'Patient', 'Médecin', 'Statut', 'Motif'])
        
        for rv, patient, medecin in rows:
            writer.writerow([
                rv.date, rv.heure, patient.nom_complet, medecin.nom_complet, 
                rv.statut, rv.motif or ''
            ])
        
        return output.getvalue()
    
    @staticmethod
    def get_appointments(page: int = 1, per_page: int = 15, statut: str = None, 
                       date_filter: str = None):
        """
        Récupère les rendez-vous avec filtres et pagination
        
        Args:
            page: Page actuelle
            per_page: Éléments par page
            statut: Filtre par statut
            date_filter: Filtre par date
            
        Returns:
            Pagination object
        """
        Patient = aliased(User)
        Medecin = aliased(User)
        
        query = db.session.query(
            RendezVous,
            func.concat(Patient.prenom, ' ', Patient.nom).label('patient_nom'),
            func.concat(Medecin.prenom, ' ', Medecin.nom).label('medecin_nom')
        ).join(Patient, RendezVous.patient_id == Patient.id).join(
            Medecin, RendezVous.medecin_id == Medecin.id
        )
        
        if statut:
            query = query.filter(RendezVous.statut == statut)
        
        if date_filter:
            try:
                d = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(RendezVous.date == d)
            except ValueError:
                pass
        
        query = query.order_by(RendezVous.date.desc(), RendezVous.heure.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
