"""
Configuration du logging structuré pour l'application.
"""
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from pathlib import Path
import json
import sys


class JSONFormatter(logging.Formatter):
    """Formateur JSON pour les logs structurés."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Ajouter les informations de l'exception si présentes
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Ajouter les champs personnalisés
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        if hasattr(record, 'resource'):
            log_data['resource'] = record.resource
        
        return json.dumps(log_data)


class RequestContextFilter(logging.Filter):
    """Filtre pour ajouter le contexte de la requête aux logs."""
    
    def filter(self, record):
        try:
            from flask import request, g
            if request:
                record.ip_address = request.remote_addr
                record.method = request.method
                record.path = request.path
                if hasattr(g, 'user_id'):
                    record.user_id = g.user_id
                if hasattr(g, 'request_id'):
                    record.request_id = g.request_id
        except:
            pass  # Pas de contexte Flask disponible
        return True


def setup_logging(app):
    """
    Configure le logging pour l'application Flask.
    """
    # Créer le répertoire de logs s'il n'existe pas
    log_dir = Path(app.instance_path) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Niveau de log basé sur l'environnement
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # Handler pour les logs généraux (rotation quotidienne)
    general_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / 'app.log',
        when='midnight',
        interval=1,
        backupCount=30
    )
    general_handler.setLevel(log_level)
    general_handler.setFormatter(JSONFormatter())
    
    # Handler pour les erreurs (rotation quotidienne)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / 'error.log',
        when='midnight',
        interval=1,
        backupCount=30
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    # Handler pour les logs d'accès
    access_handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / 'access.log',
        when='midnight',
        interval=1,
        backupCount=30
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(JSONFormatter())
    
    # Handler pour la console (en développement)
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    # Configurer le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Supprimer les handlers existants
    root_logger.handlers.clear()
    
    # Ajouter les handlers
    root_logger.addHandler(general_handler)
    root_logger.addHandler(error_handler)
    
    # Logger spécifique pour les accès
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_handler)
    access_logger.addFilter(RequestContextFilter())
    
    # Logger spécifique pour la sécurité
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    security_logger.addHandler(general_handler)
    security_logger.addFilter(RequestContextFilter())
    
    # Logger spécifique pour la base de données
    db_logger = logging.getLogger('database')
    db_logger.setLevel(logging.WARNING)
    db_logger.addHandler(general_handler)
    
    if app.debug:
        root_logger.addHandler(console_handler)
    
    # Configurer les loggers tiers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging configured - Level: {log_level}, Log directory: {log_dir}")


def log_access(action: str, resource: str = None, details: dict = None):
    """
    Log une action d'accès/utilisateur.
    
    Args:
        action: Type d'action (ex: 'login', 'logout', 'create', 'update', 'delete')
        resource: Type de ressource (ex: 'patient', 'appointment', 'user')
        details: Détails supplémentaires
    """
    logger = logging.getLogger('access')
    log_data = {
        'action': action,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if resource:
        log_data['resource'] = resource
    
    if details:
        log_data.update(details)
    
    # Créer un record avec les attributs personnalisés
    record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, json.dumps(log_data), (), None
    )
    
    if resource:
        record.resource = resource
    record.action = action
    
    # Éviter les erreurs dans les tests
    try:
        logger.handle(record)
    except:
        pass


def log_security_event(event_type: str, details: dict = None, severity: str = 'warning'):
    """
    Log un événement de sécurité.
    
    Args:
        event_type: Type d'événement (ex: 'failed_login', 'rate_limit_exceeded', 'unauthorized_access')
        details: Détails de l'événement
        severity: Niveau de sévérité ('info', 'warning', 'error', 'critical')
    """
    logger = logging.getLogger('security')
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if details:
        log_data.update(details)
    
    level = {
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }.get(severity, logging.WARNING)
    
    record = logger.makeRecord(
        logger.name, level, '', 0, json.dumps(log_data), (), None
    )
    
    record.action = event_type
    
    try:
        logger.handle(record)
    except:
        pass


def log_database_operation(operation: str, table: str, details: dict = None):
    """
    Log une opération de base de données.
    
    Args:
        operation: Type d'opération (ex: 'insert', 'update', 'delete', 'select')
        table: Nom de la table
        details: Détails de l'opération
    """
    logger = logging.getLogger('database')
    log_data = {
        'operation': operation,
        'table': table,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    if details:
        log_data.update(details)
    
    record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, json.dumps(log_data), (), None
    )
    
    record.action = operation
    record.resource = table
    
    try:
        logger.handle(record)
    except:
        pass
