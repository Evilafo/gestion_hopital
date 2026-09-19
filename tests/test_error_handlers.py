"""
Tests pour les handlers d'erreurs centralisés.
"""
import pytest
import json
from flask import Flask
from hopital.error_handlers import (
    AppError, ValidationError, AuthenticationError, AuthorizationError,
    ResourceNotFoundError, ConflictError, BusinessLogicError,
    register_error_handlers, handle_errors
)


class TestAppError:
    """Tests pour la classe AppError."""
    
    def test_app_error_creation(self):
        error = AppError("Test error", status_code=400, payload={"key": "value"})
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.payload == {"key": "value"}
    
    def test_app_error_to_dict(self):
        error = AppError("Test error", status_code=400, payload={"key": "value"})
        result = error.to_dict()
        assert result["message"] == "Test error"
        assert result["status"] == "error"
        assert result["key"] == "value"


class TestErrorSubclasses:
    """Tests pour les sous-classes d'erreurs."""
    
    def test_validation_error(self):
        error = ValidationError("Invalid data")
        assert error.status_code == 400
        assert error.message == "Invalid data"
    
    def test_authentication_error(self):
        error = AuthenticationError("Wrong password")
        assert error.status_code == 401
        assert error.message == "Wrong password"
    
    def test_authorization_error(self):
        error = AuthorizationError("No permission")
        assert error.status_code == 403
        assert error.message == "No permission"
    
    def test_resource_not_found_error(self):
        error = ResourceNotFoundError("Patient not found")
        assert error.status_code == 404
        assert error.message == "Patient not found"
    
    def test_conflict_error(self):
        error = ConflictError("Email already exists")
        assert error.status_code == 409
        assert error.message == "Email already exists"
    
    def test_business_logic_error(self):
        error = BusinessLogicError("Cannot cancel past appointment")
        assert error.status_code == 422
        assert error.message == "Cannot cancel past appointment"


class TestErrorHandlers:
    """Tests pour les handlers d'erreurs Flask."""
    
    @pytest.fixture
    def app_with_error_handlers(self):
        app = Flask(__name__, template_folder='hopital/templates')
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        
        register_error_handlers(app)
        
        @app.route('/test-app-error')
        def test_app_error():
            raise ValidationError("Test validation error")
        
        @app.route('/test-http-error')
        def test_http_error():
            from werkzeug.exceptions import NotFound
            raise NotFound()
        
        @app.route('/test-generic-error')
        def test_generic_error():
            raise ValueError("Generic error")
        
        return app
    
    def test_app_error_handler(self, app_with_error_handlers):
        with app_with_error_handlers.test_client() as client:
            response = client.get('/test-app-error', headers={'Accept': 'application/json'})
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert data['message'] == 'Test validation error'
    
    def test_http_error_handler(self, app_with_error_handlers):
        with app_with_error_handlers.test_client() as client:
            response = client.get('/test-http-error', headers={'Accept': 'application/json'})
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['status'] == 'error'
    
    def test_generic_error_handler(self, app_with_error_handlers):
        with app_with_error_handlers.test_client() as client:
            response = client.get('/test-generic-error', headers={'Accept': 'application/json'})
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'Generic error' in data['message']


class TestHandleErrorsDecorator:
    """Tests pour le décorateur handle_errors."""
    
    def test_handle_errors_success(self):
        @handle_errors
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_handle_errors_app_error(self):
        @handle_errors
        def raise_app_error():
            raise ValidationError("Test error")
        
        with pytest.raises(ValidationError):
            raise_app_error()
    
    def test_handle_errors_generic_error(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        
        @handle_errors
        def raise_generic_error():
            raise ValueError("Generic error")
        
        with app.app_context():
            with pytest.raises(AppError):
                raise_generic_error()
