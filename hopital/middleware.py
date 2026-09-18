from functools import wraps
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from hopital.extensions import limiter as app_limiter


def rate_limit_login(f):
    """Rate limiting pour la route de login"""
    @wraps(f)
    @app_limiter.limit("5 per minute", key_func=get_remote_address)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_register(f):
    """Rate limiting pour l'inscription"""
    @wraps(f)
    @app_limiter.limit("3 per hour", key_func=get_remote_address)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function