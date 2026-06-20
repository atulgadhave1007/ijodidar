# iJodidar — API-First Architecture
## REST API Design for Mobile App + Future Integrations
## June 2026

---

## WHY API-FIRST NOW

iJodidar currently has zero REST API surface except 4 JSON endpoints.
A React Native or Flutter mobile app requires a complete REST API.
Building the API now takes 2-3 weeks. Building it "later" means rewriting everything twice.

The approach: **Add API layer to existing Flask app.**
Web app (HTML routes) continues unchanged.
Mobile app calls `/api/v1/` endpoints.
They share the same models, business logic, and Celery tasks.

---

## AUTHENTICATION DESIGN

### Why not Flask sessions for mobile
Flask sessions use browser cookies. Mobile HTTP clients don't maintain cookies across app restarts. JWT tokens are the standard for mobile API authentication.

### JWT token strategy

```
Access token:  1 hour expiry (short, security)
Refresh token: 30 days expiry (long, UX)
Storage:       Secure storage (Keychain on iOS, EncryptedSharedPreferences on Android)
```

```python
# requirements.txt additions
Flask-JWT-Extended==4.6.0
marshmallow==3.22.0
marshmallow-sqlalchemy==1.1.0
```

```python
# app/__init__.py — add to create_app()
from flask_jwt_extended import JWTManager
jwt = JWTManager()

# In create_app():
jwt.init_app(app)
app.config['JWT_SECRET_KEY']             = app.config['SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES']  = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_TOKEN_LOCATION']        = ['headers']
app.config['JWT_HEADER_NAME']           = 'Authorization'
app.config['JWT_HEADER_TYPE']           = 'Bearer'
```

---

## API BLUEPRINT STRUCTURE

```
app/
  api/
    __init__.py
    auth.py          → /api/v1/auth/*
    profiles.py      → /api/v1/profiles/*
    interests.py     → /api/v1/interests/*
    conversations.py → /api/v1/conversations/*
    notifications.py → /api/v1/notifications/*
    kundli.py        → /api/v1/kundli/*
    devices.py       → /api/v1/devices/*
    plans.py         → /api/v1/plans/*
    schemas.py       → Marshmallow serializers
    errors.py        → Standard error responses
```

---

## STANDARD RESPONSE FORMAT

```json
// Success
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "total": 142, "pages": 8 }
}

// Error
{
  "success": false,
  "error": {
    "code": "INVALID_OTP",
    "message": "The OTP you entered is incorrect or has expired.",
    "field": "otp"
  }
}

// Paginated list
{
  "success": true,
  "data": [ {...}, {...} ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 142,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## COMPLETE API SPECIFICATION

### Auth Endpoints

```
POST   /api/v1/auth/send-otp
Body:  { "phone": "9876543210", "name": "Atul Gadhave" }
Notes: Creates user if not exists, sends OTP via MSG91
Returns: { "success": true, "data": { "otp_sent": true, "is_new_user": true } }

POST   /api/v1/auth/verify-otp
Body:  { "phone": "9876543210", "otp": "123456" }
Returns: { 
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "user": { "id": 1, "name": "Atul", "is_new_user": true }
  }
}
Error codes: INVALID_OTP, EXPIRED_OTP, LOCKED (too many attempts)

POST   /api/v1/auth/refresh
Header: Authorization: Bearer <refresh_token>
Returns: { "success": true, "data": { "access_token": "eyJ..." } }

POST   /api/v1/auth/logout
Header: Authorization: Bearer <access_token>
Body:  { "fcm_token": "fcm_token_to_deregister" }
Returns: { "success": true }
```

### Profile Endpoints

```
GET    /api/v1/profiles/me
Header: Authorization: Bearer <access_token>
Returns: { "success": true, "data": { <full profile> } }

PATCH  /api/v1/profiles/me
Header: Authorization: Bearer <access_token>
Body:  { "section": "about", "fields": { "bio": "...", "height": 172 } }
Returns: { "success": true, "data": { "completeness": 72, "section_score": 18 } }

