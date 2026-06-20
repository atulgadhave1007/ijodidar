"""API error code registry and helper."""
from flask import jsonify

# ── Error codes ───────────────────────────────────────────────────────────────
INVALID_OTP        = 'INVALID_OTP'
OTP_EXPIRED        = 'OTP_EXPIRED'
ACCOUNT_LOCKED     = 'ACCOUNT_LOCKED'
NOT_AUTHENTICATED  = 'NOT_AUTHENTICATED'
TOKEN_EXPIRED      = 'TOKEN_EXPIRED'
REFRESH_REQUIRED   = 'REFRESH_REQUIRED'
PHONE_NOT_VERIFIED = 'PHONE_NOT_VERIFIED'
PLAN_REQUIRED      = 'PLAN_REQUIRED'
INTEREST_LIMIT     = 'INTEREST_LIMIT'
ALREADY_EXISTS     = 'ALREADY_EXISTS'
NOT_FOUND          = 'NOT_FOUND'
FORBIDDEN          = 'FORBIDDEN'
VALIDATION_ERROR   = 'VALIDATION_ERROR'
PAYMENT_FAILED     = 'PAYMENT_FAILED'
INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'


def api_error(code: str, message: str, status: int = 400, field: str = None):
    body = {'success': False, 'error': {'code': code, 'message': message}}
    if field:
        body['error']['field'] = field
    return jsonify(body), status


def api_ok(data=None, meta=None, status: int = 200):
    body = {'success': True, 'data': data or {}}
    if meta:
        body['meta'] = meta
    return jsonify(body), status
