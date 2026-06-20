"""
app/onboarding/routes.py — 6-Step Onboarding Wizard

Replaces the scattered 22-page profile flow for NEW users.
Forces completion of the minimum viable profile before accessing the home feed.
Existing users with profiles skip this entirely.

Steps:
  1. /onboarding/gender     — gender + looking_for (REQUIRED — enforced by before_request)
  2. /onboarding/basics     — DOB + religion + marital status
  3. /onboarding/career     — occupation + income
  4. /onboarding/photo      — upload primary photo
  5. /onboarding/preferences — partner preferences
  6. /onboarding/done       — redirect to home feed

Each step is skippable (except step 1 which is enforced by before_request).
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

TOTAL_STEPS = 5

def _get_or_create_profile():
    from app.models import Profile
    p = current_user.profile
    if not p:
        p = Profile(user_id=current_user.id)
        db.session.add(p)
    return p


# ── STEP 1: Gender + Looking For (REQUIRED) ────────────────────────────────
@onboarding_bp.route('/gender', methods=['GET', 'POST'])
@login_required
def set_gender():
    """Step 1 — Enforce gender + looking_for. Cannot be skipped."""
    if (current_user.profile and
            current_user.profile.gender and
            current_user.profile.looking_for):
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        gender      = request.form.get('gender', '').strip()
        looking_for = request.form.get('looking_for', '').strip()

        if gender not in ('Male', 'Female', 'Other'):
            flash('Please select your gender.', 'danger')
            return render_template('onboarding/gender.html', step=1, total=TOTAL_STEPS)
        if looking_for not in ('Male', 'Female', 'Any'):
            flash('Please select who you are looking for.', 'danger')
            return render_template('onboarding/gender.html', step=1, total=TOTAL_STEPS)

        p = _get_or_create_profile()
        p.gender      = gender
        p.looking_for = looking_for
        db.session.commit()
        return redirect(url_for('onboarding.basics'))

    return render_template('onboarding/gender.html', step=1, total=TOTAL_STEPS)


# ── STEP 2: Basics — DOB, Religion, Marital Status ────────────────────────
@onboarding_bp.route('/basics', methods=['GET', 'POST'])
@login_required
def basics():
    """Step 2 — DOB, religion, marital status."""
    RELIGIONS = ['Hindu', 'Muslim', 'Christian', 'Sikh', 'Buddhist',
                 'Jain', 'Parsi', 'No Religion', 'Other']
    MARITAL   = ['Never Married', 'Divorced', 'Widowed', 'Separated']

    if request.method == 'POST':
        if 'skip' in request.form:
            return redirect(url_for('onboarding.career'))

        mn  = request.form.get('month', '').strip()
        dv  = request.form.get('day', '').strip()
        yv  = request.form.get('year', '').strip()
        religion       = request.form.get('religion', '').strip()
        marital_status = request.form.get('marital_status', '').strip()

        p = _get_or_create_profile()
        if mn and dv and yv:
            try:
                dob = date(int(yv), int(mn), int(dv))
                today = date.today()
                age   = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if age < 18:
                    flash('You must be at least 18 years old.', 'danger')
                    return render_template('onboarding/basics.html',
                                           step=2, total=TOTAL_STEPS,
                                           religions=RELIGIONS, marital=MARITAL)
                p.date_of_birth = dob.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                flash('Invalid date. Please check.', 'danger')
                return render_template('onboarding/basics.html',
                                       step=2, total=TOTAL_STEPS,
                                       religions=RELIGIONS, marital=MARITAL)
        if religion:
            p.religion = religion
        if marital_status:
            p.marital_status = marital_status
        db.session.commit()
        return redirect(url_for('onboarding.career'))

    return render_template('onboarding/basics.html',
                           step=2, total=TOTAL_STEPS,
                           religions=RELIGIONS, marital=MARITAL,
                           profile=current_user.profile)


# ── STEP 3: Career — Occupation + Income ──────────────────────────────────
@onboarding_bp.route('/career', methods=['GET', 'POST'])
@login_required
def career():
    """Step 3 — Occupation and annual income."""
    INCOME_BANDS = [
        (0,   'Prefer not to say'),
        (3,   'Up to ₹3 LPA'),
        (5,   '₹3 – 5 LPA'),
        (10,  '₹5 – 10 LPA'),
        (15,  '₹10 – 15 LPA'),
        (25,  '₹15 – 25 LPA'),
        (50,  '₹25 – 50 LPA'),
        (100, '₹50 LPA+'),
    ]

    if request.method == 'POST':
        if 'skip' in request.form:
            return redirect(url_for('onboarding.photo'))

        from app.models import ProfessionalDetails
        pro = ProfessionalDetails.query.filter_by(user_id=current_user.id).first()
        if not pro:
            pro = ProfessionalDetails(user_id=current_user.id)
            db.session.add(pro)

        occupation = request.form.get('occupation', '').strip()
        income_lpa = request.form.get('income_lpa', '').strip()

        if occupation:
            pro.occupation = occupation
        if income_lpa and income_lpa.isdigit():
            pro.income_lpa = int(income_lpa)

        db.session.commit()
        return redirect(url_for('onboarding.photo'))

    from app.models import ProfessionalDetails
    pro = ProfessionalDetails.query.filter_by(user_id=current_user.id).first()
    return render_template('onboarding/career.html',
                           step=3, total=TOTAL_STEPS,
                           income_bands=INCOME_BANDS, pro=pro)


# ── STEP 4: Photo Upload ───────────────────────────────────────────────────
@onboarding_bp.route('/photo', methods=['GET', 'POST'])
@login_required
def photo():
    """Step 4 — Upload primary profile photo."""
    if request.method == 'POST':
        if 'skip' in request.form:
            return redirect(url_for('onboarding.preferences'))

        from app.utils import upload_image_to_s3
        from app.models import ProfileImage
        file = request.files.get('image')
        full_url, thumb_url, card_url, err = upload_image_to_s3(
            file, user_id=current_user.id)
        if err:
            flash(err, 'danger')
            return render_template('onboarding/photo.html',
                                   step=4, total=TOTAL_STEPS)

        # Make primary
        ProfileImage.query.filter_by(
            user_id=current_user.id, is_primary=True).update({'is_primary': False})
        db.session.add(ProfileImage(
            user_id=current_user.id,
            image_url=full_url, thumb_url=thumb_url,
            card_url=card_url, is_primary=True))
        db.session.commit()
        flash('Photo uploaded!', 'success')
        return redirect(url_for('onboarding.preferences'))

    return render_template('onboarding/photo.html',
                           step=4, total=TOTAL_STEPS, user=current_user)


# ── STEP 5: Partner Preferences ───────────────────────────────────────────
@onboarding_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Step 5 — Partner age range, religion, city preference."""
    RELIGIONS = ['', 'Hindu', 'Muslim', 'Christian', 'Sikh', 'Buddhist',
                 'Jain', 'Parsi', 'No Religion', 'Other']

    if request.method == 'POST':
        if 'skip' in request.form:
            return redirect(url_for('onboarding.done'))

        from app.models import PartnerPreference
        pref = current_user.partner_preference
        if not pref:
            pref = PartnerPreference(user_id=current_user.id)
            db.session.add(pref)

        min_age = request.form.get('min_age', '').strip()
        max_age = request.form.get('max_age', '').strip()
        religion = request.form.get('religion', '').strip()
        location = request.form.get('location_preference', '').strip()

        if min_age.isdigit(): pref.min_age = int(min_age)
        if max_age.isdigit(): pref.max_age = int(max_age)
        if religion: pref.religion = religion
        if location: pref.location_preference = location

        db.session.commit()
        return redirect(url_for('onboarding.done'))

    return render_template('onboarding/preferences.html',
                           step=5, total=TOTAL_STEPS,
                           religions=RELIGIONS,
                           profile=current_user.profile,
                           pref=current_user.partner_preference)


# ── DONE ──────────────────────────────────────────────────────────────────
@onboarding_bp.route('/done')
@login_required
def done():
    """Onboarding complete — redirect to home feed."""
    return render_template('onboarding/done.html', user=current_user)
