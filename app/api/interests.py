"""REST API interest endpoints — /api/v1/interests/*"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app import db, limiter
from app.models import Interest, User, BlockList, Conversation
from app.api.errors import api_ok, api_error, NOT_FOUND, FORBIDDEN, VALIDATION_ERROR
from app.api.schemas import interest_schema, interests_schema

interests_api_bp = Blueprint('interests_api', __name__)


def _remaining_interests(user):
    plan = user.active_subscription
    if plan:
        return plan.interests_remaining()
    sent = Interest.query.filter(
        Interest.sender_id == user.id,
        Interest.status    != 'withdrawn'
    ).count()
    return max(0, 5 - sent)


@interests_api_bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit('30 per day')
def send_interest():
    uid  = int(get_jwt_identity())
    me   = User.query.get(uid)
    if not me:
        return api_error(NOT_FOUND, 'User not found', 404)

    data        = request.get_json(silent=True) or {}
    receiver_id = data.get('receiver_id')
    message     = (data.get('message') or '').strip()[:300]

    if not receiver_id:
        return api_error(VALIDATION_ERROR, 'receiver_id is required')

    receiver = User.query.get(receiver_id)
    if not receiver or not receiver.is_active_acc:
        return api_error(NOT_FOUND, 'Profile not found', 404)

    if receiver_id == uid:
        return api_error(VALIDATION_ERROR, 'Cannot send interest to yourself')

    if not me.is_verified:
        return api_error(VALIDATION_ERROR, 'Verify your email before sending interests')

    # Block check
    block = BlockList.query.filter(
        or_(
            (BlockList.blocker_id == uid)          & (BlockList.blocked_id == receiver_id),
            (BlockList.blocker_id == receiver_id)  & (BlockList.blocked_id == uid),
        )
    ).first()
    if block:
        return api_error(FORBIDDEN, 'Cannot send interest to this profile', 403)

    # Monthly limit
    remaining = _remaining_interests(me)
    if remaining <= 0:
        return api_error('LIMIT_REACHED', 'Monthly interest limit reached. Upgrade your plan.', 429)

    existing = Interest.query.filter_by(sender_id=uid, receiver_id=receiver_id).first()
    if existing:
        if existing.status == 'withdrawn':
            existing.status  = 'pending'
            existing.message = message
            db.session.commit()
        else:
            return api_error(VALIDATION_ERROR, 'Interest already sent')
        interest = existing
    else:
        interest = Interest(sender_id=uid, receiver_id=receiver_id,
                            message=message, status='pending')
        db.session.add(interest)
        db.session.commit()
        # Track monthly count
        plan = me.active_subscription
        if plan:
            plan.interests_this_month = (plan.interests_this_month or 0) + 1
            db.session.commit()

    # Side effects (non-fatal)
    try:
        from app.tasks import send_interest_email_task
        send_interest_email_task.delay(receiver_id, me.full_name)
    except Exception:
        pass
    try:
        from app.utils import create_notification, record_signal
        create_notification(user_id=receiver_id, notif_type='interest_received',
                            message=f'{me.full_name} sent you an interest request!',
                            link='/interests')
        record_signal(uid, receiver_id, 'interest_sent')
    except Exception:
        pass

    return api_ok(interest_schema.dump(interest),
                  meta={'remaining': _remaining_interests(me)}, status=201)


@interests_api_bp.route('/received', methods=['GET'])
@jwt_required()
def get_received():
    uid  = int(get_jwt_identity())
    page = max(1, request.args.get('page', 1, type=int))
    per  = min(50, request.args.get('per_page', 20, type=int))
    q = (Interest.query
         .filter_by(receiver_id=uid)
         .order_by(Interest.sent_at.desc()))
    total  = q.count()
    items  = q.offset((page - 1) * per).limit(per).all()
    return api_ok(interests_schema.dump(items),
                  meta={'page': page, 'per_page': per, 'total': total,
                        'pages': (total + per - 1) // per})


@interests_api_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent():
    uid  = int(get_jwt_identity())
    page = max(1, request.args.get('page', 1, type=int))
    per  = min(50, request.args.get('per_page', 20, type=int))
    q = (Interest.query
         .filter_by(sender_id=uid)
         .filter(Interest.status != 'withdrawn')
         .order_by(Interest.sent_at.desc()))
    total = q.count()
    items = q.offset((page - 1) * per).limit(per).all()
    return api_ok(interests_schema.dump(items),
                  meta={'page': page, 'per_page': per, 'total': total,
                        'pages': (total + per - 1) // per})


@interests_api_bp.route('/accepted', methods=['GET'])
@jwt_required()
def get_accepted():
    uid  = int(get_jwt_identity())
    page = max(1, request.args.get('page', 1, type=int))
    per  = min(50, request.args.get('per_page', 20, type=int))
    q = (Interest.query
         .filter(
             Interest.status == 'accepted',
             or_(Interest.sender_id == uid, Interest.receiver_id == uid)
         )
         .order_by(Interest.updated_at.desc()))
    total = q.count()
    items = q.offset((page - 1) * per).limit(per).all()
    return api_ok(interests_schema.dump(items),
                  meta={'page': page, 'per_page': per, 'total': total,
                        'pages': (total + per - 1) // per})


@interests_api_bp.route('/<int:interest_id>', methods=['PATCH'])
@jwt_required()
def respond_interest(interest_id):
    uid      = int(get_jwt_identity())
    me       = User.query.get(uid)
    interest = Interest.query.get(interest_id)
    if not interest:
        return api_error(NOT_FOUND, 'Interest not found', 404)

    data   = request.get_json(silent=True) or {}
    action = data.get('action')

    if action not in ('accept', 'decline', 'withdraw'):
        return api_error(VALIDATION_ERROR, 'action must be accept | decline | withdraw')

    if action == 'withdraw':
        if interest.sender_id != uid:
            return api_error(FORBIDDEN, 'Not your interest to withdraw', 403)
        interest.status = 'withdrawn'
        db.session.commit()
        return api_ok(interest_schema.dump(interest))

    # accept / decline — only receiver can act
    if interest.receiver_id != uid:
        return api_error(FORBIDDEN, 'Not your interest to respond to', 403)

    conv_id = None
    if action == 'accept':
        interest.status = 'accepted'
        u1, u2 = sorted([interest.sender_id, interest.receiver_id])
        conv = Conversation.query.filter_by(user1_id=u1, user2_id=u2).first()
        if not conv:
            conv = Conversation(user1_id=u1, user2_id=u2, interest_id=interest.id)
            db.session.add(conv)
        db.session.commit()
        conv_id = conv.id

        try:
            from app.tasks import send_interest_accepted_email_task
            send_interest_accepted_email_task.delay(interest.sender_id, me.full_name, conv_id)
        except Exception:
            pass
        try:
            from app.utils import create_notification, record_signal
            create_notification(user_id=interest.sender_id, notif_type='interest_accepted',
                                message=f'{me.full_name} accepted your interest! Start chatting.',
                                link=f'/messages/{conv_id}')
            record_signal(uid, interest.sender_id, 'interest_accepted')
            record_signal(interest.sender_id, uid, 'interest_accepted')
        except Exception:
            pass

    elif action == 'decline':
        interest.status = 'declined'
        db.session.commit()
        try:
            from app.utils import record_signal
            record_signal(uid, interest.sender_id, 'interest_declined')
        except Exception:
            pass

    out = interest_schema.dump(interest)
    if conv_id:
        out['conversation_id'] = conv_id
    return api_ok(out)
