import boto3, uuid, os, secrets
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from app import db


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def _resize_and_upload(s3, image_pil, bucket, region, key, size):
    import io
    img = image_pil.copy()
    w, h    = img.size
    min_dim = min(w, h)
    left    = (w - min_dim) // 2
    top     = (h - min_dim) // 2
    img     = img.crop((left, top, left + min_dim, top + min_dim))
    img     = img.resize((size, size))
    buf     = io.BytesIO()
    img.convert('RGB').save(buf, 'JPEG', quality=85, optimize=True)
    buf.seek(0)
    s3.upload_fileobj(buf, bucket, key, ExtraArgs={'ContentType': 'image/jpeg',
                                                    'ACL': 'private'})  # private — use signed URLs
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def get_signed_image_url(image_url: str, expiry: int = 3600) -> str:
    """
    Return a pre-signed S3 URL that expires after `expiry` seconds (default 1 hour).
    Falls back to the original URL if S3 is not configured or URL is not an S3 URL.
    Used in templates via the |signed_url filter.
    """
    if not image_url or 's3.amazonaws.com' not in image_url:
        return image_url or ''
    try:
        region = current_app.config.get('AWS_REGION', '')
        bucket = current_app.config.get('AWS_S3_BUCKET', '')
        if not region or not bucket:
            return image_url
        # Extract key from full S3 URL: https://bucket.s3.region.amazonaws.com/key
        parts = image_url.split('.amazonaws.com/')
        if len(parts) < 2:
            return image_url
        key = parts[1]
        s3  = boto3.client('s3', region_name=region)
        return s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiry,
        )
    except Exception as e:
        current_app.logger.warning(f'Signed URL failed for {image_url}: {e}')
        return image_url


def upload_image_to_s3(file, user_id=None):
    """Upload to S3 in 3 sizes. Returns (full_url, thumb_url, card_url, error)."""
    from PIL import Image
    import io

    if not file or file.filename == '':
        return None, None, None, 'No file selected.'
    if not allowed_file(file.filename):
        return None, None, None, 'Only JPG/PNG files are allowed.'

    # Guard: check S3 is configured before attempting upload
    bucket = current_app.config.get('AWS_S3_BUCKET', '')
    region = current_app.config.get('AWS_REGION', '')
    if not bucket or not region:
        current_app.logger.warning('S3 upload skipped: AWS_S3_BUCKET or AWS_REGION not configured')
        return None, None, None, 'Photo uploads are temporarily unavailable. Please try again later.'

    try:
        raw   = file.read()
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')

        uid    = user_id or 'u'
        base   = f"profiles/{uid}/{uuid.uuid4().hex}"
        bucket = current_app.config['AWS_S3_BUCKET']
        region = current_app.config['AWS_REGION']
        s3     = boto3.client('s3', region_name=region)

        full_url  = _resize_and_upload(s3, image, bucket, region, f"{base}.jpg",   800)
        card_url  = _resize_and_upload(s3, image, bucket, region, f"{base}_c.jpg", 400)
        thumb_url = _resize_and_upload(s3, image, bucket, region, f"{base}_t.jpg", 150)

        return full_url, thumb_url, card_url, None
    except Exception as e:
        current_app.logger.error(f"S3 upload error: {e}")
        return None, None, None, 'Upload failed. Please try again.'


def delete_image_from_s3(image_url):
    try:
        bucket = current_app.config['AWS_S3_BUCKET']
        region = current_app.config['AWS_REGION']
        key    = '/'.join(image_url.split('/')[-3:])  # profiles/uid/filename
        boto3.client('s3', region_name=region).delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        current_app.logger.warning(f"S3 delete error: {e}")


