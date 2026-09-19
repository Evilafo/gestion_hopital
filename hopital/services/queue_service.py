from datetime import date, datetime, timedelta
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import joinedload
from hopital.extensions import db
from hopital.models import RendezVous, FileAttente, User


class QueueService:
    """Service pour la gestion de la file d'attente"""
    
    @staticmethod
    def sync_file_du_jour(jour: Optional[date] = None) -> None:
        """
        Synchronise la file d'attente pour un jour donné
        
        Args:
            jour: Date à synchroniser (aujourd'hui par défaut)
        """
        jour = jour or date.today()
        
        rdvs = RendezVous.query.filter(
            RendezVous.date == jour,
            RendezVous.statut == 'Confirmé'
        ).order_by(RendezVous.medecin_id, RendezVous.heure).all()
        
        for rdv in rdvs:
            fa = FileAttente.query.filter_by(rendez_vous_id=rdv.id).first()
            if not fa:
                db.session.add(FileAttente(
                    rendez_vous_id=rdv.id,
                    patient_id=rdv.patient_id,
                    medecin_id=rdv.medecin_id,
                    date=jour,
                    heure_rendezvous=rdv.heure,
                    statut_file='Non arrivé',
                    ordre=0
                ))
        
        db.session.commit()
        QueueService._recompute_ordre(jour)
    
    @staticmethod
    def _recompute_ordre(jour: date):
        """
        Recalcule l'ordre de la file d'attente pour un jour donné
        
        Args:
            jour: Date concernée
        """
        medecin_ids = [
            row[0] for row in db.session.query(FileAttente.medecin_id)
            .filter(FileAttente.date == jour).distinct()
        ]
        
        for medecin_id in medecin_ids:
            items = FileAttente.query.filter_by(date=jour, medecin_id=medecin_id).order_by(
                FileAttente.heure_rendezvous, FileAttente.id
            ).all()
            
            for i, item in enumerate(items, start=1):
                item.ordre = i
        
        db.session.commit()
    
    @staticmethod
    def get_patient_position(patient_id: int, jour: Optional[date] = None) -> Optional[Dict]:
        """
        Récupère la position d'un patient dans la file d'attente
        
        Args:
            patient_id: ID du patient
            jour: Date concernée (aujourd'hui par défaut)
            
        Returns:
            Dict avec 'file' et 'rang' (None si pas en attente)
        """
        jour = jour or date.today()
        
        fa = FileAttente.query.filter_by(
            patient_id=patient_id,
            date=jour
        ).filter(FileAttente.statut_file.in_(['Non arrivé', 'En Attente', 'En Consultation'])).first()
        
        if not fa:
            return None
        
        avant = FileAttente.query.filter(
            FileAttente.medecin_id == fa.medecin_id,
            FileAttente.date == jour,
            FileAttente.statut_file == 'En Attente',
            FileAttente.ordre < (fa.ordre or 0)
        ).count()
        
        rang = avant + 1 if fa.statut_file == 'En Attente' else None
        
        return {'file': fa, 'rang': rang}
    
    @staticmethod
    def get_file_payload(jour: Optional[date] = None) -> List[Dict]:
        """
        Récupère les données de la file d'attente pour l'affichage
        
        Args:
            jour: Date concernée (aujourd'hui par défaut)
            
        Returns:
            Liste de dicts avec medecin, salle, patients
        """
        jour = jour or date.today()
        QueueService.sync_file_du_jour(jour)
        
        medecins = User.query.filter(
            User.role == 'medecin',
            User.id.in_(db.session.query(FileAttente.medecin_id).filter(FileAttente.date == jour))
        ).options(joinedload(User.salle_ref)).all()
        
        data = []
        for medecin in medecins:
            patients = FileAttente.query.options(
                joinedload(FileAttente.patient)
            ).filter(
                FileAttente.medecin_id == medecin.id,
                FileAttente.date == jour
            ).order_by(FileAttente.ordre, FileAttente.heure_rendezvous).all()
            
            data.append({
                'medecin': medecin,
                'salle': medecin.salle_ref.numero if medecin.salle_ref else 'Non assignée',
                'patients': patients
            })
        
        return data
    
    @staticmethod
    def check_in_patient(file_id: int) -> Tuple[bool, Optional[str]]:
        """
        Enregistre l'arrivée d'un patient
        
        Args:
            file_id: ID de l'entrée dans la file
            
        Returns:
            Tuple (success, error_message)
        """
        fa = db.session.get(FileAttente, file_id)
        
        if not fa:
            return False, "File introuvable"
        
        if fa.date != date.today():
            return False, "Le check-in n'est possible que le jour du rendez-vous"
        
        fa.statut_file = 'En Attente'
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def start_consultation(file_id: int, medecin_id: int) -> Tuple[bool, Optional[str]]:
        """
        Démarre une consultation
        
        Args:
            file_id: ID de l'entrée dans la file
            medecin_id: ID du médecin
            
        Returns:
            Tuple (success, error_message)
        """
        fa = db.session.get(FileAttente, file_id)
        
        if not fa or fa.medecin_id != medecin_id:
            return False, "File introuvable"
        
        ongoing = QueueService.get_consultation_en_cours(medecin_id)
        if ongoing and ongoing.id != fa.id:
            return False, "Terminez d'abord la consultation en cours"
        
        fa.statut_file = 'En Consultation'
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def end_consultation(file_id: int) -> Tuple[bool, Optional[str]]:
        """
        Termine une consultation
        
        Args:
            file_id: ID de l'entrée dans la file
            
        Returns:
            Tuple (success, error_message)
        """
        fa = db.session.get(FileAttente, file_id)
        
        if not fa:
            return False, "File introuvable"
        
        fa.statut_file = 'Terminé'
        fa.rendez_vous.statut = 'Terminé'
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def get_consultation_en_cours(medecin_id: int, jour: Optional[date] = None) -> Optional[FileAttente]:
        """
        Récupère la consultation en cours pour un médecin
        
        Args:
            medecin_id: ID du médecin
            jour: Date concernée (aujourd'hui par défaut)
            
        Returns:
            FileAttente ou None
        """
        jour = jour or date.today()
        return FileAttente.query.filter_by(
            medecin_id=medecin_id,
            date=jour,
            statut_file='En Consultation'
        ).first()
    
    @staticmethod
    def move_patient_in_queue(file_id: int, direction: str) -> Tuple[bool, Optional[str]]:
        """
        Déplace un patient dans la file d'attente
        
        Args:
            file_id: ID de l'entrée dans la file
            direction: 'up' ou 'down'
            
        Returns:
            Tuple (success, error_message)
        """
        fa = db.session.get(FileAttente, file_id)
        
        if not fa:
            return False, "File introuvable"
        
        siblings = FileAttente.query.filter_by(
            medecin_id=fa.medecin_id, date=fa.date
        ).order_by(FileAttente.ordre).all()
        
        idx = next((i for i, x in enumerate(siblings) if x.id == fa.id), None)
        if idx is None:
            return False, "Position introuvable"
        
        swap_with = idx - 1 if direction == 'up' else idx + 1
        if 0 <= swap_with < len(siblings):
            siblings[idx].ordre, siblings[swap_with].ordre = siblings[swap_with].ordre, siblings[idx].ordre
            db.session.commit()
            return True, None
        
        return False, "Déplacement impossible"
    
    @staticmethod
    def mark_patient_absent(file_id: int) -> Tuple[bool, Optional[str]]:
        """
        Marque un patient comme absent
        
        Args:
            file_id: ID de l'entrée dans la file
            
        Returns:
            Tuple (success, error_message)
        """
        fa = db.session.get(FileAttente, file_id)
        
        if not fa:
            return False, "File introuvable"
        
        fa.statut_file = 'Absent'
        
        if fa.rendez_vous and fa.rendez_vous.creneau:
            fa.rendez_vous.creneau.disponible = True
        
        db.session.commit()
        return True, None
    
    @staticmethod
    def delay_patient(file_id: int, minutes: int = 15) -> Tuple[bool, Optional[str]]:
        """
        Enregistre un retard pour un patient
        
        Args:
            file_id: ID de l'entrée dans la file
            minutes: Nombre de minutes de retard
            
        Returns:
            Tuple (success, error_message)
        """
        fa = db.session.get(FileAttente, file_id)
        
        if not fa or not fa.heure_rendezvous:
            return False, "File introuvable ou sans heure"
        
        dt = datetime.combine(date.today(), fa.heure_rendezvous) + timedelta(minutes=minutes)
        fa.heure_rendezvous = dt.time()
        db.session.commit()
        
        QueueService.sync_file_du_jour()
        return True, None
