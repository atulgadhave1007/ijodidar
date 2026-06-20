from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()
    return jsonify(count=count)


@notifications_bp.route('/notifications/list')
@login_required
def list_notifications():
    notifs = (Notification.query
              .filter_by(user_id=current_user.id)
              .order_by(Notification.created_at.desc())
              .limit(15).all())
    return jsonify([{
        'id':         n.id,
        'type':       n.type,
        'message':    n.message,
        'link':       n.link,
        'is_read':    n.is_read,
        'created_at': n.created_at.strftime('%d %b, %I:%M %p'),
    } for n in notifs])


@notifications_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_read():
    ids = request.json.get('ids', [])
    if ids:
        Notification.query.filter(
            Notification.id.in_(ids),
            Notification.user_id == current_user.id
        ).update({'is_read': True}, synchronize_session=False)
    else:
        # Mark all read
        Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).update({'is_read': True})
    db.session.commit()
    return jsonify(success=True)
