"""
console/routes.py — Staff Business Console
Completely separate from the user-facing admin panel.
AdminUsers (CEO/VP/RM/Executive) log in here — NOT as matchmaking users.
"""
from functools import wraps
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session, jsonify)
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db, limiter
from app.models import (AdminUser, User, Profile, Interest, Message,
                        UserSubscription, MembershipPlan, AssistedRequest,
                        UserReport, Notification)

console_bp = Blueprint('console', __name__, url_prefix='/console')


def _audit(action, target_type=None, target_id=None, detail=None):
    """Write one immutable row to admin_audit_logs. Call after every state change."""
    from app.models import AdminAuditLog
    admin_id = session.get('console_admin_id')
    if not admin_id:
        return
    ip = request.headers.get('X-Real-IP') or request.remote_addr or ''
    log = AdminAuditLog(
        admin_id    = admin_id,
        action      = action,
        target_type = target_type,
        target_id   = target_id,
        detail      = str(detail) if detail else None,
        ip_address  = ip,
    )
    db.session.add(log)
    # NOTE: caller must call db.session.commit() — we don't commit here
    # to avoid partial transactions


# ── Auth helpers ───────────────────────────────────────────────────────────

def console_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'console_admin_id' not in session:
            return redirect(url_for('console.login'))
        return f(*args, **kwargs)
    return decorated


