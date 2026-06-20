"""REST API profile endpoints — /api/v1/profiles/*

IDOR pattern: every resource access checks JWT identity owns/participates in it.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import or_
from datetime import datetime, timedelta, date
from app import db, limiter
from app.models import User, Profile, Address, BlockList, Shortlist, Interest
from app.api.errors import api_ok, api_error, NOT_FOUND, FORBIDDEN
from app.api.schemas import profile_full_schema, profile_card_schema
from app.utils import calculate_profile_completeness, calculate_match_score

profiles_api_bp = Blueprint('profiles_api', __name__)


def _get_user_or_404(user_id: int):
    return User.query.get(user_id)


def _blocked_ids(user_id: int):
    rows = BlockList.query.filter(
        or_(BlockList.blocker_id == user_id, BlockList.blocked_id == user_id)
    ).all()
    ids = {r.blocker_id for r in rows} | {r.blocked_id for r in rows}
    ids.discard(user_id)
    return ids


def _eager_user_query():
    return User.query.options(
        joinedload(User.profile),
        selectinload(User.profile_images),
        selectinload(User.subscriptions),
        selectinload(User.addresses).joinedload(Address.city),
        selectinload(User.educations),
        selectinload(User.professional_details),
    )


@profiles_api_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    uid  = int(get_jwt_identity())
    user = _eager_user_query().get(uid)
    if not user:
        return api_error(NOT_FOUND, 'User not found', 404)
    return api_ok(profile_full_schema.dump(user))


@profiles_api_bp.route('/me/completeness', methods=['GET'])
@jwt_required()
def get_completeness():
    uid  = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_error(NOT_FOUND, 'User not found', 404)
    pct, sections = calculate_profile_completeness(user)
    return api_ok({'total': pct, 'sections': sections})


@profiles_api_bp.route('/feed', methods=['GET'])
@jwt_required()
@limiter.limit('60 per minute')
def get_feed():
    uid     = int(get_jwt_identity())
    me      = _eager_user_query().get(uid)
    if not me:
        return api_error(NOT_FOUND, 'User not found', 404)

    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, request.args.get('per_page', 20, type=int))
    tab      = request.args.get('tab', 'all')   # all | new | near | mutual

    blocked  = _blocked_ids(uid)
    p        = me.profile
    looking_for = p.looking_for if p else None
    gender      = p.gender      if p else None

    q = (User.query
         .join(Profile)
         .filter(
             User.id            != uid,
             User.is_active_acc == True,
             User.is_hidden     == False,
             User.is_staff      == False,
         ))
    if blocked:
        q = q.filter(User.id.notin_(blocked))
    if looking_for:
        q = q.filter(Profile.gender == looking_for)
    elif gender:
        q = q.filter(Profile.gender != gender)

    # ── Tab filters ──────────────────────────────────────────────────────────
    if tab == 'new':
        cutoff = datetime.utcnow() - timedelta(days=7)
        q = q.filter(User.created_at >= cutoff)

    elif tab == 'near':
        if me.addresses:
            from app.models import Address as Addr
            city_id = me.addresses[0].city_id if me.addresses[0].city_id else None
            if city_id:
                q = q.join(Addr, Addr.user_id == User.id).filter(Addr.city_id == city_id)

    elif tab == 'mutual':
        my_shortlist = {s.shortlisted_id for s in
                        Shortlist.query.filter_by(user_id=uid).all()}
        shortlisted_me = {s.user_id for s in
                          Shortlist.query.filter_by(shortlisted_id=uid).all()}
        mutual = list(my_shortlist & shortlisted_me)
        if not mutual:
            return api_ok([], meta={'page': page, 'per_page': per_page,
                                    'total': 0, 'pages': 0, 'tab': tab})
        q = q.filter(User.id.in_(mutual))

    # Eager load for scoring + serialization
    q = q.options(
        joinedload(User.profile),
        selectinload(User.profile_images),
        selectinload(User.subscriptions),
        selectinload(User.addresses).joinedload(Address.city),
        selectinload(User.educations),
        selectinload(User.professional_details),
    )

    # Score, sort, paginate manually (score-sort requires Python, not SQL)
    candidates = q.limit(200).all()
    from app.utils import get_signal_boost
    scored = []
    for c in candidates:
        score = calculate_match_score(me, c)
        boost = get_signal_boost(uid, c.id)
        score = max(0, min(100, score + boost))
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)

    total       = len(scored)
    start       = (page - 1) * per_page
    page_items  = scored[start:start + per_page]

    serialized = []
    for score, u in page_items:
        d = profile_card_schema.dump(u)
        d['match_score'] = score
        serialized.append(d)

    return api_ok(serialized, meta={
        'page': page, 'per_page': per_page,
        'total': total, 'pages': (total + per_page - 1) // per_page,
        'tab': tab,
    })


@profiles_api_bp.route('/<username>', methods=['GET'])
@jwt_required()
def get_profile(username):
    uid  = int(get_jwt_identity())
    user = _eager_user_query().filter_by(username=username).first()
    if not user or not user.is_active_acc:
        return api_error(NOT_FOUND, 'Profile not found', 404)

    # IDOR: block check
    blocked = _blocked_ids(uid)
    if user.id in blocked:
        return api_error(NOT_FOUND, 'Profile not found', 404)

    # Track view (once per 24h)
    if user.id != uid:
        from app.models import ProfileView
        cutoff = datetime.utcnow() - timedelta(hours=24)
        already = (ProfileView.query
                   .filter_by(viewer_id=uid, viewed_id=user.id)
                   .filter(ProfileView.timestamp >= cutoff)
                   .count())
        if not already:
            db.session.add(ProfileView(viewer_id=uid, viewed_id=user.id,
                                       timestamp=datetime.utcnow()))
            db.session.commit()

    data = profile_full_schema.dump(user)

    # Add interest status relative to caller
    interest = (Interest.query
                .filter(
                    or_(
                        (Interest.sender_id == uid) & (Interest.receiver_id == user.id),
                        (Interest.sender_id == user.id) & (Interest.receiver_id == uid),
                    )
                ).first())
    data['interest_status'] = interest.status if interest else None
    data['interest_direction'] = (
        'sent'     if interest and interest.sender_id == uid else
        'received' if interest else None
    )

    return api_ok(data)
