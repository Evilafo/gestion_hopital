"""
Tests pour la configuration du logging.
"""
import pytest
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from flask import Flask
from hopital.logging_config import (
    JSONFormatter, RequestContextFilter, setup_logging,
    log_access, log_security_event, log_database_operation
)


class TestJSONFormatter:
    """Tests pour le formateur JSON."""
    
    def test_json_formatter_basic(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            'test', logging.INFO, 'test.py', 10, 'Test message', (), None
        )
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['level'] == 'INFO'
        assert data['message'] == 'Test message'
        assert data['logger'] == 'test'
        assert 'timestamp' in data
    
    def test_json_formatter_with_exception(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            'test', logging.ERROR, 'test.py', 10, 'Error message', (), None
        )
        record.exc_info = (Exception, Exception("Test"), None)
        result = formatter.format(record)
        data = json.loads(result)
        
        assert 'exception' in data
        assert data['level'] == 'ERROR'


class TestRequestContextFilter:
    """Tests pour le filtre de contexte de requête."""
    
    def test_request_context_filter_without_flask(self):
        filter_obj = RequestContextFilter()
        record = logging.LogRecord(
            'test', logging.INFO, 'test.py', 10, 'Test message', (), None
        )
        
        result = filter_obj.filter(record)
        assert result is True


class TestSetupLogging:
    """Tests pour la configuration du logging."""
    
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['LOG_LEVEL'] = 'DEBUG'
        return app
    
    def test_setup_logging_creates_log_directory(self, app, tmp_path):
        with patch.object(app, 'instance_path', str(tmp_path)):
            setup_logging(app)
            log_dir = tmp_path / 'logs'
            assert log_dir.exists()
    
    def test_setup_logging_configures_root_logger(self, app, tmp_path):
        with patch.object(app, 'instance_path', str(tmp_path)):
            setup_logging(app)
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG


class TestLogAccess:
    """Tests pour la fonction log_access."""
    
    def test_log_access_basic(self):
        log_access('login', 'user', {'user_id': 1})
        
        # Vérifier que le log a été créé (ne pas crasher)
        logger = logging.getLogger('access')
        assert logger is not None
    
    def test_log_access_without_resource(self):
        log_access('logout')
        
        logger = logging.getLogger('access')
        assert logger is not None


class TestLogSecurityEvent:
    """Tests pour la fonction log_security_event."""
    
    def test_log_security_event_warning(self):
        log_security_event('failed_login', {'ip': '127.0.0.1'}, 'warning')
        
        logger = logging.getLogger('security')
        assert logger is not None
    
    def test_log_security_event_critical(self):
        log_security_event('unauthorized_access', {'user_id': 1}, 'critical')
        
        logger = logging.getLogger('security')
        assert logger is not None


class TestLogDatabaseOperation:
    """Tests pour la fonction log_database_operation."""
    
    def test_log_database_operation(self):
        log_database_operation('insert', 'users', {'user_id': 1})
        
        logger = logging.getLogger('database')
        assert logger is not None
