from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from app import db, limiter
from app.models import (User, Profile, Address, City, State, Country,
                        Education, ProfessionalDetails, PhoneAlternate,
                        ProfileImage, Language)
from app.utils import upload_image_to_s3, delete_image_from_s3

profile_bp = Blueprint('profile', __name__)


def _get_or_create_profile():
    p = current_user.profile
    if not p:
        p = Profile(user_id=current_user.id)
        db.session.add(p)
    return p


@profile_bp.route('/profile')
@login_required
def profile():
    u   = current_user
    pro = ProfessionalDetails.query.filter_by(user_id=u.id).first()
    edu = Education.query.filter_by(user_id=u.id).first()
    permanent = Address.query.filter_by(user_id=u.id, tag='Permanent').first()
    current_a = Address.query.filter_by(user_id=u.id, tag='Current').first()
    work      = Address.query.filter_by(user_id=u.id, tag='Work').first()
    return render_template('profile/profile.html', user=u,
                           profile=u.profile, professional=pro, education=edu,
                           permanent=permanent, current=current_a, work=work)


@profile_bp.route('/name', methods=['GET', 'POST'])
@login_required
def name():
    if request.method == 'POST':
        fn = request.form.get('firstName', '').strip()
        ln = request.form.get('lastName',  '').strip()
        if not fn or not ln:
            flash('Name fields cannot be empty.', 'danger')
        else:
            current_user.first_name = fn
            current_user.last_name  = ln
            db.session.commit()
            flash('Name updated.', 'success')
            return redirect(url_for('profile.profile'))
    return render_template('profile/name.html', user=current_user)


@profile_bp.route('/gender', methods=['GET', 'POST'])
@login_required
def gender():
    p = _get_or_create_profile() if request.method == 'POST' else current_user.profile
    if request.method == 'POST':
        val = request.form.get('gender')
        if not val:
            flash('Please select a gender.', 'danger')
        else:
            p.gender = val
            db.session.commit()
            flash('Gender updated.', 'success')
            return redirect(url_for('profile.profile'))
    return render_template('profile/gender.html', user=current_user, profile=current_user.profile)


@profile_bp.route('/looking_for', methods=['GET', 'POST'])
@login_required
def looking_for():
    if request.method == 'POST':
        p = _get_or_create_profile()
        p.looking_for = request.form.get('looking_for', '')
        db.session.commit()
        flash('Preference updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/looking_for.html', user=current_user, profile=current_user.profile)


@profile_bp.route('/birthday', methods=['GET', 'POST'])
@login_required
def birthday():
    p = current_user.profile
    month = day = year = None
    birth_time = birth_village = birth_city = birth_state = birth_country = ''
    if p and p.date_of_birth:
        try:
            dob = datetime.strptime(p.date_of_birth, '%Y-%m-%d')
            month, day, year = dob.strftime('%B'), dob.day, dob.year
        except Exception:
            pass
    if p:
        birth_time    = p.birth_time    or ''
        birth_village = p.birth_village or ''
        birth_city    = p.birth_city    or ''
        birth_state   = p.birth_state   or ''
        birth_country = p.birth_country or ''

    if request.method == 'POST':
        mn, dv, yv = request.form.get('month'), request.form.get('date'), request.form.get('year')
        birth_time    = request.form.get('birth_time', '').strip()
        birth_village = request.form.get('birth_village', '').strip()
        birth_city    = request.form.get('birth_city', '').strip()
        birth_state   = request.form.get('birth_state', '').strip()
        birth_country = request.form.get('birth_country', '').strip()
        if not all([mn, dv, yv]):
            flash('Month, day and year are required.', 'danger')
        else:
            try:
                m   = datetime.strptime(mn, '%B').month
                dob = datetime(int(yv), m, int(dv)).date()
                p   = _get_or_create_profile()
                p.date_of_birth = dob.strftime('%Y-%m-%d')
                p.birth_time    = birth_time
                p.birth_village = birth_village
                p.birth_city    = birth_city
                p.birth_state   = birth_state
                p.birth_country = birth_country
                db.session.commit()
                flash('Birth details updated.', 'success')
                return redirect(url_for('profile.profile'))
            except Exception:
                flash('Invalid date. Please check.', 'danger')
    return render_template('profile/birthday.html', user=current_user, profile=p,
                           month=month, day=day, year=year,
                           birth_time=birth_time, birth_village=birth_village,
                           birth_city=birth_city, birth_state=birth_state,
                           birth_country=birth_country)


