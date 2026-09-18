from datetime import date
from functools import wraps
from flask import jsonify
from flask_login import login_required, current_user
from hopital.extensions import limiter
from hopital.services.queue_service import QueueService


def role_required(*roles):
    """Décorateur pour vérifier les rôles utilisateur"""
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'error': 'Accès non autorisé'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return decorator


def register_routes(app):
    """Enregistre les routes API"""

    @app.route('/api/queue-today')
    @role_required('secretaire', 'admin', 'medecin')
    @limiter.limit("500 per hour")
    def api_queue_today():
        payload = QueueService.get_file_payload()
        return jsonify({
            'date': date.today().isoformat(),
            'medecins': [
                {
                    'id': block['medecin'].id,
                    'nom': block['medecin'].nom_complet,
                    'specialite': block['medecin'].specialite,
                    'salle': block['salle'],
                    'patients': [
                        {
                            'id': p.id,
                            'patient_id': p.patient_id,
                            'nom': p.patient.nom_complet if p.patient else '',
                            'heure': p.heure_rendezvous.strftime('%H:%M'),
                            'statut': p.statut_file,
                            'ordre': p.ordre
                        } for p in block['patients']
                    ]
                } for block in payload
            ]
        })
