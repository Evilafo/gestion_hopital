from datetime import datetime, date, timedelta
from flask import current_app, request
from flask_mail import Message
from sqlalchemy import inspect, text, or_
from sqlalchemy.orm import joinedload, aliased

from hopital.extensions import db, mail
from hopital.models import (
    User, PatientProfil, Salle, Creneau, RendezVous, FileAttente, JournalAcces
)
from hopital.utils import date_fr


def ensure_schema():
    """Crée les tables - Avec Alembic, utilisez plutôt les migrations"""
    # En production, utilisez 'flask db upgrade' pour les migrations
    # Pour le développement, nous pouvons créer les tables si elles n'existent pas
    db.create_all()


def log_acces(user_id, action, patient_id=None, details=None):
    """Enregistre un accès dans le journal"""
    db.session.add(JournalAcces(
        user_id=user_id,
        patient_id=patient_id,
        action=action,
        details=details
    ))
    db.session.commit()


def send_reminders():
    """Envoie les rappels de rendez-vous par email"""
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


def liberer_creneau(rv):
    """Libère un créneau et annule le rendez-vous associé"""
    if rv.creneau:
        rv.creneau.disponible = True
    fa = FileAttente.query.filter_by(rendez_vous_id=rv.id).first()
    if fa:
        fa.statut_file = 'Annulé'
    rv.statut = 'Annulé'
