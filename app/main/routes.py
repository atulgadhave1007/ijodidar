from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from app.models import (User, Profile, Address, City, ProfileView,
                        Interest, BlockList, Shortlist)
from app import db
from app.utils import calculate_profile_completeness, calculate_match_score
from datetime import datetime, date, timedelta

main_bp = Blueprint('main', __name__)


def _blocked_ids(user_id):
    rows = BlockList.query.filter(
        or_(BlockList.blocker_id == user_id,
            BlockList.blocked_id  == user_id)
    ).all()
    ids = set()
    for r in rows:
        ids.add(r.blocker_id)
        ids.add(r.blocked_id)
    ids.discard(user_id)
    return ids


# ── PUBLIC LANDING ─────────────────────────────────────────────────────────
@main_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    total_users   = User.query.filter_by(is_active_acc=True, is_staff=False).count()
    total_matches = Interest.query.filter_by(status='accepted').count()
    return render_template('main/landing.html',
                           total_users=total_users, total_matches=total_matches)


# ── HOME FEED (match-score sorted) ────────────────────────────────────────
@main_bp.route('/home')
@login_required
def home():
    blocked = _blocked_ids(current_user.id)
    gender      = current_user.profile.gender      if current_user.profile else None
    looking_for = current_user.profile.looking_for if current_user.profile else None

    q = (User.query
         .join(Profile)
         .filter(
             User.id            != current_user.id,
             User.is_active_acc == True,
             User.is_hidden     == False,
             User.is_staff      == False,   # exclude staff from match feed
         ))
    if blocked:
        q = q.filter(User.id.notin_(blocked))
    # Filter by what user is looking for (correct) — not just "not same gender"
    if looking_for:
        q = q.filter(Profile.gender == looking_for)
    elif gender:
        q = q.filter(Profile.gender != gender)   # fallback if looking_for not set

    # Apply partner preferences (religion, marital status, age range)
    pref = current_user.partner_preference
    if pref:
        if pref.religion:
            q = q.filter(Profile.religion == pref.religion)
        if pref.marital_status:
            q = q.filter(Profile.marital_status == pref.marital_status)
        if pref.manglik:
            q = q.filter(Profile.manglik == pref.manglik)
        if pref.min_age or pref.max_age:
            from datetime import date
            today = date.today()
            if pref.min_age:
                max_dob = f'{today.year - pref.min_age}-12-31'
                q = q.filter(Profile.date_of_birth <= max_dob)
            if pref.max_age:
                min_dob = f'{today.year - pref.max_age}-01-01'
                q = q.filter(Profile.date_of_birth >= min_dob)

    # Eager load related data — prevents N+1 queries (was ~320 queries for 80 users)
    q = q.options(
        joinedload(User.profile),
        selectinload(User.profile_images),
        selectinload(User.subscriptions),
        selectinload(User.addresses).joinedload(Address.city),
    )
    candidates = q.limit(80).all()   # fetch more, score, then take top 24

    # Expire spotlight profiles — do it in one DB update, not a Python loop
    from datetime import datetime as _dt
    now_dt = _dt.utcnow()
    expired_ids = [
        c.profile.id for c in candidates
        if c.profile and c.profile.is_spotlight
        and c.profile.spotlight_expires_at
        and c.profile.spotlight_expires_at < now_dt
    ]
    if expired_ids:
        Profile.query.filter(Profile.id.in_(expired_ids)).update(
            {'is_spotlight': False}, synchronize_session='fetch')
        db.session.commit()

    # Score each candidate — spotlight does NOT inflate score (integrity preserved)
    # Signal boost: past behavior towards this candidate adjusts score
    from app.utils import get_signal_boost
    scored = []
    spotlight_users = []
    for c in candidates:
        score = calculate_match_score(current_user, c)
        boost = get_signal_boost(current_user.id, c.id)
        score = max(0, min(100, score + boost))   # clamp 0-100
        if c.profile and c.profile.is_spotlight:
            spotlight_users.append((score, c))   # separate list
        else:
            scored.append((score, c))

    # Sort by genuine match score
    scored.sort(key=lambda x: x[0], reverse=True)
    spotlight_users.sort(key=lambda x: x[0], reverse=True)

    # Spotlight users take top 3 positions (guaranteed visibility), rest fill in order
    top_spotlight = spotlight_users[:3]
    remaining     = scored[:24 - len(top_spotlight)]
    top           = top_spotlight + remaining

    return render_template('main/home.html',
                           scored_users=top,
                           spotlight_count=len(top_spotlight),
                           user=current_user,
                           has_preferences=bool(current_user.partner_preference))


