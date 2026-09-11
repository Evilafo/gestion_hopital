from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import joinedload
from hopital.extensions import db
from hopital.models import User, Creneau, RendezVous, FileAttente, NoteConsultation
from hopital.services.queue_service import QueueService
import os
from werkzeug.utils import secure_filename
from flask import current_app


class MedecinService:
    """Service pour la gestion des médecins"""
    
    @staticmethod
    def add_slot(medecin_id: int, date_slot: date, heure_debut: time, 
                 heure_fin: time) -> tuple[Creneau, str]:
        """
        Ajoute un créneau pour un médecin
        
        Args:
            medecin_id: ID du médecin
            date_slot: Date du créneau
            heure_debut: Heure de début
            heure_fin: Heure de fin
            
        Returns:
            Tuple (Creneau, error_message) - Creneau si succès, None + message d'erreur sinon
        """
        if heure_fin <= heure_debut:
            return None, "L'heure de fin doit être après l'heure de début"
        
        # Vérifier les conflits
        existing = Creneau.query.filter(
            Creneau.medecin_id == medecin_id,
            Creneau.date == date_slot,
            Creneau.heure_debut < heure_fin,
            Creneau.heure_fin > heure_debut
        ).first()
        
        if existing:
            return None, "Conflit avec un créneau existant"
        
        creneau = Creneau(
            medecin_id=medecin_id,
            date=date_slot,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
            disponible=True
        )
        
        db.session.add(creneau)
        db.session.commit()
        
        return creneau, None
    
    @staticmethod
    def delete_slot(slot_id: int, medecin_id: int) -> tuple[bool, str]:
        """
        Supprime un créneau
        
        Args:
            slot_id: ID du créneau
            medecin_id: ID du médecin (pour vérification)
            
        Returns:
            Tuple (success, error_message)
        """
        slot = db.session.get(Creneau, slot_id)
        
        if not slot:
            return False, "Créneau introuvable"
        
        if slot.medecin_id != medecin_id:
            return False, "Ce créneau ne vous appartient pas"
        
        if not slot.disponible:
            return False, "Impossible de supprimer un créneau réservé"
        
        db.session.delete(slot)
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def get_medecin_slots(medecin_id: int, start_date: date = None, 
                         end_date: date = None, available_only: bool = False):
        """
        Récupère les créneaux d'un médecin
        
        Args:
            medecin_id: ID du médecin
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            available_only: Uniquement les créneaux disponibles
            
        Returns:
            Query de créneaux
        """
        query = Creneau.query.filter(Creneau.medecin_id == medecin_id)
        
        if start_date:
            query = query.filter(Creneau.date >= start_date)
        
        if end_date:
            query = query.filter(Creneau.date <= end_date)
        
        if available_only:
            query = query.filter(Creneau.disponible.is_(True))
        
        return query.order_by(Creneau.date, Creneau.heure_debut)
    
    @staticmethod
    def get_medecin_dashboard_data(medecin_id: int) -> dict:
        """
        Récupère les données pour le dashboard médecin
        
        Args:
            medecin_id: ID du médecin
            
        Returns:
            Dict avec today_patients, future_slots, past_appointments, etc.
        """
        today = date.today()
        QueueService.sync_file_du_jour(today)
        
        today_patients = FileAttente.query.options(joinedload(FileAttente.patient)).filter(
            FileAttente.medecin_id == medecin_id,
            FileAttente.date == today
        ).order_by(FileAttente.ordre, FileAttente.heure_rendezvous).all()
        
        future_slots = Creneau.query.filter(
            Creneau.medecin_id == medecin_id,
            Creneau.date >= today
        ).order_by(Creneau.date, Creneau.heure_debut).all()
        
        past_appointments = RendezVous.query.options(joinedload(RendezVous.patient)).filter(
            RendezVous.medecin_id == medecin_id,
            RendezVous.date < today
        ).order_by(RendezVous.date.desc()).limit(15).all()
        
        from hopital.utils import week_dates
        week_days = week_dates(today)
        week_slots = MedecinService._slots_by_day(medecin_id, week_days)
        
        return {
            'today_patients': today_patients,
            'future_slots': future_slots,
            'past_appointments': past_appointments,
            'date_du_jour': today,
            'week_days': week_days,
            'week_slots': week_slots
        }
    
    @staticmethod
    def _slots_by_day(medecin_id: int, days: list) -> dict:
        """
        Groupe les créneaux par jour
        
        Args:
            medecin_id: ID du médecin
            days: Liste de dates
            
        Returns:
            Dict {date: [creneaux]}
        """
        slots = Creneau.query.filter(
            Creneau.medecin_id == medecin_id,
            Creneau.date.in_(days)
        ).order_by(Creneau.heure_debut).all()
        
        grouped = {d: [] for d in days}
        for s in slots:
            grouped.setdefault(s.date, []).append(s)
        
        return grouped
    
    @staticmethod
    def save_consultation_note(rdv_id: int, medecin_id: int, data: dict, 
                               document=None) -> tuple[NoteConsultation, str]:
        """
        Enregistre une note de consultation
        
        Args:
            rdv_id: ID du rendez-vous
            medecin_id: ID du médecin
            data: Données de la note (motif, diagnostic, ordonnance, notes)
            document: Fichier document (optionnel)
            
        Returns:
            Tuple (NoteConsultation, error_message)
        """
        rdv = RendezVous.query.options(
            joinedload(RendezVous.patient), joinedload(RendezVous.note)
        ).filter_by(id=rdv_id).first()
        
        if not rdv:
            return None, "Rendez-vous introuvable"
        
        if rdv.medecin_id != medecin_id:
            return None, "Accès non autorisé"
        
        note = rdv.note or NoteConsultation(rendez_vous_id=rdv.id, medecin_id=medecin_id)
        
        note.motif = data.get('motif')
        note.diagnostic = data.get('diagnostic')
        note.ordonnance = data.get('ordonnance')
        note.notes = data.get('notes')
        
        # Gestion du document
        if document and document.filename:
            folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(folder, exist_ok=True)
            filename = secure_filename(f"{rdv.id}_{document.filename}")
            document.save(os.path.join(folder, filename))
            note.document_path = filename
        
        if not rdv.note:
            db.session.add(note)
        
        db.session.commit()
        
        return note, None
    
    @staticmethod
    def get_medecins_by_specialite(specialite: str = None):
        """
        Récupère les médecins par spécialité
        
        Args:
            specialite: Filtre par spécialité (optionnel)
            
        Returns:
            Query de médecins
        """
        query = User.query.filter_by(role='medecin')
        
        if specialite:
            query = query.filter(User.specialite == specialite)
        
        return query.order_by(User.nom, User.prenom)
    
    @staticmethod
    def get_specialites():
        """
        Récupère la liste des spécialités médicales
        
        Returns:
            Liste de spécialités
        """
        return [s[0] for s in db.session.query(User.specialite).filter(
            User.role == 'medecin', User.specialite.isnot(None)
        ).distinct().all()]