@profile_bp.route('/bio', methods=['GET', 'POST'])
@login_required
def bio():
    if request.method == 'POST':
        p = _get_or_create_profile()
        p.bio = request.form.get('bio', '').strip()[:1000]
        db.session.commit()
        flash('About me updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/bio.html', user=current_user, profile=current_user.profile)


@profile_bp.route('/height', methods=['GET', 'POST'])
@login_required
def height():
    if request.method == 'POST':
        p = _get_or_create_profile()
        val = request.form.get('height', '').strip()
        p.height = int(val) if val.isdigit() else None
        db.session.commit()
        flash('Height updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/height.html', user=current_user, profile=current_user.profile)


@profile_bp.route('/religion', methods=['GET', 'POST'])
@login_required
def religion():
    from app.utils_kundli import MARATHI_SUB_CASTES
    p = _get_or_create_profile()
    if request.method == 'POST':
        p.religion          = request.form.get('religion', '').strip() or None
        p.caste             = request.form.get('caste', '').strip() or None
        p.sub_caste         = request.form.get('sub_caste', '').strip() or None
        p.marathi_sub_caste = request.form.get('marathi_sub_caste', '').strip() or None
        p.gotra             = request.form.get('gotra', '').strip() or None
        p.mother_tongue     = request.form.get('mother_tongue', '').strip() or None
        p.manglik           = request.form.get('manglik', '').strip() or None
        p.is_nri            = 'is_nri' in request.form
        p.nri_country       = request.form.get('nri_country', '').strip() or None
        db.session.commit()
        flash('Religion & community details saved.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/religion.html',
                           user=current_user, profile=p,
                           marathi_sub_castes=MARATHI_SUB_CASTES)

@profile_bp.route('/lifestyle', methods=['GET', 'POST'])
@login_required
def lifestyle():
    if request.method == 'POST':
        p = _get_or_create_profile()
        p.diet           = request.form.get('diet', '').strip()
        p.smoking        = request.form.get('smoking', '').strip()
        p.drinking       = request.form.get('drinking', '').strip()
        p.marital_status = request.form.get('marital_status', '').strip()
        p.have_children  = request.form.get('have_children', '').strip()
        p.family_type    = request.form.get('family_type', '').strip()
        p.family_status  = request.form.get('family_status', '').strip()
        p.complexion     = request.form.get('complexion', '').strip()
        p.body_type      = request.form.get('body_type', '').strip()
        db.session.commit()
        flash('Lifestyle details updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/lifestyle.html', user=current_user, profile=current_user.profile)


@profile_bp.route('/email', methods=['GET', 'POST'])
@login_required
def email():
    if request.method == 'POST':
        new_email = request.form.get('email', '').strip().lower()
        if not new_email:
            flash('Email cannot be empty.', 'danger')
        else:
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != current_user.id:
                flash('Email already registered to another account.', 'danger')
            else:
                from app.utils import generate_token, send_email
                token = generate_token()
                current_user.email              = new_email
                current_user.is_verified        = False
                current_user.verify_token       = token
                current_user.verify_token_expiry = datetime.utcnow() + __import__('datetime').timedelta(hours=24)
                db.session.commit()
                # Auto-send verification to new email
                verify_url = url_for('auth.verify_email', token=token, _external=True)
                try:
                    send_email(
                        new_email,
                        'Verify your new iJodidar email address',
                        f'<p>Hello {current_user.first_name}, click to verify your new email: '
                        f'<a href="{verify_url}">Verify Email</a>. Link expires in 24 hours.</p>',
                    )
                    flash('Email updated. A verification link has been sent to your new email.', 'success')
                except Exception:
                    flash('Email updated. Please re-verify your email address.', 'success')
                return redirect(url_for('profile.profile'))
    return render_template('profile/email.html', user=current_user)


@profile_bp.route('/phone', methods=['GET', 'POST'])
@login_required
def phone():
    alt_phones = PhoneAlternate.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        primary = request.form.get('phone', '').strip()
        if primary:
            current_user.phone = primary
        alts = [p.strip() for p in request.form.getlist('alternate_phones') if p.strip()]
        PhoneAlternate.query.filter_by(user_id=current_user.id).delete()
        for ph in alts[:2]:
            db.session.add(PhoneAlternate(user_id=current_user.id, phone=ph))
        db.session.commit()
        flash('Phone numbers updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/phone.html', user=current_user, alternate_phones=alt_phones)


