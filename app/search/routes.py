from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from datetime import date
from app.models import (User, Profile, Address, City, Education,
                        ProfessionalDetails, BlockList)
from app.utils_kundli import MARATHI_SUB_CASTES
from app import limiter

search_bp = Blueprint('search', __name__)

# ── helpers ────────────────────────────────────────────────────────────────
RELIGIONS = ['', 'Hindu', 'Muslim', 'Christian', 'Sikh', 'Buddhist',
             'Jain', 'Parsi', 'Jewish', 'No Religion', 'Other']

MARITAL_STATUSES = ['', 'Never Married', 'Divorced', 'Widowed', 'Separated']

MANGLIK_OPTS = ['', 'Yes', 'No', 'Partial']

MOTHER_TONGUES = ['', 'Hindi', 'Marathi', 'Bengali', 'Telugu', 'Tamil',
                  'Gujarati', 'Kannada', 'Malayalam', 'Punjabi', 'Odia',
                  'Urdu', 'Sindhi', 'English', 'Other']

INCOME_RANGES = [
    ('', 'Any'),
    ('0-3',   'Below 3 LPA'),
    ('3-5',   '3 – 5 LPA'),
    ('5-10',  '5 – 10 LPA'),
    ('10-15', '10 – 15 LPA'),
    ('15-25', '15 – 25 LPA'),
    ('25-50', '25 – 50 LPA'),
    ('50+',   '50 LPA+'),
]


def _blocked_ids(user_id):
    """Return set of user-ids that either blocked or are blocked by user_id."""
    rows = BlockList.query.filter(
        or_(BlockList.blocker_id == user_id,
            BlockList.blocked_id == user_id)
    ).all()
    ids = set()
    for r in rows:
        ids.add(r.blocker_id)
        ids.add(r.blocked_id)
    ids.discard(user_id)
    return ids


@search_bp.route('/search', methods=['GET'])
@login_required
@limiter.limit('60 per minute')
def search_profiles():
    args = request.args

    # base query — exclude self, hidden, suspended, blocked
    blocked = _blocked_ids(current_user.id)
    query = (
        User.query
        .join(Profile)
        .outerjoin(Address)
        .outerjoin(City,    Address.city_id    == City.id)
        .outerjoin(ProfessionalDetails)
        .outerjoin(Education)
        .filter(
            User.id        != current_user.id,
            User.is_active_acc == True,
            User.is_hidden     == False,
            User.is_staff      == False,   # never show staff in search
        )
    )
    if blocked:
        query = query.filter(User.id.notin_(blocked))

    # ── keyword ──────────────────────────────────────────────────────
    kw = args.get('keyword', '').strip()
    if kw:
        kw_like = f'%{kw}%'
        query = query.filter(or_(
            User.first_name.ilike(kw_like),
            User.last_name.ilike(kw_like),
            City.name.ilike(kw_like),
            ProfessionalDetails.occupation.ilike(kw_like),
            ProfessionalDetails.company_name.ilike(kw_like),
        ))

    # ── gender ────────────────────────────────────────────────────────
    if args.get('gender'):
        query = query.filter(Profile.gender == args['gender'])

    # ── age ───────────────────────────────────────────────────────────
    today = date.today()
    if args.get('min_age'):
        try:
            max_dob = f'{today.year - int(args["min_age"])}-12-31'
            query   = query.filter(Profile.date_of_birth <= max_dob)
        except ValueError:
            pass
    if args.get('max_age'):
        try:
            min_dob = f'{today.year - int(args["max_age"])}-01-01'
            query   = query.filter(Profile.date_of_birth >= min_dob)
        except ValueError:
            pass

    # ── height ────────────────────────────────────────────────────────
    if args.get('min_height'):
        try:
            query = query.filter(Profile.height >= int(args['min_height']))
        except ValueError:
            pass
    if args.get('max_height'):
        try:
            query = query.filter(Profile.height <= int(args['max_height']))
        except ValueError:
            pass

    # ── religion ──────────────────────────────────────────────────────
    if args.get('religion'):
        query = query.filter(Profile.religion == args['religion'])

    # ── caste ────────────────────────────────────────────────────────
    if args.get('caste', '').strip():
        query = query.filter(Profile.caste.ilike(f"%{args['caste'].strip()}%"))

    # ── marathi sub-caste (Phase 12) ──────────────────────────────────
    if args.get('marathi_sub_caste', '').strip():
        query = query.filter(
            Profile.marathi_sub_caste == args['marathi_sub_caste'].strip())

    # ── NRI filter (Phase 12) ─────────────────────────────────────────
    if args.get('is_nri') == '1':
        query = query.filter(Profile.is_nri == True)

    # ── mother tongue ─────────────────────────────────────────────────
    if args.get('mother_tongue'):
        query = query.filter(Profile.mother_tongue == args['mother_tongue'])

    # ── marital status ────────────────────────────────────────────────
    if args.get('marital_status'):
        query = query.filter(Profile.marital_status == args['marital_status'])

    # ── manglik ───────────────────────────────────────────────────────
    if args.get('manglik'):
        query = query.filter(Profile.manglik == args['manglik'])

    # ── diet ──────────────────────────────────────────────────────────
    if args.get('diet'):
        query = query.filter(Profile.diet == args['diet'])

    # ── city ──────────────────────────────────────────────────────────
    if args.get('city', '').strip():
        query = query.filter(City.name.ilike(f"%{args['city'].strip()}%"))

    # ── education ────────────────────────────────────────────────────
    if args.get('education', '').strip():
        edu_kw = f"%{args['education'].strip()}%"
        query  = query.filter(or_(
            Education.degree.ilike(edu_kw),
            Education.specialization.ilike(edu_kw),
            Education.institution.ilike(edu_kw),
        ))

    # ── income ───────────────────────────────────────────────────────
    income = args.get('income', '').strip()
    if income:
        if income == '50+':
            query = query.filter(ProfessionalDetails.income_lpa >= 50)
        elif '-' in income:
            parts = income.split('-')
            try:
                query = query.filter(
                    ProfessionalDetails.income_lpa >= int(parts[0]),
                    ProfessionalDetails.income_lpa <= int(parts[1]),
                )
            except (ValueError, IndexError):
                pass

    # ── sort ──────────────────────────────────────────────────────────
    sort = args.get('sort', 'newest')
    if sort == 'newest':
        query = query.order_by(User.created_at.desc())
    else:
        query = query.order_by(User.created_at.asc())

    page    = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.distinct().paginate(page=page, per_page=per_page, error_out=False)
    results    = pagination.items

    return render_template(
        'search/search_results.html',
        results=results,
        pagination=pagination,
        user=current_user,
        religions=RELIGIONS,
        marital_statuses=MARITAL_STATUSES,
        manglik_opts=MANGLIK_OPTS,
        mother_tongues=MOTHER_TONGUES,
        income_ranges=INCOME_RANGES,
        args=args,
        marathi_sub_castes=MARATHI_SUB_CASTES,
    )
