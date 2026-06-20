# iJodidar — Mobile App Readiness Assessment
## Android / iOS Compatibility Analysis | June 2026

---

## CURRENT STATE: NOT MOBILE-APP-READY

iJodidar is a server-rendered Flask app. Every route returns HTML.
A React Native or Flutter mobile app cannot call `/home` and get JSON data.

**What this means:** An Android/iOS app requires a REST API.
Building a mobile app without changing the backend first would require
rewriting the entire backend in parallel — exponentially more work.

---

## WHAT NEEDS TO EXIST BEFORE MOBILE APP

### 1. JWT Authentication (Not Flask Sessions)
Flask sessions are browser cookies. Mobile apps use JWT tokens.

```
Current:  POST /login → sets session cookie
Mobile:   POST /api/v1/auth/login → returns { access_token, refresh_token }
```

### 2. JSON API Endpoints
```
Current:  GET /home → returns HTML
Mobile:   GET /api/v1/profiles/feed → returns JSON array of profiles
```

### 3. Token-Based SocketIO Auth
```
Current:  SocketIO authenticates via Flask session (cookie)
Mobile:   SocketIO authenticates via JWT token in query param
          io.connect("wss://ijodidar.com", { auth: { token: jwt_token } })
```

### 4. File Upload via API
```
Current:  POST /upload_image → multipart form, Flask handles, S3 upload
Mobile:   POST /api/v1/photos → multipart/form-data with Authorization header
```

### 5. Push Notifications (FCM)
```
Current:  In-app notifications via SocketIO + email
Mobile:   Firebase Cloud Messaging (FCM) token stored on login
```

---

## CURRENT API ENDPOINTS (already exist)

| Endpoint | Method | Returns | Mobile-ready? |
|----------|--------|---------|--------------|
| `/kundli/api/calculate` | GET | JSON | ✅ Yes |
| `/kundli/api/match` | GET | JSON | ✅ Yes |
| `/kundli/api/cities` | GET | JSON | ✅ Yes |
| `/notifications/unread-count` | GET | JSON | ⚠️ Session-only |
| `/notifications/list` | GET | JSON | ⚠️ Session-only |
| `/messages/<id>/poll` | GET | JSON | ⚠️ Session-only |

All others return HTML. None work without Flask session cookie.

---

## MINIMUM API SURFACE FOR MOBILE APP v1

### Authentication

```
POST   /api/v1/auth/register     { name, phone }  → OTP sent
POST   /api/v1/auth/verify-otp   { phone, otp }   → { access_token, refresh_token, user }
POST   /api/v1/auth/login        { phone, otp }   → { access_token, refresh_token, user }
POST   /api/v1/auth/refresh      { refresh_token } → { access_token }
POST   /api/v1/auth/logout       Header: Bearer token
```

### Profiles

```
GET    /api/v1/profiles/me                    → current user's full profile
PATCH  /api/v1/profiles/me                    → update any profile fields (PATCH semantics)
GET    /api/v1/profiles/feed                  → home feed (scored, paginated)
GET    /api/v1/profiles/feed?tab=new          → new matches
GET    /api/v1/profiles/feed?tab=mutual       → mutual interests
GET    /api/v1/profiles/<username>            → view another user's profile
GET    /api/v1/profiles/completeness          → { score: 72, missing: [...] }
POST   /api/v1/profiles/photo                 → upload photo (multipart)
DELETE /api/v1/profiles/photo/<id>            → delete photo
PATCH  /api/v1/profiles/photo/<id>/primary    → set primary photo
```

### Discovery

```
GET    /api/v1/search?religion=Hindu&min_age=25&city=Pune&page=1
       → { results: [...], total: 142, page: 1, pages: 8 }
```

### Interests & Connect

```
POST   /api/v1/interests              { receiver_id }   → send interest
GET    /api/v1/interests/received     → received interests (pending)
GET    /api/v1/interests/sent         → sent interests
PATCH  /api/v1/interests/<id>         { action: accept|decline }
DELETE /api/v1/interests/<id>                           → withdraw
```

### Messaging

```
GET    /api/v1/conversations                → inbox list
GET    /api/v1/conversations/<id>/messages  → message history (paginated)
POST   /api/v1/conversations/<id>/messages  { body } → send message
PATCH  /api/v1/conversations/<id>/read      → mark as read
```

### Notifications

```
GET    /api/v1/notifications         → list (paginated)
PATCH  /api/v1/notifications/read    → mark all read
POST   /api/v1/devices               { fcm_token, platform } → register for push
```

### Kundli

