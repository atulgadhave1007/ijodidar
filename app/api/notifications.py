"""REST API notification endpoints — /api/v1/notifications/*"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Notification
from app.api.errors import api_ok, api_error, NOT_FOUND
from app.api.schemas import notification_schema, notifications_schema

notifications_api_bp = Blueprint('notifications_api', __name__)


@notifications_api_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    uid  = int(get_jwt_identity())
    page = max(1, request.args.get('page', 1, type=int))
    per  = min(50, request.args.get('per_page', 20, type=int))
    q = (Notification.query
         .filter_by(user_id=uid)
         .order_by(Notification.created_at.desc()))
    total = q.count()
    items = q.offset((page - 1) * per).limit(per).all()
    return api_ok(notifications_schema.dump(items),
                  meta={'page': page, 'per_page': per, 'total': total,
                        'pages': (total + per - 1) // per})


@notifications_api_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    uid   = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=uid, is_read=False).count()
    return api_ok({'count': count})


@notifications_api_bp.route('/read', methods=['PATCH'])
@jwt_required()
def mark_read():
    uid  = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    ids  = data.get('ids')   # optional list of notification IDs; if omitted, mark all

    q = Notification.query.filter_by(user_id=uid, is_read=False)
    if ids:
        if not isinstance(ids, list):
            return api_error('VALIDATION_ERROR', 'ids must be a list')
        q = q.filter(Notification.id.in_(ids))

    updated = q.update({'is_read': True}, synchronize_session='fetch')
    db.session.commit()
    return api_ok({'marked': updated})