def calculate_profile_completeness(user):
    score = 0
    # Basic (20)
    if user.first_name:  score += 2
    if user.last_name:   score += 2
    if user.username:    score += 2
    if user.email:       score += 2
    if user.phone:       score += 2
    p = user.profile
    if p:
        if p.date_of_birth:  score += 3
        if p.gender:         score += 2
        if p.looking_for:    score += 1
        if p.height:         score += 1
        if p.bio:            score += 3
        if p.religion:       score += 2
        if p.caste:          score += 1
        if p.marital_status: score += 1
        if p.mother_tongue:  score += 1
        if p.diet:           score += 1
        if p.birth_city or p.birth_state: score += 2
    # Address (8)
    for addr in (user.addresses or []):
        if addr.address1 and addr.city_id:
            score += 8; break
    # Photos (10)
    imgs = user.profile_images or []
    if any(i.is_primary for i in imgs):   score += 6
    extras = [i for i in imgs if not i.is_primary]
    score += min(len(extras), 2) * 2
    # Family (5)
    score += min(len(user.family_details or []), 5)
    # Education (8)
    for edu in (user.educations or []):
        if edu.degree and edu.institution:
            score += 8; break
    # Professional (8)
    for job in (user.professional_details or []):
        if job.occupation:
            score += 8; break
    # Languages (3)
    score += min(len(user.languages or []), 3)
    return min(int((score / 100) * 100), 100)


def generate_token(length=32):
    return secrets.token_urlsafe(length)


