import re
from typing import Tuple, Optional


class PasswordValidator:
    """Validateur de mots de passe sécurisés"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, Optional[str]]:
        """
        Valide un mot de passe selon les critères de sécurité
        
        Args:
            password: Mot de passe à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not password:
            return False, "Le mot de passe ne peut pas être vide"
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {PasswordValidator.MIN_LENGTH} caractères"
        
        if len(password) > PasswordValidator.MAX_LENGTH:
            return False, f"Le mot de passe ne peut pas dépasser {PasswordValidator.MAX_LENGTH} caractères"
        
        # Vérifier que le mot de passe est alphanumérique uniquement
        if not re.match(r'^[a-zA-Z0-9]+$', password):
            return False, "Le mot de passe doit contenir uniquement des lettres et des chiffres"
        
        return True, None
    
    @staticmethod
    def get_password_requirements() -> str:
        """Retourne la description des exigences de mot de passe"""
        return f"Entre {PasswordValidator.MIN_LENGTH} et {PasswordValidator.MAX_LENGTH} caractères alphanumériques (lettres et chiffres uniquement)"


class SecurityConfig:
    """Configuration de sécurité"""
    
    # Configuration des sessions
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure
    
    # Configuration CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Configuration des mots de passe
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    PASSWORD_EXPIRY_DAYS = 90  # Expiration des mots de passe
    
    # Configuration du rate limiting
    LOGIN_RATE_LIMIT = "5 per minute"
    REGISTER_RATE_LIMIT = "3 per hour"
    API_RATE_LIMIT = "100 per minute"
    
    # Configuration des headers de sécurité
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',  # HTTPS only
    }
    
    @staticmethod
    def is_default_password(password: str) -> bool:
        """Vérifie si le mot de passe est un mot de passe par défaut"""
        default_passwords = [
            'admin123', 'medecin123', 'password', '123456',
            'admin', 'root', 'toor', 'test'
        ]
        return password.lower() in default_passwords