# ── MY PROFILE ─────────────────────────────────────────────────────────────
@main_bp.route('/my_profile')
@login_required
def my_profile():
    return redirect(url_for('main.user_profile', username=current_user.username))


# ── USER PROFILE VIEW ──────────────────────────────────────────────────────
@main_bp.route('/<username>')
@login_required
def user_profile(username):
    user           = User.query.filter_by(username=username).first_or_404()
    is_own_profile = (user.id == current_user.id)

    if not is_own_profile:
        block = BlockList.query.filter(
            or_(
                (BlockList.blocker_id == current_user.id) & (BlockList.blocked_id == user.id),
                (BlockList.blocker_id == user.id)         & (BlockList.blocked_id == current_user.id),
            )
        ).first()
        if block:
            abort(404)

    # Track view + notify (once per 24h per viewer)
    if not is_own_profile:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        views  = (ProfileView.query
                  .filter_by(viewer_id=current_user.id, viewed_id=user.id)
                  .filter(ProfileView.timestamp >= cutoff)
                  .count())
        if views == 0:
            db.session.add(ProfileView(viewer_id=current_user.id,
                                       viewed_id=user.id,
                                       timestamp=datetime.utcnow()))
            db.session.commit()
            # Notify profile owner
            from app.utils import create_notification
            create_notification(
                user_id    = user.id,
                notif_type = 'profile_viewed',
                message    = f'{current_user.full_name} viewed your profile.',
                link       = f'/{current_user.username}',
            )
        else:
            db.session.commit()

    interest_sent = interest_received = None
    if not is_own_profile:
        interest_sent     = Interest.query.filter_by(
            sender_id=current_user.id, receiver_id=user.id).first()
        interest_received = Interest.query.filter_by(
            sender_id=user.id, receiver_id=current_user.id).first()

    is_connected = bool(
        (interest_sent     and interest_sent.status     == 'accepted') or
        (interest_received and interest_received.status == 'accepted')
    )
    is_shortlisted = (
        bool(Shortlist.query.filter_by(
            user_id=current_user.id, shortlisted_id=user.id).first())
        if not is_own_profile else False
    )
    is_blocked = (
        bool(BlockList.query.filter_by(
            blocker_id=current_user.id, blocked_id=user.id).first())
        if not is_own_profile else False
    )

    viewed_by_users = []
    if is_own_profile:
        recent = (ProfileView.query
                  .filter_by(viewed_id=current_user.id)
                  .order_by(ProfileView.timestamp.desc())
                  .limit(12).all())
        seen = set()
        for v in recent:
            if v.viewer_id not in seen:
                seen.add(v.viewer_id)
                viewed_by_users.append(v.viewer)
            if len(viewed_by_users) >= 5:
                break

    other_users = []
    blocked_set = _blocked_ids(current_user.id)
    if current_user.addresses:
        city_obj = current_user.addresses[0].city
        if city_obj:
            og          = current_user.profile.gender      if current_user.profile else None
            looking_for = current_user.profile.looking_for if current_user.profile else None
            q2 = (User.query.join(Profile).join(Address).join(City)
                  .filter(User.id != current_user.id,
                          User.is_active_acc == True,
                          User.is_hidden     == False,
                          User.is_staff      == False,
                          City.id            == city_obj.id))
            if looking_for:
                q2 = q2.filter(Profile.gender == looking_for)
            elif og:
                q2 = q2.filter(Profile.gender != og)
            if blocked_set:
                q2 = q2.filter(User.id.notin_(blocked_set))
            other_users = q2.limit(5).all()

    profile_score = calculate_profile_completeness(user)
    show_phone    = is_own_profile or (
        is_connected and
        bool(current_user.active_subscription and
             current_user.active_subscription.plan.can_view_phone)
    )
    match_score = (calculate_match_score(current_user, user)
                   if not is_own_profile else None)

    # Expire spotlight if past expiry date
    if user.profile and user.profile.is_spotlight:
        from datetime import datetime as _dt
        if (user.profile.spotlight_expires_at
                and user.profile.spotlight_expires_at < _dt.utcnow()):
            user.profile.is_spotlight = False
            db.session.commit()

    # Manglik compatibility
    manglik_info = None
    if not is_own_profile and user.profile and current_user.profile:
        from app.utils import manglik_compatible
        compat, msg = manglik_compatible(current_user.profile, user.profile)
        if user.profile.manglik or (current_user.profile and current_user.profile.manglik):
            manglik_info = {'compatible': compat, 'message': msg}

    return render_template(
        'main/my_profile.html',
        user=user, profile=user.profile,
        profile_score=profile_score,
        other_users=other_users,
        viewed_by_users=viewed_by_users,
        is_own_profile=is_own_profile,
        is_connected=is_connected,
        is_shortlisted=is_shortlisted,
        is_blocked=is_blocked,
        interest_sent=interest_sent,
        interest_received=interest_received,
        show_phone=show_phone,
        match_score=match_score,
        manglik_info=manglik_info,
    )