def send_email(to, subject, html_body):
    """Send email via AWS SES. Returns True on success, False if not configured or on error."""
    # Skip immediately if SES not configured — prevents hanging
    mail_from  = current_app.config.get('MAIL_FROM', '')
    aws_region = current_app.config.get('AWS_REGION', '')
    if not mail_from or not aws_region:
        current_app.logger.info(f'Email skipped (SES not configured): {to}')
        return False
    try:
        region = current_app.config.get('AWS_REGION', 'ap-south-1')
        ses    = boto3.client('ses', region_name=region)
        ses.send_email(
            Source=current_app.config.get('MAIL_FROM', 'noreply@ijodidar.in'),
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body':    {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
            }
        )
        return True
    except Exception as e:
        current_app.logger.error(f"SES email error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  MATCH SCORE ALGORITHM
# ─────────────────────────────────────────────────────────────────────────────
def calculate_match_score(current_user, candidate):
    """
    Score how well candidate matches current_user's PartnerPreference.
    Returns integer 0-100. Incorporates behavioral signal boost/suppress.
    Signal boost: accepted interests +2, shortlisted +0.5, blocked -2, reported -3.
    """
    from app.models import PartnerPreference
    from datetime import date

    pref = current_user.partner_preference
    cp   = candidate.profile
    if not cp:
        return 0

    # No preferences — return lightweight score based on profile fill
    if not pref:
        score = 0
        if cp.religion:      score += 5
        if cp.date_of_birth: score += 5
        if cp.height:        score += 5
        if cp.education_level if hasattr(cp,'education_level') else candidate.educations: score += 5
        if candidate.profile_images: score += 10
        return min(score + 10, 40)

    score = 0
    MAX   = 90

    # Religion (+20)
    if pref.religion and cp.religion:
        if pref.religion.lower() == cp.religion.lower():
            score += 20

    # Age (+15)
    if pref.min_age and pref.max_age and cp.date_of_birth:
        try:
            for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
                try:
                    dob = __import__('datetime').datetime.strptime(cp.date_of_birth, fmt).date()
                    break
                except ValueError:
                    continue
            age = date.today().year - dob.year
            if pref.min_age <= age <= pref.max_age:
                score += 15
            elif abs(age - pref.min_age) <= 2 or abs(age - pref.max_age) <= 2:
                score += 7   # partial — within 2 years of range
        except Exception:
            pass

    # Caste (+12)
    if pref.caste and cp.caste:
        if pref.caste.lower().strip() == cp.caste.lower().strip():
            score += 12
        elif pref.caste.lower() in cp.caste.lower():
            score += 5   # partial match

    # Location (+10)
    if pref.location_preference and candidate.addresses:
        loc_pref = pref.location_preference.lower()
        for addr in candidate.addresses:
            if addr.city and loc_pref in addr.city.name.lower():
                score += 10; break
            if addr.state and loc_pref in addr.state.name.lower():
                score += 5; break

    # Height (+8)
    if pref.min_height and pref.max_height and cp.height:
        if pref.min_height <= cp.height <= pref.max_height:
            score += 8
        elif abs(cp.height - pref.min_height) <= 5 or abs(cp.height - pref.max_height) <= 5:
            score += 3

    # Mother tongue (+8)
    if pref.mother_tongue and cp.mother_tongue:
        if pref.mother_tongue.lower() == cp.mother_tongue.lower():
            score += 8

    # Education (+7)
    if pref.education_level and candidate.educations:
        edu = candidate.educations[0]
        if pref.education_level.lower() in (edu.degree or '').lower():
            score += 7
        elif pref.education_level.lower() in (edu.specialization or '').lower():
            score += 4

    # Diet (+5)
    if pref.diet and cp.diet:
        if pref.diet.lower() == cp.diet.lower():
            score += 5

    # Marital status (+5)
    if pref.marital_status and cp.marital_status:
        if pref.marital_status.lower() == cp.marital_status.lower():
            score += 5

    # Profile photo bonus (+5 — improves ranking of complete profiles)
    if candidate.profile_images:
        score += 5

    # Hobbies match bonus (+5 — Phase 12)
    if pref.about and cp.hobbies:
        import json
        try:
            candidate_hobbies = json.loads(cp.hobbies or '[]')
            # Check if any candidate hobby keyword appears in preferences text
            for h in candidate_hobbies:
                if h.lower() in (pref.about or '').lower():
                    score += 5
                    break
        except Exception:
            pass

    pct = round((score / MAX) * 100)
    base_score = min(pct, 100)

    # Behavioral signal boost/suppress — max ±15 points
    try:
        boost = get_signal_boost(current_user.id, candidate.id)
        signal_pts = int(boost * 5)
        base_score = max(0, min(base_score + signal_pts, 100))
    except Exception:
        pass

    # Guna Milan compatibility boost (when both users have kundli data)
    # 28+ gunas → +5 pts  |  18-27 → +2 pts  |  <18 → -3 pts
    try:
        from app.models import KundliDetail
        my_kd    = KundliDetail.query.filter_by(user_id=current_user.id).first()
        other_kd = KundliDetail.query.filter_by(user_id=candidate.id).first()
        if my_kd and other_kd and my_kd.nakshatra and other_kd.nakshatra:
            from app.utils_kundli import calculate_guna_milan
            guna = calculate_guna_milan(my_kd.nakshatra, other_kd.nakshatra)
            if guna.get('available') and guna.get('score') is not None:
                g = guna['score']
                if g >= 28:
                    base_score = min(base_score + 5, 100)
                elif g >= 18:
                    base_score = min(base_score + 2, 100)
                elif g < 18:
                    base_score = max(base_score - 3, 0)
    except Exception:
        pass   # never fail the main score

    return base_score


def create_notification(user_id, notif_type, message, link=None):
    """Create an in-app notification. Safe to call anywhere."""
    try:
        from app.models import Notification
        n = Notification(user_id=user_id, type=notif_type,
                         message=message, link=link or '')
        db.session.add(n)
        db.session.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Notification create failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  REFERRAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def generate_referral_code(user_id):
    """Generate a short unique referral code like IJD-A3F9K2."""
    import string, random
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f"IJD-{suffix}"


def get_or_create_referral(user):
    """Get existing referral code for user, or create one."""
    from app.models import Referral
    ref = Referral.query.filter_by(referrer_id=user.id, referred_id=None).first()
    if not ref:
        code = generate_referral_code(user.id)
        # Ensure uniqueness
        while Referral.query.filter_by(code=code).first():
            code = generate_referral_code(user.id)
        ref = Referral(referrer_id=user.id, code=code)
        db.session.add(ref)
        db.session.commit()
    return ref


def record_signal(user_id: int, target_user_id: int, signal_type: str):
    """
    Record a user behavior signal for match learning.
    Fire-and-forget — never raises exceptions to caller.
    Signal values: interest_sent=1, interest_accepted=2, interest_declined=-1,
                   profile_viewed=0.3, shortlisted=0.5, blocked=-2, reported=-3
    """
    SIGNAL_VALUES = {
        'interest_sent':      1.0,
        'interest_accepted':  2.0,
        'interest_declined': -1.0,
        'profile_viewed':     0.3,
        'shortlisted':        0.5,
        'blocked':           -2.0,
        'reported':          -3.0,
    }
    try:
        from app.models import UserSignal
        value = SIGNAL_VALUES.get(signal_type, 0)
        db.session.add(UserSignal(
            user_id        = user_id,
            target_user_id = target_user_id,
            signal_type    = signal_type,
            signal_value   = value,
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()   # never crash caller


def get_signal_boost(user_id: int, candidate_id: int) -> float:
    """
    Return a score modifier based on past signals between user and candidates
    with similar profiles. Simple version: direct signal to this candidate.
    Range: -3.0 (blocked/reported) to +2.0 (accepted).
    """
    try:
        from app.models import UserSignal
        from sqlalchemy import func
        result = db.session.query(func.sum(UserSignal.signal_value))                           .filter_by(user_id=user_id,
                                      target_user_id=candidate_id)                           .scalar()
        return float(result or 0)
    except Exception:
        return 0.0


def reward_referred(referred_user):
    """Grant the referred user 15-day Silver plan as welcome bonus."""
    from app.models import MembershipPlan, UserSubscription
    from datetime import datetime, timedelta
    silver = MembershipPlan.query.filter_by(name='Silver').first()
    if not silver:
        return
    # Only if they don't already have a paid plan
    sub = referred_user.active_subscription
    if sub and sub.amount_paid > 0:
        return
    UserSubscription.query.filter_by(
        user_id=referred_user.id, is_active=True).update({'is_active': False})
    db.session.add(UserSubscription(
        user_id     = referred_user.id,
        plan_id     = silver.id,
        expires_at  = datetime.utcnow() + timedelta(days=15),
        is_active   = True,
        payment_ref = 'referral_welcome_bonus',
        amount_paid = 0,
    ))
    db.session.commit()


def reward_referrer(referrer):
    """Grant referrer 30-day Silver plan as reward."""
    from app.models import MembershipPlan, UserSubscription
    from datetime import datetime, timedelta
    silver = MembershipPlan.query.filter_by(name='Silver').first()
    if not silver:
        return
    # Only reward if they don't already have Silver or higher
    sub = referrer.active_subscription
    if sub and sub.plan.price_inr >= silver.price_inr:
        return
    UserSubscription.query.filter_by(user_id=referrer.id, is_active=True)\
                          .update({'is_active': False})
    db.session.add(UserSubscription(
        user_id     = referrer.id,
        plan_id     = silver.id,
        expires_at  = datetime.utcnow() + timedelta(days=30),
        is_active   = True,
        payment_ref = 'referral_reward',
        amount_paid = 0,
    ))
    db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
#  MANGLIK COMPATIBILITY
# ─────────────────────────────────────────────────────────────────────────────
def manglik_compatible(profile1, profile2):
    """
    Returns (compatible: bool, message: str).
    Traditional rule: Manglik + Non-Manglik = not compatible.
    Manglik + Manglik = compatible. Partial + Any = compatible.
    None/unknown = compatible (no data).
    """
    m1 = (profile1.manglik or '').strip() if profile1 else ''
    m2 = (profile2.manglik or '').strip() if profile2 else ''

    if not m1 or not m2:
        return True, 'Manglik status not available for one or both profiles.'
    if m1 == 'Partial' or m2 == 'Partial':
        return True, 'Partial Manglik — generally considered compatible.'
    if m1 == m2:
        if m1 == 'Yes':
            return True, 'Both Manglik — compatible per traditional rules.'
        return True, 'Both Non-Manglik — compatible.'
    # One Yes, one No
    return False, ('One profile is Manglik and the other is not. '
                   'Many families consider this incompatible. '
                   'Please consult a family astrologer.')


# ─────────────────────────────────────────────────────────────────────────────
#  AADHAAR / DIGILOCKER ID VERIFICATION  (Phase 14.2)
# ─────────────────────────────────────────────────────────────────────────────
def send_aadhaar_otp(aadhaar_number, phone):
    """
    Send OTP to Aadhaar-linked mobile via UIDAI / KYC provider.
    Production: use Signzy / Karza / Surepass API (~₹10-20 per KYC).
    Dev mode: returns mock OTP printed to console.
    Returns (success: bool, ref_id: str, error: str|None)
    """
    import random
    key = current_app.config.get('KYC_API_KEY', '')

    if not key:
        # Dev mode — simulate OTP
        mock_ref = f"MOCK-{random.randint(100000,999999)}"
        mock_otp = str(random.randint(100000, 999999))
        current_app.logger.info(
            f"[DEV AADHAAR OTP] Aadhaar:{aadhaar_number[-4:]} "
            f"Ref:{mock_ref} OTP:{mock_otp}")
        return True, mock_ref, None

    # Production: Surepass Aadhaar OTP API example
    try:
        import requests
        resp = requests.post(
            "https://kyc-api.surepass.io/api/v1/aadhaar-v2/send-otp",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type":  "application/json"},
            json={"id_number": aadhaar_number},
            timeout=15,
        )
        data = resp.json()
        if data.get("success"):
            return True, data["data"]["client_id"], None
        return False, '', data.get("message", "OTP send failed")
    except Exception as e:
        current_app.logger.error(f"Aadhaar OTP error: {e}")
        return False, '', "Service unavailable. Try again."


def verify_aadhaar_otp(ref_id, otp, user):
    """
    Verify Aadhaar OTP and grant ID Verified badge.
    Dev mode: any 6-digit OTP passes.
    Returns (verified: bool, error: str|None)
    """
    key = current_app.config.get('KYC_API_KEY', '')

    if not key:
        # Dev mode — any 6-digit OTP passes
        if len(otp) == 6 and otp.isdigit():
            _grant_id_verified(user)
            return True, None
        return False, "Enter a valid 6-digit OTP."

    try:
        import requests
        resp = requests.post(
            "https://kyc-api.surepass.io/api/v1/aadhaar-v2/submit-otp",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type":  "application/json"},
            json={"client_id": ref_id, "otp": otp},
            timeout=15,
        )
        data = resp.json()
        if data.get("success"):
            _grant_id_verified(user)
            return True, None
        return False, data.get("message", "Invalid OTP.")
    except Exception as e:
        current_app.logger.error(f"Aadhaar verify error: {e}")
        return False, "Verification failed. Try again."


def _grant_id_verified(user):
    """Mark profile as ID-verified and notify user."""
    from datetime import datetime
    p = user.profile
    if not p:
        from app.models import Profile
        p = Profile(user_id=user.id)
        db.session.add(p)
    p.id_verified    = True
    p.id_verified_at = datetime.utcnow()
    db.session.commit()
    create_notification(
        user_id    = user.id,
        notif_type = 'system',
        message    = '🆔 Your Aadhaar-verified badge is now active on your profile!',
        link       = f'/{user.username}',
    )


# ─────────────────────────────────────────────────────────────────────────────
#  WHATSAPP BUSINESS API  (Phase 14.3)
# ─────────────────────────────────────────────────────────────────────────────
def send_whatsapp(phone, template_name, params):
    """
    Send WhatsApp template message via Meta Business API.
    Requires WHATSAPP_TOKEN + WHATSAPP_PHONE_NUMBER_ID in config.
    Free tier: 1,000 conversations/month.
    Dev mode (no token): logs to console.
    
    Args:
        phone:         10-digit Indian number (no +91)
        template_name: 'interest_received' | 'interest_accepted' | 
                       'new_message' | 'plan_purchased' | 'otp'
        params:        list of string values for template placeholders
    """
    token    = current_app.config.get('WHATSAPP_TOKEN', '')
    phone_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID', '')

    # Dev mode
    if not token or not phone_id:
        current_app.logger.info(
            f"[DEV WhatsApp] → +91{phone} | "
            f"template={template_name} | params={params}")
        return True

    # Template definitions (create these in Meta Business Manager)
    template_map = {
        'interest_received': {
            'name':     'ijodidar_interest_received',
            'language': {'code': 'en'},
            'components': [{'type': 'body',
                'parameters': [{'type': 'text', 'text': p} for p in params]}],
        },
        'interest_accepted': {
            'name':     'ijodidar_interest_accepted',
            'language': {'code': 'en'},
            'components': [{'type': 'body',
                'parameters': [{'type': 'text', 'text': p} for p in params]}],
        },
        'new_message': {
            'name':     'ijodidar_new_message',
            'language': {'code': 'en'},
            'components': [{'type': 'body',
                'parameters': [{'type': 'text', 'text': p} for p in params]}],
        },
        'plan_purchased': {
            'name':     'ijodidar_plan_purchased',
            'language': {'code': 'en'},
            'components': [{'type': 'body',
                'parameters': [{'type': 'text', 'text': p} for p in params]}],
        },
    }

    payload = template_map.get(template_name)
    if not payload:
        current_app.logger.warning(f"WhatsApp: unknown template {template_name}")
        return False

    try:
        import requests
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type":  "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to":               f"91{phone}",
                "type":             "template",
                "template":         payload,
            },
            timeout=10,
        )
        result = resp.json()
        if resp.status_code == 200:
            return True
        current_app.logger.error(f"WhatsApp error: {result}")
        return False
    except Exception as e:
        current_app.logger.error(f"WhatsApp exception: {e}")
        return False
