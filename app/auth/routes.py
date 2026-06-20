from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, session)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User, MembershipPlan, UserSubscription
from app.utils import generate_token, send_email
from app.auth.forms import (RegistrationForm, LoginForm,
                             ForgotPasswordForm, ResetPasswordForm)

auth_bp = Blueprint('auth', __name__)


# ── LOGIN ──────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.strip().lower()).first()

        # Account lockout check
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            from datetime import timezone
            mins_left = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
            flash(f'Account locked due to too many failed attempts. Try again in {mins_left} minute(s).', 'danger')
            return render_template('auth/login.html', form=form)

        if not user or not user.check_password(form.password.data):
            if user:
                # Track failed attempts
                user.failed_login_count = (user.failed_login_count or 0) + 1
                if user.failed_login_count >= 10:
                    from datetime import timedelta
                    user.locked_until       = datetime.utcnow() + timedelta(minutes=30)
                    user.failed_login_count = 0
                    db.session.commit()
                    flash('Too many failed attempts. Account locked for 30 minutes.', 'danger')
                    return render_template('auth/login.html', form=form)
                db.session.commit()
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_active_acc:
            flash('Your account has been suspended. Contact support.', 'danger')
            return render_template('auth/login.html', form=form)

        # Successful login — reset failed count
        user.failed_login_count = 0
        user.locked_until       = None
        db.session.commit()

        login_user(user, remember=form.remember.data)
        flash(f'Welcome back, {user.first_name}!', 'success')
        # Open redirect prevention — only allow relative URLs
        from urllib.parse import urlparse
        nxt = request.args.get('next', '')
        parsed = urlparse(nxt)
        if nxt and not parsed.netloc and not parsed.scheme and nxt.startswith('/'):
            return redirect(nxt)
        return redirect(url_for('main.home'))

    return render_template('auth/login.html', form=form)


