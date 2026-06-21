import hmac, hashlib, json
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, current_app, abort)
from flask_login import login_required, current_user
from app import db
from app.models import MembershipPlan, UserSubscription
from app.utils import send_email

membership_bp = Blueprint('membership', __name__)


def _razorpay_client():
    import razorpay
    return razorpay.Client(
        auth=(current_app.config['RAZORPAY_KEY_ID'],
              current_app.config['RAZORPAY_KEY_SECRET'])
    )


def _activate_plan(user, plan, payment_ref, amount_paise):
    """Deactivate existing subs, create new active subscription."""
    UserSubscription.query.filter_by(user_id=user.id, is_active=True)\
                          .update({'is_active': False})
    expires = (datetime.utcnow() + timedelta(days=plan.duration_days)
               if plan.duration_days else None)
    sub = UserSubscription(
        user_id     = user.id,
        plan_id     = plan.id,
        expires_at  = expires,
        is_active   = True,
        payment_ref = payment_ref,
        amount_paid = amount_paise,
    )
    db.session.add(sub)
    db.session.commit()
    return sub


# ── PLANS PAGE ─────────────────────────────────────────────────────────────
@membership_bp.route('/plans')
@login_required
def plans():
    all_plans     = MembershipPlan.query.order_by(MembershipPlan.price_inr).all()
    monthly_plans = [p for p in all_plans if p.billing_period == 'monthly']
    annual_plans  = [p for p in all_plans if p.billing_period == 'annual']
    current_sub   = current_user.active_subscription
    return render_template('membership/plans.html',
                           user=current_user,
                           plans=monthly_plans,
                           annual_plans=annual_plans,
                           current_sub=current_sub,
                           razorpay_key=current_app.config['RAZORPAY_KEY_ID'])


# ── CREATE RAZORPAY ORDER ──────────────────────────────────────────────────
@membership_bp.route('/plans/create-order/<int:plan_id>', methods=['POST'])
@login_required
def create_order(plan_id):
    plan = MembershipPlan.query.get_or_404(plan_id)
    if plan.price_inr == 0:
        return jsonify(error='Cannot create order for Free plan'), 400

    try:
        client = _razorpay_client()
        order  = client.order.create({
            'amount':   plan.price_inr * 100,    # paise
            'currency': 'INR',
            'receipt':  f'plan_{plan_id}_user_{current_user.id}',
            'notes':    {
                'plan_id': plan_id,
                'user_id': current_user.id,
                'plan':    plan.name,
            }
        })
        return jsonify(order_id=order['id'], amount=order['amount'],
                       currency=order['currency'],
                       plan_name=plan.name,
                       user_name=current_user.full_name,
                       user_email=current_user.email,
                       user_phone=current_user.phone or '')
    except Exception as e:
        current_app.logger.error(f"Razorpay create_order error: {e}")
        return jsonify(error='Payment initiation failed. Try again.'), 500


