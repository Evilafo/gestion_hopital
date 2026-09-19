from datetime import date, datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from hopital.extensions import db
from hopital.models import User, Creneau, RendezVous, FileAttente
from hopital.services.queue_service import QueueService


class AppointmentService:
    """Service pour la gestion des rendez-vous"""
    
    @staticmethod
    def book_slot(slot_id: int, patient_id: int, motif: Optional[str] = None) -> Tuple[Optional[RendezVous], Optional[str]]:
        """
        Réserve un créneau pour un patient
        
        Args:
            slot_id: ID du créneau
            patient_id: ID du patient
            motif: Motif du rendez-vous
            
        Returns:
            Tuple (RendezVous, error_message) - RendezVous si succès, None + message d'erreur sinon
        """
        slot = Creneau.query.with_for_update().filter_by(id=slot_id).first()
        
        if not slot or not slot.disponible:
            return None, "Ce créneau n'est plus disponible"
        
        # Vérifier si le patient a déjà un rendez-vous à cette heure
        existing = RendezVous.query.filter_by(
            patient_id=patient_id,
            date=slot.date,
            heure=slot.heure_debut,
            statut='Confirmé'
        ).first()
        
        if existing:
            return None, "Vous avez déjà un rendez-vous à cette heure"
        
        # Créer le rendez-vous
        rv = RendezVous(
            patient_id=patient_id,
            medecin_id=slot.medecin_id,
            creneau_id=slot.id,
            date=slot.date,
            heure=slot.heure_debut,
            statut='Confirmé',
            motif=motif
        )
        
        slot.disponible = False
        db.session.add(rv)
        db.session.commit()
        
        # Synchroniser la file d'attente si c'est aujourd'hui
        if slot.date == date.today():
            QueueService.sync_file_du_jour(slot.date)
        
        return rv, None
    
    @staticmethod
    def cancel_appointment(rv_id: int) -> Tuple[bool, Optional[str]]:
        """
        Annule un rendez-vous
        
        Args:
            rv_id: ID du rendez-vous
            
        Returns:
            Tuple (success, error_message)
        """
        rv = db.session.get(RendezVous, rv_id)
        
        if not rv:
            return False, "Rendez-vous introuvable"
        
        if rv.statut != 'Confirmé':
            return False, "Ce rendez-vous ne peut plus être annulé"
        
        # Libérer le créneau
        if rv.creneau:
            rv.creneau.disponible = True
        
        # Mettre à jour la file d'attente
        fa = FileAttente.query.filter_by(rendez_vous_id=rv.id).first()
        if fa:
            fa.statut_file = 'Annulé'
        
        rv.statut = 'Annulé'
        db.session.commit()
        
        return True, None
    
    @staticmethod
    def reschedule_appointment(rv_id: int, new_slot_id: int) -> Tuple[bool, Optional[str]]:
        """
        Reprogramme un rendez-vous
        
        Args:
            rv_id: ID du rendez-vous existant
            new_slot_id: ID du nouveau créneau
            
        Returns:
            Tuple (success, error_message)
        """
        rv = RendezVous.query.options(joinedload(RendezVous.medecin)).filter_by(id=rv_id).first()
        
        if not rv:
            return False, "Rendez-vous introuvable"
        
        if rv.statut != 'Confirmé':
            return False, "Modification impossible"
        
        new_slot = Creneau.query.with_for_update().filter_by(id=new_slot_id).first()
        
        if not new_slot or not new_slot.disponible:
            return False, "Créneau indisponible"
        
        # Libérer l'ancien créneau
        if rv.creneau:
            rv.creneau.disponible = True
        
        # Réserver le nouveau créneau
        new_slot.disponible = False
        rv.creneau_id = new_slot.id
        rv.medecin_id = new_slot.medecin_id
        rv.date = new_slot.date
        rv.heure = new_slot.heure_debut
        
        # Mettre à jour la file d'attente
        fa = FileAttente.query.filter_by(rendez_vous_id=rv.id).first()
        if fa:
            db.session.delete(fa)
        
        db.session.commit()
        
        # Synchroniser la file d'attente si c'est aujourd'hui
        if new_slot.date == date.today():
            QueueService.sync_file_du_jour()
        
        return True, None
    
    @staticmethod
    def get_available_slots(medecin_id: Optional[int] = None, specialite: Optional[str] = None, 
                           start_date: Optional[date] = None, end_date: Optional[date] = None):
        """
        Récupère les créneaux disponibles
        
        Args:
            medecin_id: Filtre par médecin (optionnel)
            specialite: Filtre par spécialité (optionnel)
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            
        Returns:
            Query de créneaux disponibles
        """
        query = Creneau.query.filter(
            Creneau.date >= date.today(),
            Creneau.disponible.is_(True)
        )
        
        if medecin_id:
            query = query.filter(Creneau.medecin_id == medecin_id)
        
        if specialite:
            query = query.join(User, Creneau.medecin_id == User.id).filter(
                User.specialite == specialite
            )
        
        if start_date:
            query = query.filter(Creneau.date >= start_date)
        
        if end_date:
            query = query.filter(Creneau.date <= end_date)
        
        return query.order_by(Creneau.date, Creneau.heure_debut)
    
    @staticmethod
    def get_patient_appointments(patient_id: int, upcoming: bool = True, limit: Optional[int] = None) -> List[RendezVous]:
        """
        Récupère les rendez-vous d'un patient
        
        Args:
            patient_id: ID du patient
            upcoming: True pour les rendez-vous à venir, False pour les passés
            limit: Limite de résultats (optionnel)
            
        Returns:
            Liste de rendez-vous
        """
        query = RendezVous.query.options(joinedload(RendezVous.medecin)).filter(
            RendezVous.patient_id == patient_id
        )
        
        if upcoming:
            query = query.filter(
                RendezVous.date >= date.today(),
                RendezVous.statut == 'Confirmé'
            ).order_by(RendezVous.date, RendezVous.heure)
        else:
            query = query.filter(
                or_(
                    RendezVous.date < date.today(),
                    RendezVous.statut.in_(['Terminé', 'Annulé'])
                )
            ).order_by(RendezVous.date.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