# ── REGISTER ───────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    # Store ref code in session if present — persists even if user navigates away
    ref_code_param = request.args.get('ref', '').strip().upper()
    if ref_code_param:
        session['pending_ref_code'] = ref_code_param

    form = RegistrationForm()
    if form.validate_on_submit():
        token = generate_token()
        user  = User(
            username   = form.username.data.strip().lower(),
            first_name = form.firstname.data.strip(),
            last_name  = form.lastname.data.strip(),
            email      = form.email.data.strip().lower(),
            phone      = form.phone.data.strip(),
            verify_token       = token,
            verify_token_expiry = datetime.utcnow() + timedelta(hours=24),
            is_verified        = False,
            consented_at       = datetime.utcnow(),   # DPDP consent recorded
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        # Create Profile with DOB and gender_intent from registration
        from app.models import Profile
        profile = Profile(user_id=user.id)
        if form.date_of_birth.data:
            profile.date_of_birth = str(form.date_of_birth.data)  # YYYY-MM-DD
        db.session.add(profile)

        # Assign Free plan automatically
        free_plan = MembershipPlan.query.filter_by(name='Free').first()
        if free_plan:
            db.session.add(UserSubscription(
                user_id    = user.id,
                plan_id    = free_plan.id,
                expires_at = None,
                amount_paid = 0,
            ))
        db.session.commit()

        # Handle referral — check session cookie (more reliable than URL param)
        ref_code = session.pop('pending_ref_code', None) or request.args.get('ref', '').strip().upper()
        if ref_code:
            from app.models import Referral
            from flask import request as _req
            master_ref = Referral.query.filter_by(code=ref_code).filter(
                Referral.referred_id == None).first()
            if master_ref and master_ref.referrer_id != user.id:
                client_ip = _req.headers.get('X-Real-IP') or _req.remote_addr or ''
                new_ref = Referral(
                    referrer_id = master_ref.referrer_id,
                    referred_id = user.id,
                    code        = ref_code,
                    ip_address  = client_ip,
                )
                db.session.add(new_ref)
                db.session.commit()
                session['has_referral'] = True   # flag for welcome bonus after phone verify
                # NOTE: reward_referrer() and reward_referred() called in verify_phone()

        # Async email — Celery handles sending, register() returns immediately
        try:
            from app.tasks import send_verification_email_task, send_welcome_email_task
            send_verification_email_task.delay(user.id)
            send_welcome_email_task.delay(user.id)
        except Exception as e:
            current_app.logger.warning(f'Email task enqueue failed (Celery/Redis not running?): {e}')

        # Phone-first (C1): auto-login and send to phone verification immediately
        login_user(user)
        flash('Account created! Please verify your phone number to continue.', 'success')
        return redirect(url_for('auth.verify_phone'))

    # Show form errors as flash messages
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')

    return render_template('auth/register.html', form=form)


# ── VERIFY EMAIL ───────────────────────────────────────────────────────────
@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verify_token=token).first()
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))
    if user.is_verified:
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('auth.login'))
    # Check token expiry (24 hours)
    if user.verify_token_expiry and user.verify_token_expiry < datetime.utcnow():
        flash('Verification link has expired. Please register again or request a new link.', 'danger')
        return redirect(url_for('auth.login'))
    user.is_verified        = True
    user.verify_token       = None
    user.verify_token_expiry = None
    db.session.commit()
    flash('Email verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


# ── FORGOT PASSWORD ────────────────────────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user  = User.query.filter_by(email=email).first()
        # Always same message — prevents email enumeration
        flash('If that email is registered, you will receive a reset link shortly.',
              'info')
        if user:
            token  = generate_token()
            expiry = datetime.utcnow() + timedelta(hours=1)
            user.reset_token        = token
            user.reset_token_expiry = expiry
            db.session.commit()
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                from app.tasks import send_password_reset_email_task
                send_password_reset_email_task.delay(user.id, reset_url)
            except Exception as e:
                current_app.logger.warning(f'Password reset email failed: {e}')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


# ── RESET PASSWORD ─────────────────────────────────────────────────────────
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if (not user
            or not user.reset_token_expiry
            or user.reset_token_expiry < datetime.utcnow()):
        flash('Invalid or expired password reset link. Please request a new one.',
              'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token        = None
        user.reset_token_expiry = None
        db.session.commit()
        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')

    return render_template('auth/reset_password.html', form=form, token=token)


# ── LOGOUT ─────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))


# ── PHONE OTP ─────────────────────────────────────────────────────────────
def _send_sms_otp(phone, otp):
    """Send OTP via MSG91. In dev (no key): logs to console. Returns True on success."""
    import requests as req
    key         = current_app.config.get('MSG91_AUTH_KEY', '')
    template_id = current_app.config.get('MSG91_TEMPLATE_ID', '')

    if not key:
        current_app.logger.info(f"[DEV OTP] Phone: {phone}  OTP: {otp}")
        return True
    try:
        resp = req.post(
            "https://api.msg91.com/api/v5/otp",
            json={"template_id": template_id,
                  "mobile": f"91{phone}",
                  "authkey": key,
                  "otp": otp},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception as e:
        current_app.logger.error(f"MSG91 error: {e}")
        return False


@auth_bp.route('/send-phone-otp', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def send_phone_otp():
    import random
    phone = request.form.get('phone', '').strip()
    if not phone or len(phone) < 10:
        flash('Enter a valid 10-digit phone number.', 'danger')
        return redirect(url_for('profile.phone'))

    otp    = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=10)

    # Store hashed OTP — never store plaintext OTP in database
    from werkzeug.security import generate_password_hash
    current_user.phone            = phone
    current_user.phone_otp        = generate_password_hash(otp)   # hashed
    current_user.phone_otp_expiry = expiry
    db.session.commit()

    if _send_sms_otp(phone, otp):   # send plaintext OTP to user via SMS
        flash('OTP sent to your phone. Enter it below to verify.', 'success')
    else:
        flash('Could not send OTP. Please try again later.', 'danger')

    return redirect(url_for('auth.verify_phone'))


@auth_bp.route('/verify-phone', methods=['GET', 'POST'])
@login_required
def verify_phone():
    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        # Compare entered OTP against stored hash
        from werkzeug.security import check_password_hash
        otp_valid = (
            current_user.phone_otp
            and current_user.phone_otp_expiry
            and current_user.phone_otp_expiry > datetime.utcnow()
            and entered.isdigit()   # prevent timing attacks with non-digit input
            and check_password_hash(current_user.phone_otp, entered)
        )
        if otp_valid:
            current_user.phone_verified   = True
            current_user.phone_otp        = None
            current_user.phone_otp_expiry = None
            db.session.commit()

            # Trigger referral reward now that phone is verified
            from app.models import Referral
            from app.utils import reward_referrer, create_notification
            pending_ref = Referral.query.filter_by(
                referred_id=current_user.id, rewarded_at=None
            ).first()
            if pending_ref:
                referrer = User.query.get(pending_ref.referrer_id)
                if referrer and current_user.is_verified:
                    # Both email AND phone verified — safe to reward both sides
                    from app.utils import reward_referrer, reward_referred
                    reward_referrer(referrer)
                    pending_ref.rewarded_at = datetime.utcnow()

                    # Dual-sided: referred user also gets 15-day Silver
                    if not pending_ref.referred_rewarded_at:
                        reward_referred(current_user)
                        pending_ref.referred_rewarded_at = datetime.utcnow()

                    db.session.commit()
                    create_notification(
                        user_id    = referrer.id,
                        notif_type = 'system',
                        message    = f'🎉 {current_user.full_name} verified their phone via your referral link! You earned 1 month Silver.',
                        link       = '/referral',
                    )
                    create_notification(
                        user_id    = current_user.id,
                        notif_type = 'system',
                        message    = '🎁 Welcome bonus! You got 15 days Silver free for joining via referral.',
                        link       = '/plans',
                    )

            flash('Phone verified! Trust badge added to your profile.', 'success')
            return redirect(url_for('main.my_profile'))
        flash('Invalid or expired OTP. Please try again.', 'danger')
    return render_template('auth/verify_phone.html', user=current_user)


# ── AADHAAR / ID VERIFICATION (Phase 14.2) ────────────────────────────────
@auth_bp.route('/verify-id', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def verify_id():
    """Self-service Aadhaar OTP-based ID verification."""
    from app.utils import send_aadhaar_otp, verify_aadhaar_otp
    from flask import session

    # Already verified
    if current_user.profile and current_user.profile.id_verified:
        flash('Your profile is already ID Verified!', 'info')
        return redirect(url_for('main.my_profile'))

    if request.method == 'POST':
        step = request.form.get('step', 'send')

        if step == 'send':
            aadhaar = request.form.get('aadhaar', '').strip().replace(' ', '')
            if len(aadhaar) != 12 or not aadhaar.isdigit():
                flash('Enter a valid 12-digit Aadhaar number.', 'danger')
                return render_template('auth/verify_id.html', user=current_user, step='send')

            phone = current_user.phone or request.form.get('phone', '').strip()
            ok, ref_id, err = send_aadhaar_otp(aadhaar, phone)
            if ok:
                session['aadhaar_ref_id'] = ref_id
                session['aadhaar_last4']  = aadhaar[-4:]
                flash('OTP sent to your Aadhaar-linked mobile number.', 'success')
                return render_template('auth/verify_id.html',
                                       user=current_user, step='verify',
                                       last4=aadhaar[-4:])
            flash(f'Could not send OTP: {err}', 'danger')

        elif step == 'verify':
            otp    = request.form.get('otp', '').strip()
            ref_id = session.get('aadhaar_ref_id', '')
            ok, err = verify_aadhaar_otp(ref_id, otp, current_user)
            if ok:
                session.pop('aadhaar_ref_id', None)
                flash('🆔 Identity verified! Your profile now has an ID Verified badge.', 'success')
                return redirect(url_for('main.my_profile'))
            flash(f'Verification failed: {err}', 'danger')
            return render_template('auth/verify_id.html',
                                   user=current_user, step='verify',
                                   last4=session.get('aadhaar_last4', '****'))

    return render_template('auth/verify_id.html', user=current_user, step='send')