```
POST   /api/v1/kundli                { birth_date, birth_time, birth_city } → auto-calc + save
GET    /api/v1/kundli/match/<id>     → Guna Milan with another user
```

### Membership

```
GET    /api/v1/plans                 → list plans
POST   /api/v1/plans/<id>/order      → create Razorpay order
POST   /api/v1/plans/verify-payment  → verify payment
```

---

## IMPLEMENTATION APPROACH

### Option A: Add API layer to existing Flask app (Recommended)
**Effort: 2-3 weeks**

Add a new blueprint `api_v1_bp` under `/api/v1/` prefix.
Use Flask-JWT-Extended for token auth.
Serialize existing SQLAlchemy models with Marshmallow schemas.
Web app (HTML routes) continues unchanged.

```python
# app/api/__init__.py
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# app/api/auth.py
@api_v1_bp.route('/auth/login', methods=['POST'])
def api_login():
    # Same logic as auth/routes.py login()
    # But returns JSON + JWT instead of HTML + session
    from flask_jwt_extended import create_access_token
    ...
    return jsonify(access_token=create_access_token(user.id),
                   refresh_token=create_refresh_token(user.id))
```

### Option B: Separate FastAPI backend
**Effort: 6-8 weeks**

Build a new FastAPI service alongside Flask.
Share the same PostgreSQL database.
Flask handles web, FastAPI handles mobile.
Better long-term but significant effort now.

**Recommendation: Option A.** Add API layer to existing Flask app.
Share models, business logic, and Celery tasks.
Mobile app talks to `/api/v1/`, web uses existing HTML routes.

---

## FCM PUSH NOTIFICATIONS

### What to add to models

```python
class UserDevice(db.Model):
    __tablename__ = 'user_devices'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fcm_token   = db.Column(db.String(255), nullable=False)
    platform    = db.Column(db.String(10))  # ios / android
    app_version = db.Column(db.String(20))
    last_seen   = db.Column(db.DateTime, default=datetime.utcnow)
```

### Push notification via Celery task

```python
@celery.task
def send_push_notification_task(user_id, title, body, data=None):
    from app.models import UserDevice
    import firebase_admin
    from firebase_admin import messaging
    
    devices = UserDevice.query.filter_by(user_id=user_id).all()
    for device in devices:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=device.fcm_token,
        )
        try:
            messaging.send(message)
        except Exception:
            pass  # stale token — remove it
```

---

## CURRENT PWA CAPABILITY

iJodidar already has:
- `static/manifest.json` — PWA manifest
- `static/sw.js` — service worker
- `PLAYSTORE_TWA_GUIDE.md` — TWA (Trusted Web Activity) guide

**PWA → Play Store via TWA** is the fastest path to Android without building a native app.
Prerequisites:
- HTTPS (already done ✅)
- manifest.json with correct icons (check)
- Service worker active (check)
- `/.well-known/assetlinks.json` pointing to SHA-256 of release keystore

**PWA Limitation:** Push notifications on iOS require native app (Safari PWA push is iOS 16.4+).
For full iOS support, React Native is required.

---

## TECHNOLOGY RECOMMENDATION FOR NATIVE APP

### React Native (Recommended for iJodidar)
- One codebase for Android + iOS
- Large community, mature ecosystem
- Razorpay, SocketIO, AWS Amplify all have React Native SDKs
- Expo (managed workflow) for rapid development

### Timeline estimate (after REST API is ready)
- Week 1-2: Auth flow + onboarding
- Week 3-4: Home feed + profile view
- Week 5-6: Interests + messaging + SocketIO
- Week 7: Kundli, membership, notifications
- Week 8: Testing + Play Store submission

### Cost
- Developer: 1 mid-level React Native developer
- Timeline: 8-10 weeks
- Play Store: ₹2,500 one-time
- Apple Developer: $99/year (~₹8,200)

---

## IMMEDIATE ACTIONS FOR MOBILE READINESS

### This Week (no code changes needed)
1. Test PWA install on Android Chrome → Add to Home Screen → verify it works
2. Check `.well-known/assetlinks.json` exists for TWA

### Month 1
3. Add `last_active_at` to User model (migration)
4. Add `UserDevice` model for FCM tokens
5. Add Flask-JWT-Extended to requirements
6. Build `POST /api/v1/auth/login` returning JWT
7. Build `GET /api/v1/profiles/feed` returning JSON

### Month 2
8. Complete REST API surface (20 endpoints)
9. Update SocketIO to accept JWT token auth
10. Begin React Native app development

---

*Mobile App Readiness | iJodidar | June 2026*