GET    /api/v1/profiles/feed
Header: Authorization: Bearer <access_token>
Query: ?tab=best&page=1
Returns: { "success": true, "data": [<profile cards>], "meta": {...} }

GET    /api/v1/profiles/@<username>
Header: Authorization: Bearer <access_token>
Returns: { "success": true, "data": { <full profile + interest status + match score> } }

GET    /api/v1/profiles/completeness
Header: Authorization: Bearer <access_token>
Returns: {
  "success": true,
  "data": {
    "total": 72,
    "sections": {
      "about":   { "score": 18, "max": 25, "missing": ["bio", "hobbies"] },
      "career":  { "score": 12, "max": 20, "missing": ["income_lpa"] },
      "family":  { "score": 5,  "max": 15, "missing": ["about_family"] },
      "photos":  { "score": 12, "max": 20, "missing": ["second_photo"] },
      "prefs":   { "score": 10, "max": 10, "missing": [] }
    }
  }
}

POST   /api/v1/profiles/photos
Header: Authorization: Bearer <access_token>
Body:  multipart/form-data — image file
Returns: { "success": true, "data": { "id": 42, "url": "...", "thumb_url": "..." } }

DELETE /api/v1/profiles/photos/<id>
PATCH  /api/v1/profiles/photos/<id>/primary
```

### Interest Endpoints

```
POST   /api/v1/interests
Header: Authorization: Bearer <access_token>
Body:  { "receiver_id": 42, "message": "..." }
Returns: { "success": true, "data": { "interest_id": 99, "remaining": 14 } }
Error: LIMIT_REACHED, NOT_VERIFIED, ALREADY_SENT

GET    /api/v1/interests/received
GET    /api/v1/interests/sent
GET    /api/v1/interests/accepted
Query: ?page=1&per_page=20
Returns: { "success": true, "data": [<interest objects>], "meta": {...} }

PATCH  /api/v1/interests/<id>
Body:  { "action": "accept" | "decline" | "withdraw" }
Returns: { "success": true, "data": { "conversation_id": 55 } }  // on accept

GET    /api/v1/profiles/viewers
Header: Authorization: Bearer <access_token>
Returns: { "success": true, "data": [<viewer cards>] }
```

### Messaging Endpoints

```
GET    /api/v1/conversations
Header: Authorization: Bearer <access_token>
Returns: { "success": true, "data": [<conversation previews>] }

GET    /api/v1/conversations/<id>/messages
Header: Authorization: Bearer <access_token>
Query: ?page=1&per_page=50&before=<message_id>
Returns: { "success": true, "data": [<messages>], "meta": {...} }

POST   /api/v1/conversations/<id>/messages
Header: Authorization: Bearer <access_token>
Body:  { "body": "Hello!" }
Returns: { "success": true, "data": { <message object> } }
Error: NOT_PHONE_VERIFIED, NOT_CONNECTED, PLAN_REQUIRED

PATCH  /api/v1/conversations/<id>/read
Returns: { "success": true }
```

### Notification Endpoints

```
GET    /api/v1/notifications
GET    /api/v1/notifications/unread-count
PATCH  /api/v1/notifications/read    → mark all read

POST   /api/v1/devices
Body:  { "fcm_token": "...", "platform": "android" | "ios" }
DELETE /api/v1/devices/<fcm_token>
```

### Kundli Endpoints (already JSON, just need auth header)

```
POST   /api/v1/kundli/calculate
Body:  { "birth_date": "1995-06-15", "birth_time": "09:30", "birth_city": "Pune" }
Returns: { nakshatra, rashi, charan, gana, nadi, manglik, notes }

GET    /api/v1/kundli/match/<user_id>
Returns: { score, koots, nadi_dosha, gotra_compatible, manglik_compatible }
```

---

## MARSHMALLOW SCHEMAS

```python
# app/api/schemas.py
from marshmallow import Schema, fields, validate
from datetime import date

