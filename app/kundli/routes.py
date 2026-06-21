"""
app/kundli/routes.py

Auto-calculates all Vedic birth chart attributes from DOB + Time + Place.
Users only enter: Date of Birth, Time of Birth, Birth City.
All astrological attributes are computed automatically.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import KundliDetail, Profile
from app.utils_kundli import (calculate_guna_milan, check_gotra_compatibility,
                               NAKSHATRAS)
from app.utils import manglik_compatible
                               
from app.vedic_engine import (compute_vedic_birth_chart, compute_manglik_approximate,
                               CITY_COORDINATES)

kundli_bp = Blueprint('kundli', __name__)


@kundli_bp.route('/kundli/edit', methods=['GET', 'POST'])
@login_required
def edit_kundli():
    """
    Auto-Kundli: user enters DOB + time + city.
    System calculates nakshatra, rashi, gana, nadi, varna, yoni, manglik.
    User can override if they have a paper kundli.
    """
    kd = KundliDetail.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        mode         = request.form.get('mode', 'auto')   # 'auto' or 'manual'
        birth_date   = request.form.get('birth_date',  '').strip()
        birth_time   = request.form.get('birth_time',  '').strip()
        birth_city   = request.form.get('birth_city',  '').strip()

        if not kd:
            kd = KundliDetail(user_id=current_user.id)
            db.session.add(kd)

        kd.birth_date = birth_date
        kd.birth_time = birth_time
        kd.birth_city = birth_city

        if mode == 'auto' and birth_date and birth_time and birth_city:
            # ── AUTO-CALCULATE from DOB + time + city ──────────────────────
            chart = compute_vedic_birth_chart(birth_date, birth_time, birth_city)

            if chart.get('auto_calculated'):
                kd.nakshatra = chart['nakshatra']
                kd.rashi     = chart['rashi']
                kd.charan    = chart['charan']
                kd.gana      = chart['gana']
                kd.nadi      = chart['nadi']
                kd.varna     = chart['varna']
                kd.yoni      = chart['yoni']
                kd.birth_lat = chart['lat']
                kd.birth_lng = chart['lon']

                # Approximate Manglik
                manglik_result = compute_manglik_approximate(birth_date, birth_time, birth_city)
                kd.manglik = manglik_result.get('manglik', 'Unknown')

                # Sync to Profile for quick access
                p = current_user.profile
                if not p:
                    from app.models import Profile as P
                    p = P(user_id=current_user.id)
                    db.session.add(p)
                p.birth_nakshatra = kd.nakshatra
                p.birth_rashi     = kd.rashi
                p.manglik         = kd.manglik

                db.session.commit()
                flash(
                    f'Kundli calculated! Nakshatra: {kd.nakshatra}, '
                    f'Rashi: {kd.rashi} (Charan {kd.charan}), '
                    f'Manglik: {kd.manglik}',
                    'success'
                )
            else:
                flash(f'Auto-calculation failed: {chart.get("error", "unknown error")}', 'danger')

        elif mode == 'manual':
            # ── MANUAL ENTRY (user has paper kundli) ───────────────────────
            kd.nakshatra = request.form.get('nakshatra', '').strip()
            kd.rashi     = request.form.get('rashi',     '').strip()
            kd.charan    = request.form.get('charan', type=int)
            kd.gana      = request.form.get('gana',      '').strip()
            kd.nadi      = request.form.get('nadi',      '').strip()
            kd.manglik   = request.form.get('manglik',   '').strip()

            p = current_user.profile
            if not p:
                from app.models import Profile as P
                p = P(user_id=current_user.id)
                db.session.add(p)
            if kd.nakshatra:
                p.birth_nakshatra = kd.nakshatra
            if kd.rashi:
                p.birth_rashi = kd.rashi
            if kd.manglik:
                p.manglik = kd.manglik

            db.session.commit()
            flash('Kundli details saved (manual entry)!', 'success')
        else:
            flash('Please enter Date of Birth, Time of Birth, and Birth City.', 'warning')

        return redirect(url_for('kundli.edit_kundli'))

    nakshatra_names = [n[0] for n in NAKSHATRAS]
    rashis   = ['Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya',
                'Tula','Vrischika','Dhanu','Makara','Kumbha','Meena']
    ganas    = ['Deva', 'Manushya', 'Rakshasa']
    nadis    = ['Adi', 'Madhya', 'Antya']

    # Pre-fill birth details from Profile if KundliDetail not yet saved
    p = current_user.profile
    prefill_date = ''
    prefill_time = ''
    prefill_city = ''
    if kd:
        prefill_date = kd.birth_date or ''
        prefill_time = kd.birth_time or ''
        prefill_city = kd.birth_city or ''
    if p:
        if not prefill_date:
            # profile stores date_of_birth as 'YYYY-MM-DD' string or dob as Date
            if p.dob:
                prefill_date = p.dob.strftime('%Y-%m-%d')
            elif p.date_of_birth:
                prefill_date = str(p.date_of_birth)
        if not prefill_time and p.birth_time:
            prefill_time = p.birth_time
        if not prefill_city and p.birth_city:
            prefill_city = p.birth_city

    return render_template('kundli/edit.html',
                           user=current_user, kd=kd,
                           prefill_date=prefill_date,
                           prefill_time=prefill_time,
                           prefill_city=prefill_city,
                           nakshatras=nakshatra_names, rashis=rashis,
                           ganas=ganas, nadis=nadis)


@kundli_bp.route('/kundli/api/calculate')
@login_required
def api_calculate():
    """
    AJAX endpoint: auto-calculate chart from DOB + time + city.
    Used by the edit form for live preview before saving.
    """
    birth_date = request.args.get('date', '')
    birth_time = request.args.get('time', '')
    birth_city = request.args.get('city', '')

    if not (birth_date and birth_time and birth_city):
        return jsonify({'error': 'date, time, and city are required'}), 400

    chart   = compute_vedic_birth_chart(birth_date, birth_time, birth_city)
    manglik = compute_manglik_approximate(birth_date, birth_time, birth_city)
    chart['manglik'] = manglik.get('manglik', 'Unknown')
    chart['manglik_notes'] = manglik.get('notes', '')
    return jsonify(chart)


@kundli_bp.route('/kundli/match/<int:other_user_id>')
@login_required
def match_kundli(other_user_id):
    """Full Guna Milan report between current user and another user."""
    from app.models import User
    other    = User.query.get_or_404(other_user_id)
    my_kd    = KundliDetail.query.filter_by(user_id=current_user.id).first()
    other_kd = KundliDetail.query.filter_by(user_id=other_user_id).first()

    guna_result = calculate_guna_milan(
        my_kd.nakshatra    if my_kd    else None,
        other_kd.nakshatra if other_kd else None,
    )

    my_gotra    = current_user.profile.gotra if current_user.profile else None
    other_gotra = other.profile.gotra        if other.profile        else None
    gotra_compat, gotra_msg = check_gotra_compatibility(
        my_gotra, other_gotra,
        current_user.profile.religion if current_user.profile else '',
        other.profile.religion        if other.profile        else '',
    )

    manglik_compat, manglik_msg = manglik_compatible(
        current_user.profile if current_user.profile else None,
        other.profile        if other.profile        else None,
    )

    return render_template('kundli/match.html',
                           user=current_user, other=other,
                           my_kd=my_kd, other_kd=other_kd,
                           guna=guna_result,
                           gotra_compatible=gotra_compat,
                           gotra_msg=gotra_msg,
                           manglik_compatible=manglik_compat,
                           manglik_msg=manglik_msg)


@kundli_bp.route('/kundli/api/match')
@login_required
def api_match():
    """JSON endpoint: quick Guna score by nakshatra names."""
    n1 = request.args.get('n1', '')
    n2 = request.args.get('n2', '')
    return jsonify(calculate_guna_milan(n1, n2))


@kundli_bp.route('/kundli/api/cities')
@login_required
def api_cities():
    """Autocomplete: return matching city names from built-in database."""
    q = request.args.get('q', '').lower().strip()
    if len(q) < 2:
        return jsonify([])
    matches = [c.title() for c in CITY_COORDINATES if q in c][:15]
    return jsonify(sorted(matches))
