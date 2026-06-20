from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, selectinload
from app import db, limiter
from app.models import Conversation, Message, User, Interest

messaging_bp = Blueprint('messaging', __name__)


def _get_or_403(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
        abort(403)
    return conv


def _can_message(current_user, other_id):
    """Return True if current_user is allowed to message other_id."""
    plan    = current_user.active_subscription
    can_msg = plan and plan.plan.can_message if plan else False
    if not can_msg:
        interest = Interest.query.filter(
            or_(
                and_(Interest.sender_id   == current_user.id,
                     Interest.receiver_id == other_id),
                and_(Interest.sender_id   == other_id,
                     Interest.receiver_id == current_user.id),
            ),
            Interest.status == 'accepted'
        ).first()
        can_msg = bool(interest)
    return can_msg


# ── INBOX ──────────────────────────────────────────────────────────────────
@messaging_bp.route('/messages')
@login_required
def inbox():
    convs = (Conversation.query
             .filter(or_(Conversation.user1_id == current_user.id,
                         Conversation.user2_id == current_user.id))
             .options(
                 joinedload(Conversation.user1).selectinload(User.profile_images),
                 joinedload(Conversation.user2).selectinload(User.profile_images),
             )
             .order_by(Conversation.updated_at.desc())
             .all())
    return render_template('messaging/inbox.html',
                           user=current_user, conversations=convs)


# ── CONVERSATION ───────────────────────────────────────────────────────────
@messaging_bp.route('/messages/<int:conv_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("120 per minute")
def conversation(conv_id):
    conv    = _get_or_403(conv_id)
    other   = conv.other_user(current_user.id)
    can_msg = _can_message(current_user, other.id)

    if request.method == 'POST':
        # Gate 1: phone must be verified before messaging
        if not current_user.phone_verified:
            flash('Please verify your phone number to start messaging.', 'warning')
            return redirect(url_for('profile.phone'))

        if not can_msg:
            flash('Upgrade your plan to send messages.', 'warning')
            return redirect(url_for('membership.plans'))
        body = request.form.get('body', '').strip()
        if not body or len(body) > 1000:
            flash('Invalid message.', 'danger')
            return redirect(url_for('messaging.conversation', conv_id=conv_id))

        msg             = Message(conversation_id=conv_id,
                                  sender_id=current_user.id, body=body)
        conv.updated_at = db.func.now()
        db.session.add(msg)
        db.session.commit()

        # In-app notification (sync — fast DB write)
        from app.utils import create_notification
        create_notification(
            user_id    = other.id,
            notif_type = 'new_message',
            message    = f'{current_user.full_name} sent you a message.',
            link       = f'/messages/{conv_id}',
        )
        # Async email + WhatsApp via Celery
        try:
            from app.tasks import send_message_email_task
            send_message_email_task.delay(
                other.id, current_user.full_name, body[:200], conv_id)
        except Exception:
            pass
        try:
            from app.utils import send_whatsapp
            if other.phone:
                send_whatsapp(other.phone, 'new_message',
                              [other.first_name, current_user.full_name])
        except Exception:
            pass

        return redirect(url_for('messaging.conversation', conv_id=conv_id))

    # Mark received messages as read
    (Message.query
     .filter_by(conversation_id=conv_id, is_read=False)
     .filter(Message.sender_id != current_user.id)
     .update({'is_read': True}))
    db.session.commit()

    messages = conv.messages.all()
    return render_template('messaging/conversation.html',
                           user=current_user, conv=conv, other=other,
                           messages=messages, can_msg=can_msg)


# ── POLL (fallback for non-WS clients) ────────────────────────────────────
@messaging_bp.route('/messages/<int:conv_id>/poll')
@login_required
def poll_messages(conv_id):
    conv     = _get_or_403(conv_id)
    after_id = request.args.get('after', 0, type=int)
    msgs     = (Message.query
                .filter_by(conversation_id=conv_id)
                .filter(Message.id > after_id)
                .order_by(Message.sent_at.asc()).all())
    for m in msgs:
        if m.sender_id != current_user.id:
            m.is_read = True
    db.session.commit()
    return jsonify([{
        'id':        m.id,
        'body':      m.body,
        'sender_id': m.sender_id,
        'sent_at':   m.sent_at.strftime('%I:%M %p'),
        'is_mine':   m.sender_id == current_user.id,
    } for m in msgs])


# ── WebRTC CALL PAGE (Phase 13.1) ─────────────────────────────────────────
@messaging_bp.route('/messages/<int:conv_id>/call')
@login_required
def call(conv_id):
    conv  = _get_or_403(conv_id)
    other = conv.other_user(current_user.id)

    # Only Gold/Platinum plan members can initiate calls
    plan     = current_user.active_subscription
    can_call = plan and plan.plan.can_view_phone   # Gold+ can also call
    if not can_call:
        from flask import flash, redirect, url_for
        flash('Upgrade to Gold or Platinum to make voice/video calls.', 'warning')
        return redirect(url_for('membership.plans'))

    call_type = request.args.get('type', 'video')   # 'video' or 'audio'
    return render_template('messaging/call.html',
                           user=current_user, other=other,
                           conv=conv, call_type=call_type)
