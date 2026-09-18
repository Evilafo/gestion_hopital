from flask import current_app
from hopital.utils import date_fr
from datetime import date


def register_routes(app):
    """Enregistre toutes les routes de l'application"""
    
    @app.context_processor
    def inject_globals():
        return {
            'date_fr': date_fr,
            'today': date.today(),
        }

    @app.template_filter('date_fr')
    def _date_fr_filter(value):
        return date_fr(value)
    
    # Import et enregistrement des modules de routes
    from hopital.routes import auth, patient, medecin, admin, api
    
    auth.register_routes(app)
    patient.register_routes(app)
    medecin.register_routes(app)
    admin.register_routes(app)
    api.register_routes(app)
