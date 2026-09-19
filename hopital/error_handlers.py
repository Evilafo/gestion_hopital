"""
Gestion centralisée des erreurs de l'application.
"""
import logging
from functools import wraps
from flask import jsonify, render_template, request, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timezone


class AppError(Exception):
    """Classe de base pour les erreurs de l'application."""
    def __init__(self, message: str, status_code: int = 500, payload: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv


class ValidationError(AppError):
    """Erreur de validation des données."""
    def __init__(self, message: str, payload: dict = None):
        super().__init__(message, status_code=400, payload=payload)


class AuthenticationError(AppError):
    """Erreur d'authentification."""
    def __init__(self, message: str = "Authentication failed", payload: dict = None):
        super().__init__(message, status_code=401, payload=payload)


class AuthorizationError(AppError):
    """Erreur d'autorisation."""
    def __init__(self, message: str = "Insufficient permissions", payload: dict = None):
        super().__init__(message, status_code=403, payload=payload)


class ResourceNotFoundError(AppError):
    """Ressource non trouvée."""
    def __init__(self, message: str = "Resource not found", payload: dict = None):
        super().__init__(message, status_code=404, payload=payload)


class ConflictError(AppError):
    """Erreur de conflit (ex: ressource déjà existante)."""
    def __init__(self, message: str = "Resource conflict", payload: dict = None):
        super().__init__(message, status_code=409, payload=payload)


class BusinessLogicError(AppError):
    """Erreur de logique métier."""
    def __init__(self, message: str, payload: dict = None):
        super().__init__(message, status_code=422, payload=payload)


def handle_error(error: Exception):
    """
    Handler centralisé pour toutes les erreurs.
    Retourne une réponse JSON pour les requêtes API, 
    ou une page HTML pour les requêtes web.
    """
    logger = current_app.logger
    
    # Log l'erreur
    log_error(error, logger)
    
    # Détermine si c'est une requête API
    is_api = request.path.startswith('/api/') or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']
    
    status_code = 500
    response_data = {
        'status': 'error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if isinstance(error, AppError):
        status_code = error.status_code
        response_data.update(error.to_dict())
    elif isinstance(error, HTTPException):
        status_code = error.code
        response_data['message'] = error.description
    elif isinstance(error, IntegrityError):
        status_code = 409
        response_data['message'] = 'Database integrity error'
        response_data['details'] = str(error.orig)
    elif isinstance(error, SQLAlchemyError):
        status_code = 500
        response_data['message'] = 'Database error'
        response_data['details'] = str(error)
    else:
        response_data['message'] = str(error) if str(error) else 'Internal server error'
    
    if current_app.debug:
        response_data['debug'] = {
            'type': type(error).__name__,
            'args': error.args
        }
    
    if is_api:
        return jsonify(response_data), status_code
    else:
        return render_template('errors/error.html', 
                             error=response_data, 
                             status_code=status_code), status_code


def log_error(error: Exception, logger: logging.Logger):
    """Log l'erreur avec les détails appropriés."""
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'path': request.path,
        'method': request.method,
        'ip': request.remote_addr,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if hasattr(error, 'status_code'):
        error_info['status_code'] = error.status_code
    
    if isinstance(error, AppError):
        logger.error(f"Application error: {error_info}")
    elif isinstance(error, SQLAlchemyError):
        logger.error(f"Database error: {error_info}")
    elif isinstance(error, HTTPException):
        logger.warning(f"HTTP error: {error_info}")
    else:
        logger.critical(f"Unexpected error: {error_info}", exc_info=True)


def register_error_handlers(app):
    """Enregistre tous les handlers d'erreurs sur l'application Flask."""
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return handle_error(error)
    
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return handle_error(error)
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        return handle_error(error)
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        return handle_error(error)
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        return handle_error(error)
    
    app.logger.info("Error handlers registered")


def handle_errors(f):
    """
    Décorateur pour wrapper les fonctions avec la gestion d'erreurs.
    Utile pour les routes et les services.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError:
            raise  # Laisser les erreurs d'application être gérées par les handlers
        except IntegrityError as e:
            current_app.logger.error(f"Integrity error in {f.__name__}: {str(e)}")
            raise ConflictError("Database integrity violation")
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in {f.__name__}: {str(e)}")
            raise AppError("Database operation failed")
        except Exception as e:
            current_app.logger.exception(f"Unexpected error in {f.__name__}: {str(e)}")
            raise AppError("An unexpected error occurred")
    
    return wrapped