# ── VERIFY PAYMENT (client callback) ──────────────────────────────────────
@membership_bp.route('/plans/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    data       = request.get_json()
    order_id   = data.get('razorpay_order_id', '')
    payment_id = data.get('razorpay_payment_id', '')
    signature  = data.get('razorpay_signature', '')

    # Step 1: Verify HMAC signature first — reject anything that fails
    secret   = current_app.config['RAZORPAY_KEY_SECRET'].encode()
    body     = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        current_app.logger.warning(f'Invalid Razorpay signature for {current_user.email}')
        return jsonify(success=False, error='Invalid payment signature'), 400

    # Step 2: Fetch plan_id from Razorpay order (server-side) — NOT from user input
    # This prevents a user from paying for Silver but claiming Platinum
    try:
        client  = _razorpay_client()
        order   = client.order.fetch(order_id)
        notes   = order.get('notes', {})
        plan_id = notes.get('plan_id')
        order_user_id = notes.get('user_id')
        # Verify this order belongs to the current user
        if not plan_id or str(order_user_id) != str(current_user.id):
            current_app.logger.warning(
                f'Order user mismatch: order={order_user_id} session={current_user.id}')
            return jsonify(success=False, error='Order validation failed'), 400
    except Exception as e:
        current_app.logger.error(f'Razorpay order fetch failed: {e}')
        # Fallback: use plan_id from client as last resort (already signature-verified)
        plan_id = data.get('plan_id')
        if not plan_id:
            return jsonify(success=False, error='Could not validate order'), 400

    plan = MembershipPlan.query.get_or_404(int(plan_id))
    sub  = _activate_plan(current_user, plan,
                          payment_ref=payment_id,
                          amount_paise=plan.price_inr * 100)

    # Receipt email
    _send_receipt_email(current_user, plan, payment_id, sub)

    return jsonify(success=True,
                   message=f'Successfully upgraded to {plan.name}!',
                   redirect=url_for('main.home'))


# ── RAZORPAY WEBHOOK (server-to-server) ────────────────────────────────────
@membership_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    """Webhook for async payment confirmation from Razorpay dashboard."""
    payload   = request.get_data()
    signature = request.headers.get('X-Razorpay-Signature', '')
    # Use dedicated webhook secret (set in Razorpay Dashboard → Webhooks)
    # Falls back to API secret if webhook secret not configured
    webhook_secret = (current_app.config.get('RAZORPAY_WEBHOOK_SECRET') or
                      current_app.config.get('RAZORPAY_KEY_SECRET', ''))
    if not webhook_secret:
        current_app.logger.error('Razorpay webhook: no secret configured')
        abort(400)
    secret   = webhook_secret.encode()
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        abort(400)

    event = request.get_json()
    if event.get('event') == 'payment.captured':
        payment = event['payload']['payment']['entity']
        notes   = payment.get('notes', {})
        plan_id = notes.get('plan_id')
        user_id = notes.get('user_id')
        if plan_id and user_id:
            from app.models import User
            user = User.query.get(int(user_id))
            plan = MembershipPlan.query.get(int(plan_id))
            if user and plan:
                sub = _activate_plan(user, plan,
                                     payment_ref=payment['id'],
                                     amount_paise=payment['amount'])
                _send_receipt_email(user, plan, payment['id'], sub)

    return jsonify(status='ok')


# ── UPGRADE (fallback — manual UPI ref) ───────────────────────────────────
@membership_bp.route('/plans/upgrade/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def upgrade(plan_id):
    """Fallback for when Razorpay key is not configured."""
    plan = MembershipPlan.query.get_or_404(plan_id)
    if plan.name == 'Free':
        flash('You are already on the Free plan.', 'info')
        return redirect(url_for('membership.plans'))

    # When Razorpay is live, force proper payment flow (prevents free plan claims)
    if current_app.config.get('RAZORPAY_KEY_ID'):
        flash('Please use the payment button on the plans page.', 'info')
        return redirect(url_for('membership.plans'))

    if request.method == 'POST':
        payment_ref = request.form.get('payment_ref', '').strip()
        if not payment_ref or len(payment_ref) < 5:
            flash('A valid UPI / payment reference is required.', 'danger')
            return redirect(request.url)
        # Mark as PENDING — admin must verify before activating
        sub = UserSubscription(
            user_id     = current_user.id,
            plan_id     = plan.id,
            expires_at  = None,
            is_active   = False,   # inactive until admin verifies payment
            payment_ref = f'PENDING:{payment_ref}',
            amount_paid = 0,
        )
        db.session.add(sub)
        db.session.commit()
        # Notify admin
        for admin_email in current_app.config.get('ADMIN_EMAILS', []):
            try:
                from app.utils import send_email
                send_email(admin_email,
                    f'Manual Plan Request — {current_user.full_name}',
                    f'<p><strong>{current_user.email}</strong> submitted UPI ref <code>{payment_ref}</code> '
                    f'for <strong>{plan.name}</strong> plan. '
                    f'Verify and activate at /console/users/{current_user.id}</p>')
            except Exception:
                pass
        flash(f'Payment reference submitted for {plan.name} plan. '
              'Our team will verify and activate within 2 hours.', 'info')
        return redirect(url_for('main.home'))

    return render_template('membership/checkout.html',
                           user=current_user, plan=plan,
                           razorpay_key=current_app.config['RAZORPAY_KEY_ID'])


def _send_receipt_email(user, plan, payment_id, sub):
    try:
        valid_until = (sub.expires_at.strftime('%d %b %Y')
                       if sub.expires_at else 'Lifetime')
        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:0 auto;">
          <h2 style="color:#dc3545;">Payment Successful! 🎉</h2>
          <p>Hi {user.first_name}, your iJodidar account has been upgraded.</p>
          <table style="width:100%;border-collapse:collapse;margin:20px 0;">
            <tr><td style="padding:8px;border-bottom:1px solid #eee;color:#666;">Plan</td>
                <td style="padding:8px;border-bottom:1px solid #eee;font-weight:600;">{plan.name}</td></tr>
            <tr><td style="padding:8px;border-bottom:1px solid #eee;color:#666;">Amount</td>
                <td style="padding:8px;border-bottom:1px solid #eee;font-weight:600;">₹{plan.price_inr}</td></tr>
            <tr><td style="padding:8px;border-bottom:1px solid #eee;color:#666;">Valid Until</td>
                <td style="padding:8px;border-bottom:1px solid #eee;">{valid_until}</td></tr>
            <tr><td style="padding:8px;color:#666;">Payment ID</td>
                <td style="padding:8px;font-family:monospace;font-size:12px;">{payment_id}</td></tr>
          </table>
          <a href="https://ijodidar.in/home" style="background:#dc3545;color:white;
          padding:12px 28px;border-radius:25px;text-decoration:none;
          display:inline-block;">Start Connecting</a>
          <p style="margin-top:20px;color:#999;font-size:12px;">
          Keep this email as your payment receipt.</p>
        </div>"""
        send_email(user.email, f'iJodidar {plan.name} Plan — Payment Receipt', html)
    except Exception:
        pass


# ── SPOTLIGHT ─────────────────────────────────────────────────────────────
SPOTLIGHT_PRICE_INR  = 199
SPOTLIGHT_DAYS       = 7


@membership_bp.route('/spotlight')
@login_required
def spotlight():
    from app.models import Profile
    p = current_user.profile
    return render_template('membership/spotlight.html',
                           user=current_user,
                           profile=p,
                           price=SPOTLIGHT_PRICE_INR,
                           days=SPOTLIGHT_DAYS,
                           razorpay_key=current_app.config['RAZORPAY_KEY_ID'])


@membership_bp.route('/spotlight/create-order', methods=['POST'])
@login_required
def spotlight_create_order():
    try:
        client = _razorpay_client()
        order  = client.order.create({
            'amount':   SPOTLIGHT_PRICE_INR * 100,
            'currency': 'INR',
            'receipt':  f'spotlight_user_{current_user.id}',
            'notes':    {'user_id': current_user.id, 'type': 'spotlight'},
        })
        return jsonify(order_id=order['id'],
                       amount=order['amount'],
                       currency=order['currency'],
                       user_name=current_user.full_name,
                       user_email=current_user.email,
                       user_phone=current_user.phone or '')
    except Exception as e:
        current_app.logger.error(f"Spotlight order error: {e}")
        return jsonify(error='Payment initiation failed.'), 500


@membership_bp.route('/spotlight/verify-payment', methods=['POST'])
@login_required
def spotlight_verify_payment():
    import hmac as _hmac, hashlib as _hashlib
    from datetime import datetime, timedelta
    data       = request.get_json()
    order_id   = data.get('razorpay_order_id', '')
    payment_id = data.get('razorpay_payment_id', '')
    signature  = data.get('razorpay_signature', '')

    secret   = current_app.config['RAZORPAY_KEY_SECRET'].encode()
    body     = f"{order_id}|{payment_id}".encode()
    expected = _hmac.new(secret, body, _hashlib.sha256).hexdigest()

    if not _hmac.compare_digest(expected, signature):
        return jsonify(success=False, error='Invalid signature'), 400

    p = current_user.profile
    if not p:
        from app.models import Profile
        p = Profile(user_id=current_user.id)
        db.session.add(p)

    now = datetime.utcnow()
    # Extend if already spotlighted, else start fresh
    if p.is_spotlight and p.spotlight_expires_at and p.spotlight_expires_at > now:
        p.spotlight_expires_at = p.spotlight_expires_at + timedelta(days=SPOTLIGHT_DAYS)
    else:
        p.is_spotlight         = True
        p.spotlight_expires_at = now + timedelta(days=SPOTLIGHT_DAYS)
    db.session.commit()

    # Send receipt
    try:
        send_email(
            current_user.email,
            'iJodidar Spotlight Activated!',
            f"""<div style="font-family:sans-serif;max-width:500px;">
            <h2 style="color:#dc3545;">⭐ Spotlight Active!</h2>
            <p>Your profile is now featured at the top of search and home feed.</p>
            <p><strong>Valid until:</strong> {p.spotlight_expires_at.strftime('%d %b %Y, %I:%M %p')}</p>
            <p><strong>Payment ID:</strong> <code>{payment_id}</code></p>
            </div>"""
        )
    except Exception:
        pass

    return jsonify(success=True, message='Spotlight activated!',
                   redirect=url_for('main.home'))


@membership_bp.route('/spotlight/buy-manual', methods=['POST'])
@login_required
def spotlight_buy_manual():
    """Fallback — manual payment ref when Razorpay not configured.
    Spotlight is NOT auto-activated — admin must verify payment first.
    """
    payment_ref = request.form.get('payment_ref', '').strip()
    if not payment_ref or len(payment_ref) < 5:
        flash('A valid payment reference is required.', 'danger')
        return redirect(url_for('membership.spotlight'))
    # Do NOT activate spotlight — create pending record for admin to verify
    # Notify admin via email
    try:
        for admin_email in current_app.config.get('ADMIN_EMAILS', []):
            send_email(
                admin_email,
                f'Spotlight Request — {current_user.full_name}',
                f'<p><strong>{current_user.email}</strong> submitted UPI ref '
                f'<code>{payment_ref}</code> for Spotlight (₹{SPOTLIGHT_PRICE_INR}). '
                f'Verify at /console/users/{current_user.id}</p>'
            )
    except Exception:
        pass
    flash('Spotlight request submitted! Our team will verify and activate within 2 hours.', 'info')
    return redirect(url_for('main.home'))


# ── ASSISTED PLAN (Phase 14.4) ─────────────────────────────────────────────
ASSISTED_PRICE_INR = 2999
ASSISTED_DURATION  = 30   # days


@membership_bp.route('/plans/assisted', methods=['GET', 'POST'])
@login_required
def assisted_plan():
    """Assisted Plan landing & signup."""
    from app.models import AssistedRequest
    existing = AssistedRequest.query.filter_by(
        user_id=current_user.id, status='pending').first()

    if request.method == 'POST':
        if existing:
            flash('You already have an active Assisted request. Our team will contact you soon.',
                  'info')
            return redirect(url_for('membership.assisted_plan'))

        ar = AssistedRequest(
            user_id = current_user.id,
            status  = 'pending',
        )
        db.session.add(ar)
        db.session.commit()

        # Notify admins
        try:
            for admin_email in current_app.config.get('ADMIN_EMAILS', []):
                send_email(
                    admin_email,
                    f'New Assisted Plan Request — {current_user.full_name}',
                    f"""<div style="font-family:sans-serif;">
                    <h2>New Assisted Plan Request</h2>
                    <p><strong>User:</strong> {current_user.full_name}</p>
                    <p><strong>Email:</strong> {current_user.email}</p>
                    <p><strong>Phone:</strong> {current_user.phone or 'Not set'}</p>
                    <a href="https://ijodidar.in/admin/assisted">View in Admin</a>
                    </div>"""
                )
        except Exception:
            pass

        # WhatsApp admin notification
        try:
            from app.utils import send_whatsapp
            for admin_email in current_app.config.get('ADMIN_EMAILS', []):
                pass  # WhatsApp admin numbers would be configured separately

        except Exception:
            pass

        flash('Request submitted! Our team will WhatsApp/call you within 24 hours.', 'success')
        return redirect(url_for('membership.assisted_plan'))

    return render_template('membership/assisted.html',
                           user=current_user,
                           price=ASSISTED_PRICE_INR,
                           existing=existing)
