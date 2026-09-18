from datetime import datetime, date, timedelta
from uuid import uuid4

MOIS_FR = [
    '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
]


def date_fr(d):
    """Formate une date en français"""
    if not d:
        return ''
    return f"{d.day} {MOIS_FR[d.month]} {d.year}"


def week_dates(start=None):
    """Génère les dates de la semaine à partir d'une date"""
    start = start or date.today()
    monday = start - timedelta(days=start.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def generate_internal_email():
    """Génère un email interne pour les patients sans compte web"""
    return f"dossier.{uuid4().hex[:10]}@interne.hopital.local"