# ── SITEMAP ────────────────────────────────────────────────────────────────
# ── PRIVACY POLICY ────────────────────────────────────────────────────────
@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('main/privacy_policy.html')


# ── TERMS OF SERVICE ──────────────────────────────────────────────────────
@main_bp.route('/terms')
def terms():
    return render_template('main/terms.html')


# ── ACCOUNT DELETION (DPDP Compliance) ────────────────────────────────────
@main_bp.route('/account/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    """DPDP Act: user right to erasure — anonymize all personal data."""
    from flask_login import logout_user
    if request.method == 'POST':
        confirm = request.form.get('confirm', '').strip().lower()
        password = request.form.get('password', '').strip()
        if confirm != 'delete' or not current_user.check_password(password):
            flash('Incorrect confirmation. Enter your password and type DELETE.', 'danger')
            return redirect(url_for('main.delete_account'))

        user = current_user._get_current_object()
        user_id = user.id

        # Anonymize personal data (keep structure for DB integrity)
        import secrets as _sec
        anon_id = _sec.token_hex(8)
        user.first_name  = 'Deleted'
        user.last_name   = 'User'
        user.email       = f'deleted_{anon_id}@ijodidar.deleted'
        user.phone       = None
        user.username    = f'deleted_{anon_id}'
        user.password_hash = 'deleted'
        user.is_active_acc = False
        user.is_hidden     = True
        user.verify_token  = None
        user.reset_token   = None

        # Clear profile personal details
        if user.profile:
            user.profile.bio           = None
            user.profile.linkedin_url  = None
            user.profile.birth_village = None
            user.profile.birth_city    = None

        # Delete profile photos, notifications, family details
        from app.models import ProfileImage, Notification, PhoneAlternate
        from app.utils import delete_image_from_s3
        for img in user.profile_images:
            try:
                delete_image_from_s3(img.image_url)
            except Exception:
                pass
        ProfileImage.query.filter_by(user_id=user_id).delete()
        Notification.query.filter_by(user_id=user_id).delete()
        PhoneAlternate.query.filter_by(user_id=user_id).delete()

        db.session.commit()
        logout_user()
        flash('Your account has been deleted. Thank you for using iJodidar.', 'info')
        return redirect(url_for('main.landing'))

    return render_template('main/delete_account.html', user=current_user)


# ── LEGAL PAGES (DPDP compliance) ─────────────────────────────────────────
@main_bp.route('/sitemap.xml')
def sitemap():
    from flask import Response
    from flask import request as _req
    base = f"{_req.scheme}://{_req.host}"
    users = (User.query
             .filter_by(is_active_acc=True, is_hidden=False,
                        is_verified=True, is_staff=False)
             .limit(5000).all())
    pages = [
        f'<url><loc>{base}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'<url><loc>{base}/search</loc><changefreq>hourly</changefreq><priority>0.9</priority></url>',
        f'<url><loc>{base}/success-stories</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>',
    ]
    for u in users:
        pages.append(
            f'<url><loc>{base}/{u.username}</loc>'
            f'<changefreq>weekly</changefreq><priority>0.6</priority></url>'
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + ''.join(pages) + '</urlset>')
    return Response(xml, mimetype='application/xml')


# ── SUCCESS STORIES ────────────────────────────────────────────────────────
@main_bp.route('/success-stories')
def success_stories():
    from app.models import SuccessStory
    stories = (SuccessStory.query
               .filter_by(is_published=True)
               .order_by(SuccessStory.created_at.desc()).all())
    return render_template('main/success_stories.html', stories=stories)
