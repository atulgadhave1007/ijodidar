"""REST API conversation/messaging endpoints — /api/v1/conversations/*"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app import db
from app.models import Conversation, Message, User, Interest
from app.api.errors import api_ok, api_error, NOT_FOUND, FORBIDDEN, VALIDATION_ERROR
from app.api.schemas import conv_summary_schema, convs_summary_schema, message_schema, messages_schema

conversations_api_bp = Blueprint('conversations_api', __name__)


def _get_conv_or_403(conv_id, uid):
    conv = Conversation.query.get(conv_id)
    if not conv:
        return None, api_error(NOT_FOUND, 'Conversation not found', 404)
    if uid not in (conv.user1_id, conv.user2_id):
        return None, api_error(FORBIDDEN, 'Not a participant', 403)
    return conv, None


@conversations_api_bp.route('', methods=['GET'])
@jwt_required()
def list_conversations():
    uid  = int(get_jwt_identity())
    page = max(1, request.args.get('page', 1, type=int))
    per  = min(50, request.args.get('per_page', 20, type=int))
    q = (Conversation.query
         .filter(or_(Conversation.user1_id == uid, Conversation.user2_id == uid))
         .order_by(Conversation.updated_at.desc()))
    total = q.count()
    convs = q.offset((page - 1) * per).limit(per).all()
    return api_ok(convs_summary_schema.dump(convs),
                  meta={'page': page, 'per_page': per, 'total': total,
                        'pages': (total + per - 1) // per})


@conversations_api_bp.route('/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conv_id):
    uid = int(get_jwt_identity())
    conv, err = _get_conv_or_403(conv_id, uid)
    if err:
        return err

    # Cursor-based pagination: before=<message_id>
    before = request.args.get('before', type=int)
    per    = min(50, request.args.get('per_page', 30, type=int))

    q = conv.messages.order_by(Message.sent_at.desc())
    if before:
        pivot = Message.query.get(before)
        if pivot:
            q = q.filter(Message.sent_at < pivot.sent_at)
    msgs = q.limit(per).all()
    msgs = list(reversed(msgs))   # chronological order

    has_more = False
    if msgs:
        has_more = (conv.messages.filter(Message.sent_at < msgs[0].sent_at).count() > 0)

    return api_ok(messages_schema.dump(msgs),
                  meta={'has_more': has_more,
                        'oldest_id': msgs[0].id if msgs else None})


@conversations_api_bp.route('/<int:conv_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conv_id):
    uid = int(get_jwt_identity())
    me  = User.query.get(uid)
    conv, err = _get_conv_or_403(conv_id, uid)
    if err:
        return err

    # Must have accepted interest to message
    u1, u2 = conv.user1_id, conv.user2_id
    accepted = (Interest.query
                .filter(
                    Interest.status == 'accepted',
                    or_(
                        (Interest.sender_id == u1) & (Interest.receiver_id == u2),
                        (Interest.sender_id == u2) & (Interest.receiver_id == u1),
                    )
                ).first())
    if not accepted:
        return api_error(FORBIDDEN, 'Interest must be accepted before messaging', 403)

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return api_error(VALIDATION_ERROR, 'Message body cannot be empty')
    if len(body) > 2000:
        return api_error(VALIDATION_ERROR, 'Message too long (max 2000 chars)')

    from datetime import datetime as _dt
    msg = Message(conversation_id=conv_id, sender_id=uid, body=body)
    conv.updated_at = _dt.utcnow()
    db.session.add(msg)
    db.session.commit()

    # In-app notification (non-fatal)
    try:
        other_uid = conv.user2_id if uid == conv.user1_id else conv.user1_id
        from app.utils import create_notification
        create_notification(user_id=other_uid, notif_type='new_message',
                            message=f'{me.full_name} sent you a message.',
                            link=f'/messages/{conv_id}')
    except Exception:
        pass

    return api_ok(message_schema.dump(msg), status=201)


@conversations_api_bp.route('/<int:conv_id>/read', methods=['PATCH'])
@jwt_required()
def mark_read(conv_id):
    uid = int(get_jwt_identity())
    conv, err = _get_conv_or_403(conv_id, uid)
    if err:
        return err

    (Message.query
     .filter_by(conversation_id=conv_id, is_read=False)
     .filter(Message.sender_id != uid)
     .update({'is_read': True}))
    db.session.commit()
    return api_ok({'success': True})
