from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, limiter
from app.models import Interest, User, Shortlist, Conversation, BlockList, UserReport

connect_bp = Blueprint('connect', __name__)


def _get_interest(sender_id, receiver_id):
    return Interest.query.filter_by(sender_id=sender_id, receiver_id=receiver_id).first()


# ── SEND INTEREST ──────────────────────────────────────────────────────────
@connect_bp.route('/interest/send/<int:receiver_id>', methods=['POST'])
@login_required
@limiter.limit("30 per day")
def send_interest(receiver_id):
    receiver = User.query.get_or_404(receiver_id)
    if receiver.id == current_user.id:
        flash('You cannot send interest to yourself.', 'danger')
        return redirect(url_for('main.user_profile', username=receiver.username))

    # Verification gate — must verify email before sending interests
    if not current_user.is_verified:
        flash('Please verify your email address before sending interests.', 'warning')
        return redirect(url_for('main.user_profile', username=receiver.username))

    # Blocked?
    block = BlockList.query.filter(
        ((BlockList.blocker_id == current_user.id) & (BlockList.blocked_id == receiver_id)) |
        ((BlockList.blocker_id == receiver_id)      & (BlockList.blocked_id == current_user.id))
    ).first()
    if block:
        flash('You cannot send interest to this profile.', 'danger')
        return redirect(url_for('main.home'))

    # Plan limit — monthly reset
    plan = current_user.active_subscription
    if plan:
        remaining = plan.interests_remaining()
        if remaining <= 0:
            flash(f'Monthly interest limit reached. Upgrade your plan for more.', 'warning')
            return redirect(url_for('membership.plans'))
    else:
        # No subscription — check free limit (5 total)
        sent = Interest.query.filter(
            Interest.sender_id == current_user.id,
            Interest.status    != 'withdrawn'
        ).count()
        if sent >= 5:
            flash('Free plan limit (5 interests) reached. Upgrade to Silver or higher.', 'warning')
            return redirect(url_for('membership.plans'))

    existing = _get_interest(current_user.id, receiver_id)
    if existing:
        if existing.status == 'withdrawn':
            existing.status  = 'pending'
            existing.message = request.form.get('message', '').strip()[:300]
            db.session.commit()
            flash(f'Interest re-sent to {receiver.full_name}.', 'success')
        else:
            flash('You have already sent interest to this person.', 'info')
        return redirect(url_for('main.user_profile', username=receiver.username))

    db.session.add(Interest(
        sender_id   = current_user.id,
        receiver_id = receiver_id,
        message     = request.form.get('message', '').strip()[:300],
        status      = 'pending',
    ))
    db.session.commit()
    # Track monthly interest count
    plan = current_user.active_subscription
    if plan:
        plan.interests_this_month = (plan.interests_this_month or 0) + 1
        db.session.commit()

    # Async email via Celery
    try:
        from app.tasks import send_interest_email_task
        send_interest_email_task.delay(receiver_id, current_user.full_name)
    except Exception:
        pass

    # In-app notification
    from app.utils import create_notification
    create_notification(
        user_id    = receiver_id,
        notif_type = 'interest_received',
        message    = f'{current_user.full_name} sent you an interest request!',
        link       = f'/interests',
    )
    # WhatsApp notification (Phase 14.3)
    from app.utils import send_whatsapp
    if receiver.phone:
        send_whatsapp(receiver.phone, 'interest_received',
                      [receiver.first_name, current_user.full_name])

    # Record behavior signal
    try:
        from app.utils import record_signal
        record_signal(current_user.id, receiver_id, 'interest_sent')
    except Exception:
        pass
    # Record behavioral signal for match learning
    try:
        from app.utils import record_signal
        record_signal(current_user.id, receiver_id, 'interest_sent')
    except Exception:
        pass

    flash(f'Interest sent to {receiver.full_name}!', 'success')
    return redirect(url_for('main.user_profile', username=receiver.username))


# ── RESPOND TO INTEREST ────────────────────────────────────────────────────
@connect_bp.route('/interest/respond/<int:interest_id>/<action>', methods=['POST'])
@login_required
def respond_interest(interest_id, action):
    interest = Interest.query.get_or_404(interest_id)
    if interest.receiver_id != current_user.id:
        abort(403)

    if action == 'accept':
        interest.status = 'accepted'
        u1, u2 = sorted([interest.sender_id, interest.receiver_id])
        conv = Conversation.query.filter_by(user1_id=u1, user2_id=u2).first()
        if not conv:
            conv = Conversation(user1_id=u1, user2_id=u2, interest_id=interest.id)
            db.session.add(conv)
        db.session.commit()

        # Async email via Celery
        try:
            from app.tasks import send_interest_accepted_email_task
            send_interest_accepted_email_task.delay(
                interest.sender_id, current_user.full_name, conv.id)
        except Exception:
            pass

        # In-app notification to sender
        from app.utils import create_notification
        create_notification(
            user_id    = interest.sender_id,
            notif_type = 'interest_accepted',
            message    = f'{current_user.full_name} accepted your interest! Start chatting.',
            link       = f'/messages/{conv.id}',
        )
        # WhatsApp notification (Phase 14.3)
        from app.utils import send_whatsapp
        if interest.sender.phone:
            send_whatsapp(interest.sender.phone, 'interest_accepted',
                          [interest.sender.first_name, current_user.full_name])

        # Record acceptance signal for both sides
        try:
            from app.utils import record_signal
            record_signal(current_user.id,  interest.sender_id,   'interest_accepted')
            record_signal(interest.sender_id, current_user.id,     'interest_accepted')
        except Exception:
            pass
        # Record signal: receiver accepted this sender's interest
        try:
            from app.utils import record_signal
            record_signal(current_user.id, interest.sender_id, 'interest_accepted')
        except Exception:
            pass

        flash(f"You accepted {interest.sender.full_name}'s interest! You can now chat.", 'success')
        return redirect(url_for('messaging.conversation', conv_id=conv.id))

    elif action == 'decline':
        interest.status = 'declined'
        db.session.commit()
        # Record signal: receiver declined
        try:
            from app.utils import record_signal
            record_signal(current_user.id, interest.sender_id, 'interest_declined')
        except Exception:
            pass
        flash('Interest declined.', 'info')

    return redirect(url_for('connect.my_interests'))