def perm_required(permission):
    """Role-based permission guard."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'console_admin_id' not in session:
                return redirect(url_for('console.login'))
            admin = AdminUser.query.get(session['console_admin_id'])
            if not admin or not admin.is_active:
                session.pop('console_admin_id', None)
                return redirect(url_for('console.login'))
            if not admin.can(permission):
                flash(f'Your role ({admin.role_label}) does not have access to this section.', 'danger')
                return redirect(url_for('console.dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_admin():
    admin_id = session.get('console_admin_id')
    return AdminUser.query.get(admin_id) if admin_id else None


# ── LOGIN / LOGOUT ─────────────────────────────────────────────────────────

@console_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")   # rate limit console login — defence in depth
def login():
    # Flask-level IP check (defence-in-depth alongside Nginx allow/deny)
    import os
    client_ip   = request.headers.get('X-Real-IP') or request.remote_addr or ''
    allowed_raw = os.environ.get('CONSOLE_ALLOWED_IPS', '')
    allowed     = [ip.strip() for ip in allowed_raw.split(',') if ip.strip()]
    if allowed and client_ip not in allowed:
        from flask import abort
        abort(404)   # 404 not 403 — don't reveal console exists

    if 'console_admin_id' in session:
        return redirect(url_for('console.dashboard'))

    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        admin    = AdminUser.query.filter_by(email=email).first()

        # Account lockout check
        if admin and admin.locked_until and admin.locked_until > datetime.utcnow():
            mins_left = max(1, int((admin.locked_until - datetime.utcnow()).total_seconds() / 60))
            error = f'Account locked due to too many failed attempts. Try again in {mins_left} minute(s).'
            # Log this for monitoring
            import logging
            logging.getLogger(__name__).warning(
                f'Console locked — login attempt blocked for {email} from {client_ip}')
            return render_template('console/login.html', error=error)

        if admin and admin.is_active and admin.check_password(password):
            # Password correct — check if TOTP is required
            if admin.totp_enabled:
                # Store temp session for TOTP verification step
                session['console_totp_pending'] = admin.id
                return redirect(url_for('console.totp_verify'))
            # No TOTP — complete login
            admin.failed_login_count = 0
            admin.locked_until       = None
            admin.last_login         = datetime.utcnow()
            db.session.commit()
            session['console_admin_id'] = admin.id
            session.permanent = True
            _audit('login', 'admin_user', admin.id, f"email={admin.email}")
            db.session.commit()
            return redirect(url_for('console.dashboard'))

        # Failed login — track attempts
        if admin:
            admin.failed_login_count = (admin.failed_login_count or 0) + 1
            if admin.failed_login_count >= 5:   # lower threshold for console (5 vs 10 for users)
                admin.locked_until       = datetime.utcnow() + timedelta(minutes=60)  # 1-hour lock
                admin.failed_login_count = 0
                db.session.commit()
                import logging
                logging.getLogger(__name__).critical(
                    f'Console login LOCKED after 5 failures: {email} from {client_ip}')
                error = 'Too many failed attempts. Account locked for 60 minutes.'
                return render_template('console/login.html', error=error)
            db.session.commit()

        error = 'Invalid email or password.'

    return render_template('console/login.html', error=error)


@console_bp.route('/logout')
def logout():
    session.pop('console_admin_id', None)
    session.pop('console_totp_pending', None)
    return redirect(url_for('console.login'))


# ── TOTP 2FA VERIFICATION ─────────────────────────────────────────────────

@console_bp.route('/totp-verify', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def totp_verify():
    """Step 2 of login — verify Google Authenticator code."""
    admin_id = session.get('console_totp_pending')
    if not admin_id:
        return redirect(url_for('console.login'))

    admin = AdminUser.query.get(admin_id)
    if not admin or not admin.is_active:
        session.pop('console_totp_pending', None)
        return redirect(url_for('console.login'))

    error = None
    if request.method == 'POST':
        code = request.form.get('totp_code', '').strip().replace(' ', '')
        if admin.verify_totp(code):
            session.pop('console_totp_pending', None)
            admin.failed_login_count = 0
            admin.locked_until       = None
            admin.last_login         = datetime.utcnow()
            db.session.commit()
            session['console_admin_id'] = admin.id
            session.permanent = True
            _audit('login_totp', 'admin_user', admin.id)
            db.session.commit()
            return redirect(url_for('console.dashboard'))
        else:
            admin.failed_login_count = (admin.failed_login_count or 0) + 1
            if admin.failed_login_count >= 5:
                admin.locked_until       = datetime.utcnow() + timedelta(minutes=60)
                admin.failed_login_count = 0
                session.pop('console_totp_pending', None)
            db.session.commit()
            error = 'Invalid code. Please try again.'

    return render_template('console/totp_verify.html', error=error)


@console_bp.route('/totp-setup', methods=['GET', 'POST'])
@console_login_required
def totp_setup():
    """Allow admin to set up or disable TOTP 2FA."""
    admin = get_current_admin()
    error = success = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate':
            admin.generate_totp_secret()
            db.session.commit()
            success = 'Secret generated. Scan the QR code with Google Authenticator.'
        elif action == 'enable':
            code = request.form.get('totp_code', '').strip()
            # Verify code before enabling
            if admin.totp_secret and admin.verify_totp(code):
                admin.totp_enabled    = True
                admin.totp_verified_at = datetime.utcnow()
                db.session.commit()
                _audit('enable_totp', 'admin_user', admin.id)
                db.session.commit()
                success = '2FA enabled successfully! You will need Google Authenticator on next login.'
            else:
                error = 'Invalid code. Please scan the QR code and try again.'
        elif action == 'disable':
            code = request.form.get('totp_code', '').strip()
            if admin.verify_totp(code):
                admin.totp_enabled  = False
                admin.totp_secret   = None
                _audit('disable_totp', 'admin_user', admin.id)
                db.session.commit()
                success = '2FA has been disabled.'
            else:
                error = 'Invalid code. Cannot disable 2FA without valid code.'

    # Generate QR code image as base64
    qr_data_url = None
    if admin.totp_secret:
        import qrcode, io, base64
        uri  = admin.get_totp_uri()
        qr   = qrcode.make(uri)
        buf  = io.BytesIO()
        qr.save(buf, format='PNG')
        qr_data_url = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

    return render_template('console/totp_setup.html',
                           admin=admin,
                           qr_data_url=qr_data_url,
                           error=error, success=success)


# ── DASHBOARD ─────────────────────────────────────────────────────────────

@console_bp.route('/')
@console_login_required
@perm_required('dashboard')
def dashboard():
    admin = get_current_admin()

    # Core KPIs — exclude staff users
    total_users    = User.query.filter_by(is_staff=False).count()
    verified_users = User.query.filter_by(is_verified=True, is_staff=False).count()
    week_ago       = datetime.utcnow() - timedelta(days=7)
    new_this_week  = User.query.filter(
        User.created_at >= week_ago, User.is_staff == False).count()

    total_matches  = Interest.query.filter_by(status='accepted').count()
    total_messages = Message.query.count()
    pending_reports= UserReport.query.filter_by(status='pending').count()

    # Revenue KPIs
    revenue_total  = db.session.query(func.sum(UserSubscription.amount_paid))\
                               .join(User)\
                               .filter(User.is_staff == False).scalar() or 0
    revenue_month  = db.session.query(func.sum(UserSubscription.amount_paid))\
                               .join(User)\
                               .filter(User.is_staff == False,
                                       UserSubscription.started_at >= datetime.utcnow()-timedelta(days=30))\
                               .scalar() or 0
    paying_users   = (UserSubscription.query
                      .join(User)
                      .filter(UserSubscription.is_active == True,
                              UserSubscription.amount_paid > 0,
                              User.is_staff == False).count())
    assisted_pending = AssistedRequest.query.filter_by(status='pending').count()

    # Gender split
    male_count   = Profile.query.join(User).filter(Profile.gender=='Male',   User.is_staff==False).count()
    female_count = Profile.query.join(User).filter(Profile.gender=='Female', User.is_staff==False).count()

    # Registrations last 7 days for sparkline
    days7 = [(datetime.utcnow()-timedelta(days=i)).date() for i in range(6,-1,-1)]
    reg_trend = []
    for d in days7:
        count = User.query.filter(
            func.date(User.created_at)==str(d), User.is_staff==False).count()
        reg_trend.append(count)

    # Recent user registrations (real users only)
    recent_users = (User.query
                    .filter_by(is_staff=False)
                    .order_by(User.created_at.desc()).limit(8).all())

    # Plan distribution
    plan_dist = (db.session.query(MembershipPlan.name, func.count(UserSubscription.id))
                 .join(MembershipPlan)
                 .join(User)
                 .filter(UserSubscription.is_active==True, User.is_staff==False)
                 .group_by(MembershipPlan.name).all())

    return render_template('console/dashboard.html',
                           admin=admin,
                           total_users=total_users,
                           verified_users=verified_users,
                           new_this_week=new_this_week,
                           total_matches=total_matches,
                           total_messages=total_messages,
                           pending_reports=pending_reports,
                           revenue_total=revenue_total // 100,
                           revenue_month=revenue_month // 100,
                           paying_users=paying_users,
                           assisted_pending=assisted_pending,
                           male_count=male_count,
                           female_count=female_count,
                           reg_trend=reg_trend,
                           days7=[d.strftime('%d %b') for d in days7],
                           recent_users=recent_users,
                           plan_dist=plan_dist,
                           zip=zip,
                           set=set)


# ── ANALYTICS ─────────────────────────────────────────────────────────────

@console_bp.route('/analytics')
@console_login_required
@perm_required('analytics')
def analytics():
    admin = get_current_admin()

    # Registrations — 30 days
    days_30 = datetime.utcnow() - timedelta(days=30)
    reg_rows = (db.session.query(
                    func.date(User.created_at).label('day'),
                    func.count(User.id).label('count'))
                .filter(User.created_at >= days_30, User.is_staff == False)
                .group_by(func.date(User.created_at))
                .order_by(func.date(User.created_at)).all())

    # Revenue — 12 months
    months_12 = datetime.utcnow() - timedelta(days=365)
    rev_rows = (db.session.query(
                    func.to_char(UserSubscription.started_at, 'YYYY-MM').label('month'),
                    func.sum(UserSubscription.amount_paid).label('total'))
                .join(User)
                .filter(UserSubscription.started_at >= months_12,
                        UserSubscription.amount_paid > 0,
                        User.is_staff == False)
                .group_by(func.to_char(UserSubscription.started_at, 'YYYY-MM'))
                .order_by(func.to_char(UserSubscription.started_at, 'YYYY-MM'))).all()

    # Interest funnel
    interests_sent     = Interest.query.count()
    interests_accepted = Interest.query.filter_by(status='accepted').count()
    interests_declined = Interest.query.filter_by(status='declined').count()
    interests_pending  = Interest.query.filter_by(status='pending').count()
    conversion_rate    = round((interests_accepted / max(interests_sent, 1)) * 100, 1)

    # Top cities by profile count
    city_rows = (db.session.query(
                     db.text('cities.name'), func.count(db.text('addresses.id')))
                 .select_from(db.text('addresses'))
                 .join(db.text('cities'), db.text('cities.id = addresses.city_id'))
                 .join(User, db.text('addresses.user_id = users.id'))
                 .filter(User.is_staff == False)
                 .group_by(db.text('cities.name'))
                 .order_by(func.count(db.text('addresses.id')).desc())
                 .limit(10).all()) if False else []  # simplified

    # Plan distribution
    plan_dist = (db.session.query(MembershipPlan.name, func.count(UserSubscription.id))
                 .join(MembershipPlan).join(User)
                 .filter(UserSubscription.is_active==True, User.is_staff==False)
                 .group_by(MembershipPlan.name).all())

    # Profile completion rate
    with_photo   = Profile.query.join(User).filter(User.is_staff==False).count()

    return render_template('console/analytics.html',
                           admin=admin,
                           reg_labels=[str(r.day) for r in reg_rows],
                           reg_data=[r.count for r in reg_rows],
                           rev_labels=[r.month for r in rev_rows],
                           rev_data=[int((r.total or 0)/100) for r in rev_rows],
                           interests_sent=interests_sent,
                           interests_accepted=interests_accepted,
                           interests_declined=interests_declined,
                           interests_pending=interests_pending,
                           conversion_rate=conversion_rate,
                           plan_dist=plan_dist)

# ── USER MANAGEMENT ────────────────────────────────────────────────────────

@console_bp.route('/users')
@console_login_required
@perm_required('users')
def users():
    admin = get_current_admin()
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '')
    filt = request.args.get('filter', 'all')

    query = User.query.filter_by(is_staff=False)   # NEVER show staff in user list

    if q:
        query = query.filter(
            (User.email.ilike(f'%{q}%')) |
            (User.username.ilike(f'%{q}%')) |
            (User.first_name.ilike(f'%{q}%')) |
            (User.last_name.ilike(f'%{q}%')) |
            (User.phone.ilike(f'%{q}%'))
        )
    if filt == 'verified':
        query = query.filter_by(is_verified=True)
    elif filt == 'unverified':
        query = query.filter_by(is_verified=False)
    elif filt == 'suspended':
        query = query.filter_by(is_active_acc=False)
    elif filt == 'paying':
        query = query.join(UserSubscription).filter(
            UserSubscription.is_active==True, UserSubscription.amount_paid > 0)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('console/users.html',
                           admin=admin, pagination=pagination, q=q, filter=filt)


@console_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@console_login_required
@perm_required('users')
def user_detail(user_id):
    admin = get_current_admin()
    u = User.query.filter_by(id=user_id, is_staff=False).first_or_404()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'toggle_active':
            u.is_active_acc = not u.is_active_acc
            flash(f"User {'activated' if u.is_active_acc else 'suspended'}.", 'success')
        elif action == 'toggle_verified':
            u.is_verified = not u.is_verified
            flash(f"Email verification {'granted' if u.is_verified else 'revoked'}.", 'success')
        elif action == 'grant_id_verified':
            if u.profile:
                u.profile.id_verified    = True
                u.profile.id_verified_at = datetime.utcnow()
                flash('ID Verified badge granted.', 'success')
        elif action == 'admin_note':
            # Create in-app notification as admin note to user
            note = request.form.get('note', '').strip()
            if note:
                from app.utils import create_notification
                create_notification(u.id, 'system', f'[Staff message] {note}', '')
                flash('Note sent to user as notification.', 'success')
        db.session.commit()
        return redirect(url_for('console.user_detail', user_id=user_id))

    interests_sent     = Interest.query.filter_by(sender_id=u.id).count()
    interests_received = Interest.query.filter_by(receiver_id=u.id).count()
    accepted           = Interest.query.filter(
        (Interest.sender_id==u.id)|(Interest.receiver_id==u.id),
        Interest.status=='accepted').count()

    return render_template('console/user_detail.html',
                           admin=admin, u=u,
                           interests_sent=interests_sent,
                           interests_received=interests_received,
                           accepted=accepted)


# ── REPORTS ────────────────────────────────────────────────────────────────

@console_bp.route('/reports')
@console_login_required
@perm_required('reports')
def reports():
    admin  = get_current_admin()
    status = request.args.get('status', 'pending')
    items  = (UserReport.query.filter_by(status=status)
              .order_by(UserReport.created_at.desc()).all())
    return render_template('console/reports.html',
                           admin=admin, items=items, status=status)


@console_bp.route('/reports/<int:report_id>/<action>', methods=['POST'])
@console_login_required
@perm_required('reports')
def handle_report(report_id, action):
    from app.models import UserReport
    r = UserReport.query.get_or_404(report_id)
    if action == 'dismiss':
        r.status = 'dismissed'
        _audit('dismiss_report', 'report', r.id)
    elif action == 'suspend':
        r.status = 'reviewed'
        r.reported.is_active_acc = False
        _audit('suspend_reported_user', 'user', r.reported_id,
               f"report_id={r.id} reason={r.reason}")
    db.session.commit()
    flash(f'Report {action}ed.', 'success')
    return redirect(url_for('console.reports'))


# ── ASSISTED PLANS (Relationship Manager focus) ────────────────────────────

@console_bp.route('/assisted')
@console_login_required
@perm_required('assisted')
def assisted():
    admin = get_current_admin()
    status = request.args.get('status', 'all')
    query  = AssistedRequest.query

    # RMs only see their own assignments
    if admin.role == 'relationship_manager':
        query = query.filter_by(assigned_manager=admin.name)
    elif status != 'all':
        query = query.filter_by(status=status)

    requests_list = query.order_by(AssistedRequest.created_at.desc()).all()
    return render_template('console/assisted.html',
                           admin=admin, requests=requests_list, status=status)


@console_bp.route('/assisted/<int:req_id>/update', methods=['POST'])
@console_login_required
@perm_required('assisted')
def update_assisted(req_id):
    from app.models import RMContactLog
    ar = AssistedRequest.query.get_or_404(req_id)
    admin = get_current_admin()
    old_status = ar.status

    ar.assigned_manager    = request.form.get('manager', '').strip() or None
    ar.manager_phone       = request.form.get('manager_phone', '').strip() or None
    ar.notes               = request.form.get('notes', '').strip() or None
    ar.family_pref_notes   = request.form.get('family_pref_notes', '').strip() or None
    ar.status              = request.form.get('status', ar.status)
    ar.plan_tier           = request.form.get('plan_tier', ar.plan_tier or 'basic')

    # Assign current RM if not already assigned
    if admin.role == 'relationship_manager' and not ar.assigned_rm_id:
        ar.assigned_rm_id   = admin.id
        ar.assigned_manager = admin.name

    db.session.commit()

    if ar.status == 'active' and old_status != 'active':
        from app.utils import create_notification
        create_notification(ar.user_id, 'system',
            f'Your Assisted Plan is now active! {ar.assigned_manager or "Your manager"} will contact you soon.',
            '/plans/assisted')

    _audit('update_assisted', 'assisted_request', ar.id,
           f"status={ar.status} manager={ar.assigned_manager}")
    db.session.commit()
    flash('Updated.', 'success')
    return redirect(url_for('console.assisted_detail', req_id=req_id))


@console_bp.route('/assisted/<int:req_id>', methods=['GET'])
@console_login_required
@perm_required('assisted')
def assisted_detail(req_id):
    """Detailed RM workflow view for one assisted request."""
    from app.models import RMContactLog
    ar    = AssistedRequest.query.get_or_404(req_id)
    admin = get_current_admin()
    return render_template('console/assisted_detail.html',
                           admin=admin, ar=ar,
                           CONTACT_TYPES=['call','whatsapp','email','meeting',
                                          'profile_shared','outcome_noted'],
                           OUTCOMES=['interested','not_interested','meeting_arranged',
                                     'family_approved','pending'])


@console_bp.route('/assisted/<int:req_id>/log', methods=['POST'])
@console_login_required
@perm_required('assisted')
def add_contact_log(req_id):
    """Add an RM contact log entry."""
    from app.models import RMContactLog
    ar    = AssistedRequest.query.get_or_404(req_id)
    admin = get_current_admin()

    log = RMContactLog(
        request_id   = ar.id,
        admin_id     = admin.id,
        contact_type = request.form.get('contact_type', 'call').strip(),
        summary      = request.form.get('summary', '').strip()[:1000],
        outcome      = request.form.get('outcome', '').strip() or None,
        next_action  = request.form.get('next_action', '').strip() or None,
    )
    # Track profiles sent count
    if log.contact_type == 'profile_shared':
        ar.profiles_sent = (ar.profiles_sent or 0) + 1
    db.session.add(log)
    db.session.commit()
    flash('Contact log added.', 'success')
    return redirect(url_for('console.assisted_detail', req_id=req_id))


# ── STAFF MANAGEMENT (CEO only) ────────────────────────────────────────────

@console_bp.route('/staff')
@console_login_required
@perm_required('staff')
def staff():
    admin = get_current_admin()
    staff_list = AdminUser.query.order_by(AdminUser.created_at.desc()).all()
    return render_template('console/staff.html',
                           admin=admin, staff_list=staff_list)


@console_bp.route('/staff/add', methods=['POST'])
@console_login_required
@perm_required('staff')
def add_staff():
    admin = get_current_admin()
    name  = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    role  = request.form.get('role', 'executive')
    pwd   = request.form.get('password', '').strip()

    if AdminUser.query.filter_by(email=email).first():
        flash('Email already registered as staff.', 'danger')
        return redirect(url_for('console.staff'))

    a = AdminUser(name=name, email=email, role=role, created_by_id=admin.id)
    a.set_password(pwd)
    db.session.add(a)
    db.session.commit()
    flash(f'{name} added as {a.role_label}.', 'success')
    return redirect(url_for('console.staff'))


@console_bp.route('/staff/<int:staff_id>/toggle', methods=['POST'])
@console_login_required
@perm_required('staff')
def toggle_staff(staff_id):
    admin = get_current_admin()
    a = AdminUser.query.get_or_404(staff_id)
    if a.id == admin.id:
        flash('Cannot deactivate your own account.', 'danger')
        return redirect(url_for('console.staff'))
    a.is_active = not a.is_active
    db.session.commit()
    flash(f'Staff account {"activated" if a.is_active else "deactivated"}.', 'success')
    return redirect(url_for('console.staff'))


# ── API endpoints for dashboard widgets ────────────────────────────────────

# ── ACTIVATE PENDING MANUAL SUBSCRIPTION (admin verification) ─────────────
@console_bp.route('/users/<int:user_id>/activate-sub/<int:sub_id>', methods=['POST'])
@console_login_required
@perm_required('users')
def activate_subscription(user_id, sub_id):
    """Manually activate a pending subscription after verifying UPI payment."""
    from app.models import UserSubscription, User
    sub = UserSubscription.query.filter_by(
        id=sub_id, user_id=user_id, is_active=False).first_or_404()
    # Remove PENDING: prefix from payment_ref
    if sub.payment_ref and sub.payment_ref.startswith('PENDING:'):
        sub.payment_ref = sub.payment_ref[8:]
    sub.is_active   = True
    sub.amount_paid = sub.plan.price_inr * 100
    from datetime import datetime, timedelta
    if sub.plan.duration_days:
        sub.expires_at = datetime.utcnow() + timedelta(days=sub.plan.duration_days)
    # Deactivate other subs
    UserSubscription.query.filter(
        UserSubscription.user_id == user_id,
        UserSubscription.id      != sub_id,
        UserSubscription.is_active == True
    ).update({'is_active': False})
    db.session.commit()
    # Notify user
    from app.utils import create_notification
    create_notification(user_id, 'system',
        f'Your {sub.plan.name} plan is now active! Welcome to iJodidar {sub.plan.name}.',
        '/plans')
    flash(f'{sub.plan.name} plan activated for user #{user_id}.', 'success')
    return redirect(url_for('console.user_detail', user_id=user_id))


@console_bp.route('/api/live-stats')
@console_login_required
def api_live_stats():
    """Polled every 60s by dashboard for live counts."""
    return jsonify(
        total_users    = User.query.filter_by(is_staff=False).count(),
        online_today   = User.query.filter(
            User.updated_at >= datetime.utcnow()-timedelta(hours=24),
            User.is_staff == False).count(),
        pending_reports= UserReport.query.filter_by(status='pending').count(),
        assisted_pending= AssistedRequest.query.filter_by(status='pending').count(),
    )
