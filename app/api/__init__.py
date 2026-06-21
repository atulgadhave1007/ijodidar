"""app/api/__init__.py — REST API v1 blueprint

All endpoints live under /api/v1/.
JWT Bearer token auth. Session auth is NOT used here.
CSRF is exempted (registered in app/__init__.py via csrf.exempt).
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import JWTManager

api_v1_bp = Blueprint('api_v1', __name__)

# ── Sub-blueprints ────────────────────────────────────────────────────────────
from app.api.auth          import auth_api_bp
from app.api.profiles      import profiles_api_bp
from app.api.interests     import interests_api_bp
from app.api.conversations import conversations_api_bp
from app.api.notifications import notifications_api_bp
from app.api.devices       import devices_api_bp

api_v1_bp.register_blueprint(auth_api_bp,           url_prefix='/auth')
api_v1_bp.register_blueprint(profiles_api_bp,       url_prefix='/profiles')
api_v1_bp.register_blueprint(interests_api_bp,      url_prefix='/interests')
api_v1_bp.register_blueprint(conversations_api_bp,  url_prefix='/conversations')
api_v1_bp.register_blueprint(notifications_api_bp,  url_prefix='/notifications')
api_v1_bp.register_blueprint(devices_api_bp,        url_prefix='/devices')


# ── JWT error handlers (return JSON, not HTML) ────────────────────────────────
from app import jwt as _jwt
from app.api.errors import api_error, NOT_AUTHENTICATED, TOKEN_EXPIRED, REFRESH_REQUIRED


@_jwt.expired_token_loader
def expired_token_cb(jwt_header, jwt_payload):
    if jwt_payload.get('type') == 'refresh':
        return api_error(REFRESH_REQUIRED, 'Refresh token expired. Please log in again.', 401)
    return api_error(TOKEN_EXPIRED, 'Access token expired. Use /auth/refresh.', 401)


@_jwt.invalid_token_loader
def invalid_token_cb(reason):
    return api_error(NOT_AUTHENTICATED, f'Invalid token: {reason}', 401)


@_jwt.unauthorized_loader
def missing_token_cb(reason):
    return api_error(NOT_AUTHENTICATED, 'Authorization header missing or malformed.', 401)


@_jwt.revoked_token_loader
def revoked_token_cb(jwt_header, jwt_payload):
    return api_error(NOT_AUTHENTICATED, 'Token has been revoked. Please log in again.', 401)


# ── JWT user identity loader ──────────────────────────────────────────────────
@_jwt.user_lookup_loader
def user_lookup_cb(_jwt_header, jwt_data):
    from app.models import User
    identity = jwt_data['sub']
    return User.query.get(int(identity))


# ── JWT token blocklist check (Redis DB4) ────────────────────────────────────
@_jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get('jti')
    if not jti:
        return False
    try:
        import redis as _redis
        import os
        url  = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        base = url.rsplit('/', 1)[0]
        r    = _redis.from_url(f'{base}/4', decode_responses=True)
        return r.exists(f'jwt_bl:{jti}') == 1
    except Exception:
        return False   # fail open — if Redis is unavailable, don't block requests


# ── Generic API 404 / 405 ────────────────────────────────────────────────────
@api_v1_bp.app_errorhandler(404)
def api_404(e):
    from flask import request
    if request.path.startswith('/api/'):
        return jsonify({'success': False,
                        'error': {'code': 'NOT_FOUND', 'message': str(e)}}), 404
    return e


@api_v1_bp.app_errorhandler(405)
def api_405(e):
    from flask import request
    if request.path.startswith('/api/'):
        return jsonify({'success': False,
                        'error': {'code': 'METHOD_NOT_ALLOWED', 'message': str(e)}}), 405
    return e