class ProfileCardSchema(Schema):
    """Compact profile — for feed and search results."""
    id           = fields.Int(dump_only=True)
    username     = fields.Str()
    first_name   = fields.Str()
    age          = fields.Method('get_age')
    city         = fields.Method('get_city')
    religion     = fields.Str(attribute='profile.religion')
    caste        = fields.Str(attribute='profile.caste')
    occupation   = fields.Method('get_occupation')
    photo_url    = fields.Method('get_photo_url')
    thumb_url    = fields.Method('get_thumb_url')
    match_score  = fields.Int(dump_only=True)   # injected by view
    trust_score  = fields.Int()
    trust_label  = fields.Str()
    plan_name    = fields.Str()
    is_spotlight = fields.Bool(attribute='profile.is_spotlight')

    def get_age(self, obj):
        p = obj.profile
        if not p: return None
        dob = p.dob or (
            __import__('datetime').datetime.strptime(p.date_of_birth, '%Y-%m-%d').date()
            if p.date_of_birth else None
        )
        if not dob: return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_city(self, obj):
        for addr in obj.addresses:
            if addr.city: return addr.city.name
        return obj.profile.birth_city if obj.profile else None

    def get_occupation(self, obj):
        for pro in obj.professional_details:
            if pro.occupation: return pro.occupation
        return None

    def get_photo_url(self, obj):
        from app.utils import get_signed_image_url
        for img in obj.profile_images:
            if img.is_primary:
                return get_signed_image_url(img.image_url, expiry=3600)
        return None

    def get_thumb_url(self, obj):
        from app.utils import get_signed_image_url
        for img in obj.profile_images:
            if img.is_primary:
                return get_signed_image_url(img.thumb_url or img.image_url, expiry=3600)
        return None


class ProfileFullSchema(ProfileCardSchema):
    """Full profile — for profile view page."""
    last_name       = fields.Str()
    email           = fields.Str()
    phone           = fields.Method('get_phone')   # only if plan allows
    height          = fields.Int(attribute='profile.height')
    weight          = fields.Int(attribute='profile.weight')
    bio             = fields.Str(attribute='profile.bio')
    religion        = fields.Str(attribute='profile.religion')
    caste           = fields.Str(attribute='profile.caste')
    sub_caste       = fields.Str(attribute='profile.sub_caste')
    gotra           = fields.Str(attribute='profile.gotra')
    marital_status  = fields.Str(attribute='profile.marital_status')
    mother_tongue   = fields.Str(attribute='profile.mother_tongue')
    diet            = fields.Str(attribute='profile.diet')
    smoking         = fields.Str(attribute='profile.smoking')
    drinking        = fields.Str(attribute='profile.drinking')
    family_type     = fields.Str(attribute='profile.family_type')
    family_status   = fields.Str(attribute='profile.family_status')
    is_nri          = fields.Bool(attribute='profile.is_nri')
    nri_country     = fields.Str(attribute='profile.nri_country')
    nakshatra       = fields.Str(attribute='profile.birth_nakshatra')
    rashi           = fields.Str(attribute='profile.birth_rashi')
    manglik         = fields.Str(attribute='profile.manglik')
    hobbies         = fields.Method('get_hobbies')
    photos          = fields.Method('get_photos')
    educations      = fields.Method('get_educations')
    professional    = fields.Method('get_professional')
    completeness    = fields.Int()

    def get_phone(self, obj):
        # Only return phone if viewer has Gold+ plan AND interest is accepted
        # This is injected by the view based on viewer context
        return None  # populated by view

    def get_hobbies(self, obj):
        import json
        if obj.profile and obj.profile.hobbies:
            try: return json.loads(obj.profile.hobbies)
            except: return []
        return []

    def get_photos(self, obj):
        from app.utils import get_signed_image_url
        return [
            {'id': img.id, 'url': get_signed_image_url(img.image_url), 'is_primary': img.is_primary}
            for img in obj.profile_images
        ]

    def get_educations(self, obj):
        return [
            {'degree': e.degree, 'specialization': e.specialization, 'institution': e.institution}
            for e in obj.educations
        ]

    def get_professional(self, obj):
        for p in obj.professional_details:
            return {'occupation': p.occupation, 'company': p.company_name,
                    'income_lpa': p.income_lpa, 'employment_type': p.employment_type}
        return {}