# ── WITHDRAW ───────────────────────────────────────────────────────────────
@connect_bp.route('/interest/withdraw/<int:interest_id>', methods=['POST'])
@login_required
def withdraw_interest(interest_id):
    interest = Interest.query.get_or_404(interest_id)
    if interest.sender_id != current_user.id:
        abort(403)
    interest.status = 'withdrawn'
    db.session.commit()
    flash('Interest withdrawn.', 'info')
    return redirect(url_for('connect.my_interests'))


# ── MY INTERESTS ───────────────────────────────────────────────────────────
@connect_bp.route('/interests')
@login_required
def my_interests():
    sent     = (Interest.query
                .filter_by(sender_id=current_user.id)
                .filter(Interest.status.in_(['pending', 'declined']))
                .order_by(Interest.sent_at.desc()).all())
    received = (Interest.query
                .filter_by(receiver_id=current_user.id)
                .order_by(Interest.sent_at.desc()).all())
    pending  = [i for i in received if i.status == 'pending']
    # accepted: interests the user sent that were accepted + interests received that user accepted
    # tag each with which side current_user is on so template can show the right other-person
    sent_accepted     = [i for i in sent     if i.status == 'accepted']
    received_accepted = [i for i in received if i.status == 'accepted']
    declined = [i for i in received if i.status == 'declined']
    return render_template('connect/interests.html',
                           user=current_user,
                           sent=sent, pending=pending,
                           sent_accepted=sent_accepted,
                           received_accepted=received_accepted,
                           declined=declined)


# ── SHORTLIST ──────────────────────────────────────────────────────────────
@connect_bp.route('/shortlist/toggle/<int:target_id>', methods=['POST'])
@login_required
def toggle_shortlist(target_id):
    if target_id == current_user.id:
        return jsonify(success=False, msg='Cannot shortlist yourself.')
    existing = Shortlist.query.filter_by(
        user_id=current_user.id, shortlisted_id=target_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify(success=True, action='removed', msg='Removed from shortlist.')
    db.session.add(Shortlist(user_id=current_user.id, shortlisted_id=target_id))
    db.session.commit()
    try:
        from app.utils import record_signal
        record_signal(current_user.id, target_id, 'shortlisted')
    except Exception:
        pass
    return jsonify(success=True, action='added', msg='Added to shortlist!')


@connect_bp.route('/shortlist')
@login_required
def my_shortlist():
    items = (Shortlist.query
             .filter_by(user_id=current_user.id)
             .order_by(Shortlist.created_at.desc()).all())
    return render_template('connect/shortlist.html', user=current_user, items=items)


# ── BLOCK ──────────────────────────────────────────────────────────────────
@connect_bp.route('/block/<int:target_id>', methods=['POST'])
@login_required
def block_user(target_id):
    if target_id == current_user.id:
        return jsonify(success=False, msg='Cannot block yourself.')
    target = User.query.get_or_404(target_id)
    existing = BlockList.query.filter_by(
        blocker_id=current_user.id, blocked_id=target_id).first()
    if existing:
        return jsonify(success=False, msg='Already blocked.')
    db.session.add(BlockList(blocker_id=current_user.id, blocked_id=target_id))
    db.session.commit()
    try:
        from app.utils import record_signal
        record_signal(current_user.id, target_id, 'blocked')
    except Exception:
        pass
    flash(f'{target.full_name} has been blocked. They will no longer appear in your searches.', 'info')
    return redirect(url_for('main.home'))


@connect_bp.route('/unblock/<int:target_id>', methods=['POST'])
@login_required
def unblock_user(target_id):
    block = BlockList.query.filter_by(
        blocker_id=current_user.id, blocked_id=target_id).first_or_404()
    db.session.delete(block)
    db.session.commit()
    flash('User unblocked.', 'success')
    return redirect(url_for('main.home'))


# ── REPORT ─────────────────────────────────────────────────────────────────
@connect_bp.route('/report/<int:target_id>', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def report_user(target_id):
    if target_id == current_user.id:
        return jsonify(success=False, msg='Cannot report yourself.')
    target = User.query.get_or_404(target_id)
    reason  = request.form.get('reason', '').strip()
    details = request.form.get('details', '').strip()
    if not reason:
        flash('Please select a reason for the report.', 'danger')
        return redirect(url_for('main.user_profile', username=target.username))
    db.session.add(UserReport(
        reporter_id = current_user.id,
        reported_id = target_id,
        reason      = reason,
        details     = details[:500],
        status      = 'pending',
    ))
    db.session.commit()
    try:
        from app.utils import record_signal
        record_signal(current_user.id, target_id, 'reported')
    except Exception:
        pass
    flash('Report submitted. Our team will review it within 24 hours.', 'success')
    return redirect(url_for('main.user_profile', username=target.username))
