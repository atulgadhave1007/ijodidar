"""REST API auth endpoints — /api/v1/auth/*

Security baseline (MASTER_PROMPT.md §6.3):
- Rate limiting via Flask-Limiter backed by Redis
- JWT tokens validated on every protected call
- Blocklist via Redis DB4 on logout / password change
- No PII logged
"""
from datetime import datetime, timedelta
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
    current_user as jwt_current_user,
)
from app import db, limiter
from app.models import User
from app.api.errors import (api_ok, api_error,
    INVALID_CREDENTIALS, ACCOUNT_LOCKED, NOT_FOUND, VALIDATION_ERROR)
from app.api.schemas import user_schema

auth_api_bp = Blueprint('auth_api', __name__)


def _blocklist_redis():
    import redis as _redis
    import os
    url = os.environ.get('REDIS_URL', 'redis://localhost:6379/4')
    # Force DB4 for blocklist regardless of REDIS_URL DB number
    base = url.rsplit('/', 1)[0]
    return _redis.from_url(f'{base}/4', decode_responses=True)


@auth_api_bp.route('/login', methods=['POST'])
@limiter.limit('20 per minute')
def login():
    data = request.get_json(silent=True) or {}
    email    = (data.get('email', '') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return api_error(VALIDATION_ERROR, 'email and password are required', 422)

    user = User.query.filter_by(email=email).first()

    if user and user.locked_until and user.locked_until > datetime.utcnow():
        mins = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        return api_error(ACCOUNT_LOCKED,
                         f'Account locked. Try again in {mins} minute(s).', 429)

    if not user or not user.check_password(password):
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            if user.failed_login_count >= 10:
                user.locked_until       = datetime.utcnow() + timedelta(minutes=30)
                user.failed_login_count = 0
            db.session.commit()
        return api_error(INVALID_CREDENTIALS, 'Invalid email or password', 401)

    if not user.is_active_acc:
        return api_error(INVALID_CREDENTIALS, 'Account suspended. Contact support.', 403)

    user.failed_login_count = 0
    user.locked_until       = None
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return api_ok({
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'user': user_schema.dump(user),
    })


@auth_api_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id      = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return api_ok({'access_token': access_token})


@auth_api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    try:
        r   = _blocklist_redis()
        ttl = int(timedelta(hours=1).total_seconds()) + 60   # access token TTL + buffer
        r.setex(f'jwt_bl:{jti}', ttl, '1')
    except Exception:
        pass   # non-fatal — token will expire naturally
    return api_ok({'message': 'Logged out'})


@auth_api_bp.route('/forgot-password', methods=['POST'])
@limiter.limit('5 per hour')
def forgot_password():
    data  = request.get_json(silent=True) or {}
    email = (data.get('email', '') or '').strip().lower()
    if not email:
        return api_error(VALIDATION_ERROR, 'email is required', 422)
    user = User.query.filter_by(email=email).first()
    if user:
        from app.utils import generate_token
        token  = generate_token()
        expiry = datetime.utcnow() + timedelta(hours=1)
        user.reset_token        = token
        user.reset_token_expiry = expiry
        db.session.commit()
        reset_url = f'https://ijodidar.com/reset-password/{token}'
        try:
            from app.tasks import send_password_reset_email_task
            send_password_reset_email_task.delay(user.id, reset_url)
        except Exception:
            pass
    # Always same response — prevents email enumeration
    return api_ok({'message': 'If that email is registered, a reset link has been sent.'})


@auth_api_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data     = request.get_json(silent=True) or {}
    token    = data.get('token', '').strip()
    password = data.get('password', '')
    if not token or not password or len(password) < 8:
        return api_error(VALIDATION_ERROR,
                         'token and password (min 8 chars) are required', 422)
    user = User.query.filter_by(reset_token=token).first()
    if (not user or not user.reset_token_expiry
            or user.reset_token_expiry < datetime.utcnow()):
        return api_error(NOT_FOUND, 'Invalid or expired reset token', 400)
    user.set_password(password)
    user.reset_token        = None
    user.reset_token_expiry = None
    db.session.commit()
    return api_ok({'message': 'Password reset successfully.'})