@profile_bp.route('/address/<tag>', methods=['GET', 'POST'])
@login_required
def address(tag):
    if tag.lower() not in ['permanent', 'current', 'work']:
        abort(400)
    tag_cap   = tag.capitalize()
    addr      = Address.query.filter_by(user_id=current_user.id, tag=tag_cap).first()
    cities    = City.query.order_by(City.name).all()
    states    = State.query.order_by(State.name).all()
    countries = Country.query.order_by(Country.name).all()
    if request.method == 'POST':
        try:
            city_id    = int(request.form.get('city_id'))
            state_id   = int(request.form.get('state_id'))
            country_id = int(request.form.get('country_id'))
        except (TypeError, ValueError):
            flash('Please select valid city, state, and country.', 'danger')
            return redirect(url_for('profile.address', tag=tag))
        if not addr:
            addr = Address(user_id=current_user.id, tag=tag_cap)
            db.session.add(addr)
        addr.address1   = request.form.get('address1', '').strip()
        addr.address2   = request.form.get('address2', '').strip()
        addr.address3   = request.form.get('address3', '').strip()
        addr.city_id    = city_id
        addr.state_id   = state_id
        addr.country_id = country_id
        addr.zipcode    = request.form.get('zipcode', '').strip()
        if not addr.address1 or not addr.zipcode:
            flash('Address and ZIP code are required.', 'danger')
            return redirect(url_for('profile.address', tag=tag))
        db.session.commit()
        flash(f'{tag_cap} address updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/address.html', user=current_user, address=addr,
                           cities=cities, states=states, countries=countries, tag=tag)


@profile_bp.route('/professional', methods=['GET', 'POST'])
@login_required
def professional():
    pro = ProfessionalDetails.query.filter_by(user_id=current_user.id).first()
    if not pro:
        pro = ProfessionalDetails(user_id=current_user.id)
        db.session.add(pro)
    if request.method == 'POST':
        pro.occupation          = request.form.get('occupation', '').strip()
        pro.company_name        = request.form.get('company_name', '').strip()
        pro.designation         = request.form.get('designation', '').strip()
        pro.employment_type     = request.form.get('employment_type', '').strip()
        pro.location            = request.form.get('location', '').strip()
        exp = request.form.get('years_of_experience', '')
        pro.years_of_experience = int(exp) if exp.isdigit() else None
        pro.package             = request.form.get('package', '').strip()
        pro.turn_over           = request.form.get('turn_over', '').strip()
        db.session.commit()
        flash('Professional details updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/professional.html', user=current_user, professional=pro)


@profile_bp.route('/education', methods=['GET', 'POST'])
@login_required
def education():
    edu = Education.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        if not edu:
            edu = Education(user_id=current_user.id)
            db.session.add(edu)
        edu.degree          = request.form.get('degree', '').strip()
        edu.specialization  = request.form.get('specialization', '').strip()
        edu.university      = request.form.get('university', '').strip()
        edu.institution     = request.form.get('institution', '').strip()
        yop = request.form.get('year_of_passing', '')
        edu.year_of_passing = int(yop) if yop.isdigit() else None
        edu.grade           = request.form.get('grade', '').strip()
        if not edu.degree or not edu.institution:
            flash('Degree and institution are required.', 'danger')
        else:
            db.session.commit()
            flash('Education updated.', 'success')
            return redirect(url_for('profile.profile'))
    return render_template('profile/education.html', user=current_user, education=edu)


@profile_bp.route('/language', methods=['GET', 'POST'])
@login_required
def language():
    user_languages = Language.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        action  = request.form.get('action')
        lang_id = request.form.get('language_id', type=int)
        if action == 'add':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Language name required.', 'danger')
                return redirect(url_for('profile.language'))
            db.session.add(Language(user_id=current_user.id, name=name,
                proficiency=request.form.get('proficiency') or None,
                certification=request.form.get('certification') or None,
                notes=request.form.get('notes') or None))
            db.session.commit()
            flash('Language added.', 'success')
        elif action == 'edit' and lang_id:
            lang = Language.query.filter_by(id=lang_id, user_id=current_user.id).first_or_404()
            lang.name=request.form.get('name','').strip()
            lang.proficiency=request.form.get('proficiency') or None
            lang.certification=request.form.get('certification') or None
            lang.notes=request.form.get('notes') or None
            db.session.commit()
            flash('Language updated.', 'success')
        elif action == 'delete' and lang_id:
            lang = Language.query.filter_by(id=lang_id, user_id=current_user.id).first_or_404()
            db.session.delete(lang)
            db.session.commit()
            flash('Language removed.', 'success')
        return redirect(url_for('profile.language'))
    return render_template('profile/language.html', user=current_user, user_languages=user_languages)


