from datetime import datetime, date, time, timedelta
from uuid import uuid4

from flask import current_app, request
from flask_mail import Message
from sqlalchemy import inspect, text, func, or_
from sqlalchemy.orm import joinedload, aliased

from hopital.extensions import db, mail
from hopital.models import (
    User, PatientProfil, Salle, Creneau, RendezVous, FileAttente, JournalAcces
)
from hopital.utils import date_fr, week_dates, generate_internal_email


def ensure_schema():
    db.create_all()
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if 'rendez_vous' in tables:
        cols = {c['name'] for c in inspector.get_columns('rendez_vous')}
        _add_column_if_missing('rendez_vous', 'motif', 'VARCHAR(255)', cols)
        _add_column_if_missing('rendez_vous', 'reminder_j1_sent', 'BOOLEAN DEFAULT 0', cols)
        _add_column_if_missing('rendez_vous', 'reminder_h2_sent', 'BOOLEAN DEFAULT 0', cols)
    if 'user' in tables:
        cols = {c['name'] for c in inspector.get_columns('user')}
        _add_column_if_missing('user', 'compte_web', 'BOOLEAN DEFAULT 1', cols)


def _add_column_if_missing(table, column, ddl, existing):
    if column in existing:
        return
    db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}'))
    db.session.commit()


def log_acces(user_id, action, patient_id=None, details=None):
    db.session.add(JournalAcces(
        user_id=user_id,
        patient_id=patient_id,
        action=action,
        details=details
    ))
    db.session.commit()


# Fonctions de compatibilité - Redirection vers les nouveaux services
def ensure_patient_profile(user):
    from hopital.services.patient_service import PatientService
    return PatientService.ensure_patient_profile(user)


def sync_file_du_jour(jour=None):
    from hopital.services.queue_service import QueueService
    return QueueService.sync_file_du_jour(jour)


def book_slot(slot_id, patient_id, motif=None):
    from hopital.services.appointment_service import AppointmentService
    return AppointmentService.book_slot(slot_id, patient_id, motif)


def liberer_creneau(rv):
    if rv.creneau:
        rv.creneau.disponible = True
    fa = FileAttente.query.filter_by(rendez_vous_id=rv.id).first()
    if fa:
        fa.statut_file = 'Annulé'
    rv.statut = 'Annulé'


def consultation_en_cours(medecin_id, jour=None):
    from hopital.services.queue_service import QueueService
    return QueueService.get_consultation_en_cours(medecin_id, jour)


def position_file(patient_id, jour=None):
    from hopital.services.queue_service import QueueService
    return QueueService.get_patient_position(patient_id, jour)


def file_payload(jour=None):
    from hopital.services.queue_service import QueueService
    return QueueService.get_file_payload(jour)


def stats_secretariat():
    from hopital.services.admin_service import AdminService
    return AdminService.get_stats()


def send_reminders():
    now = datetime.now()
    tomorrow = date.today() + timedelta(days=1)
    sent = 0
    errors = []

    j1 = RendezVous.query.options(joinedload(RendezVous.patient), joinedload(RendezVous.medecin)).filter(
        RendezVous.date == tomorrow,
        RendezVous.statut == 'Confirmé',
        or_(RendezVous.reminder_j1_sent.is_(False), RendezVous.reminder_j1_sent.is_(None))
    ).all()

    h2 = RendezVous.query.options(joinedload(RendezVous.patient), joinedload(RendezVous.medecin)).filter(
        RendezVous.date == date.today(),
        RendezVous.statut == 'Confirmé',
        or_(RendezVous.reminder_h2_sent.is_(False), RendezVous.reminder_h2_sent.is_(None))
    ).all()

    def _try_send(rv, kind):
        nonlocal sent
        if not rv.patient or not rv.patient.email or not rv.patient.compte_web:
            return
        if rv.patient.email.endswith('@interne.hopital.local'):
            return
        subject = 'Rappel de rendez-vous' if kind == 'j1' else 'Votre rendez-vous est dans 2 heures'
        body = (
            f"Bonjour {rv.patient.prenom},\n\n"
            f"Rappel : rendez-vous le {date_fr(rv.date)} à {rv.heure.strftime('%H:%M')} "
            f"avec le Dr {rv.medecin.nom}.\n"
        )
        if current_app.config.get('MAIL_SERVER'):
            try:
                mail.send(Message(
                    subject=subject,
                    recipients=[rv.patient.email],
                    body=body
                ))
            except Exception as exc:
                errors.append(str(exc))
                return
        if kind == 'j1':
            rv.reminder_j1_sent = True
        else:
            rv.reminder_h2_sent = True
        sent += 1

    for rv in j1:
        _try_send(rv, 'j1')

    for rv in h2:
        rdv_dt = datetime.combine(rv.date, rv.heure)
        if timedelta(0) <= (rdv_dt - now) <= timedelta(hours=2):
            _try_send(rv, 'h2')

    db.session.commit()
    return sent, errors
