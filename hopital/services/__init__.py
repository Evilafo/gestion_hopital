from hopital.services.auth_service import AuthService
from hopital.services.patient_service import PatientService
from hopital.services.medecin_service import MedecinService
from hopital.services.admin_service import AdminService
from hopital.services.appointment_service import AppointmentService
from hopital.services.queue_service import QueueService

# Import des fonctions utilitaires pour compatibilité
from hopital.utils import date_fr, week_dates, generate_internal_email

# Wrapper function pour compatibilité avec les tests
def book_slot(slot_id: int, patient_id: int, motif: str = None):
    """Wrapper pour AppointmentService.book_slot"""
    return AppointmentService.book_slot(slot_id, patient_id, motif)

__all__ = [
    'AuthService',
    'PatientService', 
    'MedecinService',
    'AdminService',
    'AppointmentService',
    'QueueService',
    'date_fr',
    'week_dates',
    'generate_internal_email',
    'book_slot'
]
