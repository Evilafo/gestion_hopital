import re
from typing import Tuple, Optional


class PasswordValidator:
    """Validateur de mots de passe sécurisés"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
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
        
        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        
        if PasswordValidator.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        
        if PasswordValidator.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        if PasswordValidator.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial"
        
        # Vérifier les mots de passe courants et faibles
        weak_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 'password123',
            'admin123', 'medecin123', 'root', 'toor', 'welcome',
            'Password123!', 'Admin123!', 'Qwerty123!', 'Welcome123!'
        ]
        
        if password.lower() in [wp.lower() for wp in weak_passwords]:
            return False, "Ce mot de passe est trop courant et non sécurisé"
        
        return True, None
    
    @staticmethod
    def get_password_requirements() -> str:
        """Retourne la description des exigences de mot de passe"""
        requirements = [
            f"Entre {PasswordValidator.MIN_LENGTH} et {PasswordValidator.MAX_LENGTH} caractères"
        ]
        
        if PasswordValidator.REQUIRE_UPPERCASE:
            requirements.append("Au moins une majuscule")
        
        if PasswordValidator.REQUIRE_LOWERCASE:
            requirements.append("Au moins une minuscule")
        
        if PasswordValidator.REQUIRE_DIGIT:
            requirements.append("Au moins un chiffre")
        
        if PasswordValidator.REQUIRE_SPECIAL:
            requirements.append("Au moins un caractère spécial (!@#$%^&*(),.?\":{}|<>)")
        
        return ", ".join(requirements)


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