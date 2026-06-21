"""REST API device (FCM token) endpoints — /api/v1/devices/*"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import UserDevice
from app.api.errors import api_ok, api_error, NOT_FOUND, FORBIDDEN, VALIDATION_ERROR

devices_api_bp = Blueprint('devices_api', __name__)

VALID_PLATFORMS = {'android', 'ios', 'web'}


@devices_api_bp.route('', methods=['POST'])
@jwt_required()
def register_device():
    uid  = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    fcm_token   = (data.get('fcm_token') or '').strip()
    platform    = (data.get('platform') or '').strip().lower()
    app_version = (data.get('app_version') or '').strip()[:20] or None

    if not fcm_token:
        return api_error(VALIDATION_ERROR, 'fcm_token is required')
    if platform not in VALID_PLATFORMS:
        return api_error(VALIDATION_ERROR, f'platform must be one of: {", ".join(VALID_PLATFORMS)}')

    device = UserDevice.query.filter_by(fcm_token=fcm_token).first()
    if device:
        # Token already registered — update owner + last_seen (handles re-installs)
        device.user_id     = uid
        device.platform    = platform
        device.app_version = app_version
        device.last_seen   = datetime.utcnow()
    else:
        device = UserDevice(user_id=uid, fcm_token=fcm_token,
                            platform=platform, app_version=app_version)
        db.session.add(device)

    db.session.commit()
    return api_ok({'id': device.id, 'platform': device.platform}, status=201)


@devices_api_bp.route('/<fcm_token>', methods=['DELETE'])
@jwt_required()
def unregister_device(fcm_token):
    uid    = int(get_jwt_identity())
    device = UserDevice.query.filter_by(fcm_token=fcm_token).first()
    if not device:
        return api_error(NOT_FOUND, 'Device not found', 404)
    if device.user_id != uid:
        return api_error(FORBIDDEN, 'Not your device', 403)

    db.session.delete(device)
    db.session.commit()
    return api_ok({'success': True})