```

---

## ERROR CODES REFERENCE

```python
# app/api/errors.py
API_ERRORS = {
    # Auth
    'INVALID_OTP':       (400, "The OTP you entered is incorrect or expired."),
    'OTP_EXPIRED':       (400, "OTP has expired. Please request a new one."),
    'ACCOUNT_LOCKED':    (429, "Too many failed attempts. Try again in 30 minutes."),
    'NOT_AUTHENTICATED': (401, "Please sign in to continue."),
    'TOKEN_EXPIRED':     (401, "Your session has expired. Please sign in again."),

    # Verification
    'EMAIL_NOT_VERIFIED': (403, "Please verify your email to perform this action."),
    'PHONE_NOT_VERIFIED': (403, "Please verify your phone number to send messages."),

    # Rate / limits
    'INTEREST_LIMIT':    (429, "You've reached your monthly interest limit. Upgrade to send more."),
    'PLAN_REQUIRED':     (403, "Upgrade your plan to access this feature."),

    # Resources
    'NOT_FOUND':         (404, "The requested resource was not found."),
    'ALREADY_EXISTS':    (409, "This action has already been performed."),

    # Input
    'VALIDATION_ERROR':  (422, "Please check your input and try again."),
}

def api_error(code, **kwargs):
    msg  = kwargs.get('message') or API_ERRORS.get(code, (400, "Unknown error"))[1]
    status = API_ERRORS.get(code, (400, ""))[0]
    return {'success': False, 'error': {'code': code, 'message': msg, **kwargs}}, status
```

---

## RATE LIMITING FOR API

```python
# Per-token rate limits (not per-IP for authenticated API)
API_RATE_LIMITS = {
    '/api/v1/auth/send-otp':   '5 per hour per phone',
    '/api/v1/auth/verify-otp': '10 per 30 minutes per phone',
    '/api/v1/profiles/feed':   '60 per minute per user',
    '/api/v1/interests':       '20 per minute per user',
    '/api/v1/conversations/<id>/messages': '30 per minute per user',
}
```

---

## SocketIO — JWT AUTH (Mobile Fix)

```python
# app/messaging/socket_events.py — add JWT support
@socketio.on('connect')
def on_connect(auth):
    """Support both session (web) and JWT (mobile) auth."""
    from flask_login import current_user
    
    if current_user.is_authenticated:
        # Web app — session auth
        join_room(f'user_{current_user.id}')
        return
    
    # Mobile app — JWT auth
    token = (auth or {}).get('token')
    if token:
        try:
            from flask_jwt_extended import decode_token
            data    = decode_token(token)
            user_id = data['sub']
            join_room(f'user_{user_id}')
            # Store user_id in socket session
            from flask import session as sock_session
            sock_session['jwt_user_id'] = user_id
        except Exception:
            return False  # disconnect
```

---

## OPENAPI DOCUMENTATION

```python
# requirements.txt
flask-swagger-ui==4.11.1

# In create_app() — serve Swagger UI in dev only
if env == 'development':
    from flask_swagger_ui import get_swaggerui_blueprint
    swaggerui = get_swaggerui_blueprint(
        '/api/docs',
        '/static/openapi.json',
        config={'app_name': 'iJodidar API'}
    )
    app.register_blueprint(swaggerui, url_prefix='/api/docs')
```

---

*API-First Architecture | iJodidar | June 2026*
*Implement: Month 1-2 | Required for: Mobile app*
