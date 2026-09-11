import pytest
from hopital.security import PasswordValidator, SecurityConfig


class TestPasswordValidator:
    """Tests pour le validateur de mots de passe"""
    
    def test_valid_password(self):
        """Test qu'un mot de passe valide passe la validation"""
        password = "SecurePass123!"
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is True
        assert error is None
    
    def test_too_short_password(self):
        """Test qu'un mot de passe trop court est rejeté"""
        password = "Short1!"
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is False
        assert "8 caractères" in error
    
    def test_no_uppercase(self):
        """Test qu'un mot de passe sans majuscule est rejeté"""
        password = "lowercase123!"
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is False
        assert "majuscule" in error
    
    def test_no_lowercase(self):
        """Test qu'un mot de passe sans minuscule est rejeté"""
        password = "UPPERCASE123!"
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is False
        assert "minuscule" in error
    
    def test_no_digit(self):
        """Test qu'un mot de passe sans chiffre est rejeté"""
        password = "NoDigits!!"
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is False
        assert "chiffre" in error
    
    def test_no_special_char(self):
        """Test qu'un mot de passe sans caractère spécial est rejeté"""
        password = "NoSpecial123"
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is False
        assert "spécial" in error
    
    def test_weak_password(self):
        """Test que les mots de passe courants sont rejetés"""
        weak_passwords = ["Password123!", "Admin123!", "Qwerty123!"]
        for password in weak_passwords:
            is_valid, error = PasswordValidator.validate(password)
            assert is_valid is False
            assert "courant" in error or "non sécurisé" in error
    
    def test_empty_password(self):
        """Test qu'un mot de passe vide est rejeté"""
        password = ""
        is_valid, error = PasswordValidator.validate(password)
        assert is_valid is False
        assert "vide" in error
    
    def test_get_password_requirements(self):
        """Test que les exigences de mot de passe sont correctement retournées"""
        requirements = PasswordValidator.get_password_requirements()
        assert "8" in requirements
        assert "majuscule" in requirements
        assert "minuscule" in requirements
        assert "chiffre" in requirements
        assert "spécial" in requirements


class TestSecurityConfig:
    """Tests pour la configuration de sécurité"""
    
    def test_default_password_detection(self):
        """Test que les mots de passe par défaut sont détectés"""
        assert SecurityConfig.is_default_password("admin123") is True
        assert SecurityConfig.is_default_password("password") is True
        assert SecurityConfig.is_default_password("SecurePass123!") is False
    
    def test_rate_limit_config(self):
        """Test que les limites de rate sont configurées"""
        assert SecurityConfig.LOGIN_RATE_LIMIT == "5 per minute"
        assert SecurityConfig.REGISTER_RATE_LIMIT == "3 per hour"
        assert SecurityConfig.API_RATE_LIMIT == "100 per minute"
    
    def test_security_headers(self):
        """Test que les headers de sécurité sont configurés"""
        assert 'X-Content-Type-Options' in SecurityConfig.SECURITY_HEADERS
        assert 'X-Frame-Options' in SecurityConfig.SECURITY_HEADERS
        assert 'X-XSS-Protection' in SecurityConfig.SECURITY_HEADERS
        assert 'Strict-Transport-Security' in SecurityConfig.SECURITY_HEADERS