@profile_bp.route('/upload_image', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def upload_image():
    file = request.files.get('image')
    is_primary = 'is_primary' in request.form
    full_url, thumb_url, card_url, err = upload_image_to_s3(file, user_id=current_user.id)
    if err:
        flash(err, 'danger')
        return redirect(url_for('main.my_profile'))
    if is_primary:
        ProfileImage.query.filter_by(user_id=current_user.id, is_primary=True)\
                          .update({'is_primary': False})
    db.session.add(ProfileImage(
        user_id=current_user.id, image_url=full_url,
        thumb_url=thumb_url, card_url=card_url, is_primary=is_primary))
    db.session.commit()
    flash('Photo uploaded!', 'success')
    return redirect(url_for('main.my_profile'))


@profile_bp.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    img = ProfileImage.query.get_or_404(image_id)
    if img.user_id != current_user.id:
        abort(403)
    delete_image_from_s3(img.image_url)
    db.session.delete(img)
    db.session.commit()
    flash('Photo deleted.', 'info')
    return redirect(url_for('main.my_profile'))


@profile_bp.route('/set_primary_image/<int:image_id>')
@login_required
def set_primary_image(image_id):
    img = ProfileImage.query.get_or_404(image_id)
    if img.user_id != current_user.id:
        abort(403)
    ProfileImage.query.filter_by(user_id=current_user.id).update({'is_primary': False})
    img.is_primary = True
    db.session.commit()
    flash('Profile photo updated.', 'success')
    return redirect(url_for('main.my_profile'))


# ── PARTNER PREFERENCES ────────────────────────────────────────────────────
@profile_bp.route('/partner_preferences', methods=['GET', 'POST'])
@login_required
def partner_preferences():
    from app.models import PartnerPreference
    pref = PartnerPreference.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        if not pref:
            pref = PartnerPreference(user_id=current_user.id)
            db.session.add(pref)
        def _int(key):
            v = request.form.get(key, '').strip()
            try: return int(v) if v else None
            except ValueError: return None
        def _str(key):
            v = request.form.get(key, '').strip()
            return v if v else None
        pref.min_age          = _int('min_age')
        pref.max_age          = _int('max_age')
        pref.min_height       = _int('min_height')
        pref.max_height       = _int('max_height')
        pref.religion         = _str('religion')
        pref.caste            = _str('caste')
        pref.mother_tongue    = _str('mother_tongue')
        pref.marital_status   = _str('marital_status')
        pref.min_income       = _str('min_income')
        pref.education_level  = _str('education_level')
        pref.manglik          = _str('manglik')
        pref.diet             = _str('diet')
        pref.smoking          = _str('smoking')
        pref.drinking         = _str('drinking')
        pref.location_preference = _str('location_preference')
        pref.about            = request.form.get('about', '').strip()[:500] or None
        db.session.commit()
        flash('Partner preferences saved.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/partner_preferences.html',
                           user=current_user, pref=pref)


# ── PRIVACY / HIDE / DEACTIVATE ────────────────────────────────────────────
@profile_bp.route('/privacy', methods=['GET', 'POST'])
@login_required
def privacy():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'toggle_hide':
            current_user.is_hidden = not current_user.is_hidden
            db.session.commit()
            state = 'hidden from' if current_user.is_hidden else 'visible in'
            flash(f'Your profile is now {state} search results.', 'success')
        elif action == 'deactivate':
            current_user.is_hidden     = True
            current_user.is_active_acc = False
            db.session.commit()
            from flask_login import logout_user
            logout_user()
            flash('Your account has been deactivated. Contact support to reactivate.', 'info')
            return redirect(url_for('auth.login'))
        return redirect(url_for('profile.privacy'))
    return render_template('profile/privacy.html', user=current_user)


# ── ACCOUNT DELETION (DPDP right to erasure) ─────────────────────────────
@profile_bp.route('/account/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Permanently delete user account and all personal data (DPDP compliance)."""
    from flask_login import logout_user
    from app.models import (Profile, Address, Education, ProfessionalDetails,
                            FamilyDetails, ProfileImage, Language, PhoneAlternate,
                            Interest, Shortlist, BlockList, Notification,
                            UserSubscription, Referral, KundliDetail,
                            PartnerPreference, ProfileView, UserReport)

    if request.method == 'POST':
        confirm = request.form.get('confirm_text', '').strip()
        if confirm != 'DELETE':
            flash('Please type DELETE to confirm account deletion.', 'danger')
            return render_template('profile/delete_account.html', user=current_user)

        user_id = current_user.id
        username = current_user.username

        # Anonymise — do not hard delete to preserve referential integrity
        # Soft-delete: wipe PII, mark inactive, hide
        current_user.first_name  = 'Deleted'
        current_user.last_name   = 'User'
        current_user.email       = f'deleted_{user_id}@ijodidar.deleted'
        current_user.phone       = None
        current_user.username    = f'deleted_user_{user_id}'
        current_user.is_active_acc = False
        current_user.is_hidden   = True
        current_user.password_hash = 'DELETED'
        current_user.verify_token = None
        current_user.reset_token  = None

        # Delete profile data
        if current_user.profile:
            current_user.profile.bio           = None
            current_user.profile.profile_picture = None
            current_user.profile.linkedin_url  = None

        # Delete photos from S3
        for img in list(current_user.profile_images):
            try:
                from app.utils import delete_image_from_s3
                delete_image_from_s3(img.image_url)
            except Exception:
                pass
            db.session.delete(img)

        # Delete sensitive records
        PhoneAlternate.query.filter_by(user_id=user_id).delete()
        Notification.query.filter_by(user_id=user_id).delete()

        db.session.commit()
        logout_user()
        flash('Your account and personal data have been permanently deleted.', 'success')
        current_app.logger.info(f'Account deleted: user_id={user_id}')
        return redirect(url_for('main.landing'))

    return render_template('profile/delete_account.html', user=current_user)


# ── DATA EXPORT (DPDP right to data portability) ──────────────────────────
@profile_bp.route('/account/export')
@login_required
@limiter.limit("3 per day")
def export_data():
    """
    Generate and download a complete export of the user's personal data.
    DPDP Act 2023 — right to data portability.
    Returns a JSON file with all profile data, interests, messages, and payments.
    Rate limited: max 3 exports per day.
    """
    import json
    from datetime import datetime
    from app.models import (Interest, Conversation, Message, UserSubscription,
                            Referral, Shortlist, ProfileView, Notification)

    u = current_user._get_current_object()

    # ── Basic profile ──────────────────────────────────────────────────────
    profile_data = {
        'name':          u.full_name,
        'email':         u.email,
        'phone':         u.phone,
        'username':      u.username,
        'joined':        u.created_at.isoformat(),
        'email_verified': u.is_verified,
        'phone_verified': u.phone_verified,
    }

    p = u.profile
    if p:
        profile_data.update({
            'gender':         p.gender,
            'looking_for':    p.looking_for,
            'date_of_birth':  str(p.dob or p.date_of_birth or ''),
            'religion':       p.religion,
            'caste':          p.caste,
            'marital_status': p.marital_status,
            'height_cm':      p.height,
            'bio':            p.bio,
            'diet':           p.diet,
            'smoking':        p.smoking,
            'drinking':       p.drinking,
            'mother_tongue':  p.mother_tongue,
            'manglik':        p.manglik,
            'is_nri':         p.is_nri,
            'nri_country':    p.nri_country,
        })

    # ── Professional ──────────────────────────────────────────────────────
    pro = next(iter(u.professional_details), None) if hasattr(u, 'professional_details') else None
    professional = {}
    if pro:
        professional = {
            'occupation':   pro.occupation,
            'company':      pro.company_name,
            'designation':  pro.designation,
            'income_lpa':   pro.income_lpa,
        }

    # ── Addresses ─────────────────────────────────────────────────────────
    addresses = []
    for addr in (u.addresses or []):
        addresses.append({
            'tag':     addr.tag,
            'address': addr.address1,
            'zipcode': addr.zipcode,
        })

    # ── Interests sent/received ────────────────────────────────────────────
    interests_sent = []
    for i in Interest.query.filter_by(sender_id=u.id).all():
        interests_sent.append({
            'to_user_id': i.receiver_id,
            'status':     i.status,
            'sent_at':    i.sent_at.isoformat(),
        })

    interests_received = []
    for i in Interest.query.filter_by(receiver_id=u.id).all():
        interests_received.append({
            'from_user_id': i.sender_id,
            'status':       i.status,
            'sent_at':      i.sent_at.isoformat(),
        })

    # ── Messages ──────────────────────────────────────────────────────────
    convs = Conversation.query.filter(
        (Conversation.user1_id == u.id) | (Conversation.user2_id == u.id)
    ).all()
    messages_export = []
    for conv in convs:
        other_id = conv.user2_id if conv.user1_id == u.id else conv.user1_id
        for msg in conv.messages.filter_by(sender_id=u.id).all():
            messages_export.append({
                'conversation_with_user_id': other_id,
                'sent_at': msg.sent_at.isoformat(),
                'body':    msg.body,
            })

    # ── Payment history ────────────────────────────────────────────────────
    payments = []
    for sub in UserSubscription.query.filter_by(user_id=u.id).all():
        if sub.amount_paid > 0:
            payments.append({
                'plan':        sub.plan.name if sub.plan else '?',
                'amount_inr':  sub.amount_paid // 100,
                'started_at':  sub.started_at.isoformat(),
                'expires_at':  sub.expires_at.isoformat() if sub.expires_at else None,
                'payment_ref': sub.payment_ref,
            })

    # ── Shortlists ──────────────────────────────────────────────────────────
    shortlisted_ids = [s.shortlisted_id for s in
                       Shortlist.query.filter_by(user_id=u.id).all()]

    # ── Referrals ──────────────────────────────────────────────────────────
    referral_data = {}
    own_ref = Referral.query.filter_by(
        referrer_id=u.id, referred_id=None).first()
    if own_ref:
        referral_data['your_referral_code'] = own_ref.code
        referral_data['rewards_earned'] = Referral.query.filter(
            Referral.referrer_id == u.id,
            Referral.rewarded_at != None).count()

    # ── Build export payload ───────────────────────────────────────────────
    export = {
        'export_generated_at': datetime.utcnow().isoformat() + 'Z',
        'export_type':         'iJodidar Personal Data Export',
        'legal_basis':         'DPDP Act 2023 — Right to Data Portability',
        'profile':             profile_data,
        'professional':        professional,
        'addresses':           addresses,
        'interests_sent':      interests_sent,
        'interests_received':  interests_received,
        'messages_sent':       messages_export,
        'payment_history':     payments,
        'shortlisted_user_ids': shortlisted_ids,
        'referral':            referral_data,
    }

    payload  = json.dumps(export, indent=2, ensure_ascii=False)
    filename = f"ijodidar_data_export_{u.username}_{datetime.utcnow().strftime('%Y%m%d')}.json"

    from flask import Response
    return Response(
        payload,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Cache-Control': 'no-store',
        }
    )


# ── REFERRAL DASHBOARD ─────────────────────────────────────────────────────
@profile_bp.route('/referral')
@login_required
def referral():
    from app.utils import get_or_create_referral
    from app.models import Referral
    ref          = get_or_create_referral(current_user)
    total_joined = Referral.query.filter(
        Referral.referrer_id == current_user.id,
        Referral.referred_id != None
    ).count()
    rewarded     = Referral.query.filter(
        Referral.referrer_id == current_user.id,
        Referral.rewarded_at != None
    ).count()
    return render_template('profile/referral.html',
                           user=current_user,
                           ref=ref,
                           total_joined=total_joined,
                           rewarded=rewarded)


# ── HOBBIES / INTERESTS (Phase 12) ────────────────────────────────────────
@profile_bp.route('/hobbies', methods=['GET', 'POST'])
@login_required
def hobbies():
    from app.utils_kundli import HOBBIES
    import json
    p = _get_or_create_profile()
    if request.method == 'POST':
        selected = request.form.getlist('hobbies')[:20]   # max 20
        p.hobbies = json.dumps(selected)
        db.session.commit()
        flash('Hobbies updated!', 'success')
        return redirect(url_for('profile.profile'))
    current_hobbies = json.loads(p.hobbies) if p and p.hobbies else []
    return render_template('profile/hobbies.html',
                           user=current_user, profile=p,
                           all_hobbies=HOBBIES,
                           current_hobbies=current_hobbies)


# ── NRI STATUS (Phase 12) ──────────────────────────────────────────────────
@profile_bp.route('/nri', methods=['GET', 'POST'])
@login_required
def nri_status():
    p = _get_or_create_profile()
    if request.method == 'POST':
        p.is_nri      = 'is_nri' in request.form
        p.nri_country = request.form.get('nri_country', '').strip() or None
        db.session.commit()
        flash('NRI status updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile/nri.html', user=current_user, profile=p)


# ── UNIFIED PROFILE EDITOR ─────────────────────────────────────────────────
@profile_bp.route('/profile/edit')
@login_required
def profile_edit():
    from app.models import PartnerPreference
    from app.utils_kundli import MARATHI_SUB_CASTES, HOBBIES
    import json
    u    = current_user
    p    = u.profile
    pro  = ProfessionalDetails.query.filter_by(user_id=u.id).first()
    edu  = Education.query.filter_by(user_id=u.id).first()
    pref = PartnerPreference.query.filter_by(user_id=u.id).first()
    perm = Address.query.filter_by(user_id=u.id, tag='Permanent').first()
    curr = Address.query.filter_by(user_id=u.id, tag='Current').first()
    cities    = City.query.order_by(City.name).limit(500).all()
    states    = State.query.order_by(State.name).all()
    countries = Country.query.order_by(Country.name).all()
    try:
        raw = p.hobbies if p and p.hobbies else None
        current_hobbies = json.loads(raw) if raw else []
        if not isinstance(current_hobbies, list):
            current_hobbies = []
    except Exception:
        current_hobbies = []
    tab = request.args.get('tab', 'basic')
    return render_template('profile/edit.html',
        user=u, profile=p, professional=pro, education=edu, pref=pref,
        permanent=perm, current_addr=curr,
        cities=cities, states=states, countries=countries,
        marathi_sub_castes=MARATHI_SUB_CASTES,
        all_hobbies=HOBBIES,
        current_hobbies=current_hobbies,
        active_tab=tab,
    )


@profile_bp.route('/profile/save/<section>', methods=['POST'])
@login_required
def profile_save(section):
    from flask import jsonify
    u = current_user

    try:
        if section == 'basic':
            fn = request.form.get('first_name', '').strip()
            ln = request.form.get('last_name', '').strip()
            if not fn or not ln:
                return jsonify(success=False, message='Name fields cannot be empty.')
            u.first_name = fn
            u.last_name  = ln
            p = _get_or_create_profile()
            p.gender      = request.form.get('gender', '').strip() or p.gender
            p.looking_for = request.form.get('looking_for', '').strip() or None
            p.bio         = request.form.get('bio', '').strip()[:1000] or None
            h = request.form.get('height', '').strip()
            p.height = int(h) if h.isdigit() else p.height
            # birthday
            mn, dv, yv = request.form.get('month'), request.form.get('date'), request.form.get('year')
            if mn and dv and yv:
                try:
                    from datetime import datetime as _dt
                    m   = _dt.strptime(mn, '%B').month
                    dob = _dt(int(yv), m, int(dv)).date()
                    p.date_of_birth = dob.strftime('%Y-%m-%d')
                    p.birth_time    = request.form.get('birth_time', '').strip() or None
                    p.birth_village = request.form.get('birth_village', '').strip() or None
                    p.birth_city    = request.form.get('birth_city', '').strip() or None
                    p.birth_state   = request.form.get('birth_state', '').strip() or None
                    p.birth_country = request.form.get('birth_country', '').strip() or None
                except Exception:
                    return jsonify(success=False, message='Invalid date of birth.')
            db.session.commit()

        elif section == 'community':
            p = _get_or_create_profile()
            p.religion          = request.form.get('religion', '').strip() or None
            p.caste             = request.form.get('caste', '').strip() or None
            p.sub_caste         = request.form.get('sub_caste', '').strip() or None
            p.marathi_sub_caste = request.form.get('marathi_sub_caste', '').strip() or None
            p.gotra             = request.form.get('gotra', '').strip() or None
            p.mother_tongue     = request.form.get('mother_tongue', '').strip() or None
            p.manglik           = request.form.get('manglik', '').strip() or None
            p.is_nri            = request.form.get('is_nri') == '1'
            p.nri_country       = request.form.get('nri_country', '').strip() or None
            db.session.commit()

        elif section == 'lifestyle':
            p = _get_or_create_profile()
            p.diet           = request.form.get('diet', '').strip() or None
            p.smoking        = request.form.get('smoking', '').strip() or None
            p.drinking       = request.form.get('drinking', '').strip() or None
            p.marital_status = request.form.get('marital_status', '').strip() or None
            p.have_children  = request.form.get('have_children', '').strip() or None
            p.family_type    = request.form.get('family_type', '').strip() or None
            p.family_status  = request.form.get('family_status', '').strip() or None
            p.complexion     = request.form.get('complexion', '').strip() or None
            p.body_type      = request.form.get('body_type', '').strip() or None
            db.session.commit()

        elif section == 'career':
            pro = ProfessionalDetails.query.filter_by(user_id=u.id).first()
            if not pro:
                pro = ProfessionalDetails(user_id=u.id)
                db.session.add(pro)
            pro.occupation      = request.form.get('occupation', '').strip() or None
            pro.company_name    = request.form.get('company_name', '').strip() or None
            pro.designation     = request.form.get('designation', '').strip() or None
            pro.employment_type = request.form.get('employment_type', '').strip() or None
            inc = request.form.get('income_lpa', '').strip()
            pro.income_lpa = int(inc) if inc.isdigit() else None
            exp = request.form.get('years_of_experience', '').strip()
            pro.years_of_experience = int(exp) if exp.isdigit() else None
            # Education
            edu = Education.query.filter_by(user_id=u.id).first()
            if not edu:
                edu = Education(user_id=u.id)
                db.session.add(edu)
            edu.degree         = request.form.get('degree', '').strip() or None
            edu.specialization = request.form.get('specialization', '').strip() or None
            edu.university     = request.form.get('university', '').strip() or None
            edu.institution    = request.form.get('institution', '').strip() or None
            yop = request.form.get('year_of_passing', '').strip()
            edu.year_of_passing = int(yop) if yop.isdigit() else None
            db.session.commit()

        elif section == 'location':
            tag = request.form.get('tag', 'Permanent')
            if tag not in ('Permanent', 'Current'):
                return jsonify(success=False, message='Invalid address tag.')
            addr = Address.query.filter_by(user_id=u.id, tag=tag).first()
            if not addr:
                addr = Address(user_id=u.id, tag=tag)
                db.session.add(addr)
            def _int_id(key):
                v = request.form.get(key, '').strip()
                try:
                    n = int(v)
                    return n if n > 0 else None
                except (TypeError, ValueError):
                    return None
            addr.city_id    = _int_id('city_id')
            addr.state_id   = _int_id('state_id')
            addr.country_id = _int_id('country_id')
            addr.address1 = request.form.get('address1', '').strip() or None
            addr.zipcode  = request.form.get('zipcode', '').strip() or None
            db.session.commit()

        elif section == 'hobbies':
            import json as _json
            p = _get_or_create_profile()
            selected = request.form.getlist('hobbies')[:20]
            p.hobbies = _json.dumps(selected)
            db.session.commit()

        elif section == 'preferences':
            from app.models import PartnerPreference
            pref = PartnerPreference.query.filter_by(user_id=u.id).first()
            if not pref:
                pref = PartnerPreference(user_id=u.id)
                db.session.add(pref)
            def _int(key):
                v = request.form.get(key, '').strip()
                try: return int(v) if v else None
                except ValueError: return None
            def _str(key):
                v = request.form.get(key, '').strip()
                return v if v else None
            pref.min_age         = _int('min_age')
            pref.max_age         = _int('max_age')
            pref.min_height      = _int('min_height')
            pref.max_height      = _int('max_height')
            pref.min_income_lpa  = _int('min_income_lpa')
            pref.max_income_lpa  = _int('max_income_lpa')
            pref.religion        = _str('religion')
            pref.caste           = _str('caste')
            pref.mother_tongue   = _str('mother_tongue')
            pref.marital_status  = _str('marital_status')
            pref.education_level = _str('education_level')
            pref.manglik         = _str('manglik')
            pref.diet            = _str('diet')
            pref.smoking         = _str('smoking')
            pref.drinking        = _str('drinking')
            pref.about           = request.form.get('about', '').strip()[:500] or None
            db.session.commit()

        else:
            return jsonify(success=False, message='Unknown section.')

        return jsonify(success=True, message='Saved successfully.')

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message='Save failed. Please try again.')


# ── LANGUAGE PREFERENCE (Phase 13.2) ──────────────────────────────────────
@profile_bp.route('/set-language', methods=['POST'])
@login_required
def set_ui_language():
    lang = request.form.get('lang', 'en')
    if lang not in ('en', 'mr'):
        lang = 'en'
    p = _get_or_create_profile()
    p.ui_language = lang
    db.session.commit()
    from flask import session
    session['ui_language'] = lang
    flash('Language updated!', 'success')
    return redirect(request.referrer or url_for('main.home'))
