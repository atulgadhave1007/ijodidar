# iJodidar — Recommended Architecture
## Production-Grade Design for Indian Matrimony Platform
## June 2026

---

## CURRENT ARCHITECTURE (Accurate Diagram)

```
User Browser (HTTPS)
       │
       ▼
Route 53 → 13.205.222.218
       │
       ▼
Nginx 1.24
  ├── SSL termination (Let's Encrypt)
  ├── /console/ → IP allowlist check
  └── Proxy → Gunicorn unix socket
       │
       ▼
Gunicorn 23.0 (3 workers, gevent cooperative multitasking)
  └── Flask 3.1 app (13 blueprints, ~80 routes, returns HTML)
       │
       ├── PostgreSQL 16 (same EC2, port 5432)
       ├── Redis (same EC2, port 6379) ← rate limiting + Celery broker
       └── AWS services (SES email, S3 photos) via boto3
       
Celery Worker (separate process)
  ├── Reads jobs from Redis
  └── Executes: SES email, MSG91 SMS, S3 uploads, WhatsApp
```

**This is a correct, well-structured monolith for 0-10K users.**
No changes needed to this core for the next 12 months.

---

## WHAT SHOULD CHANGE (and when)

### Change 1: Add REST API Layer (Month 1-2)
**Why:** Mobile app is impossible without it.
**How:** New blueprint `/api/v1/` with Flask-JWT-Extended.
**Impact:** Zero change to existing HTML routes.

```
Current:  Flask → HTML routes only
Target:   Flask → HTML routes (web) + JSON API routes (mobile)
                              ↓
                         JWT tokens
                         Marshmallow schemas
                         Rate limiting per token
```

### Change 2: Phone-First Registration (Month 1)
**Why:** 40-60% of users drop at email verification step.
**How:** Make phone OTP the primary auth, email secondary.
**Impact:** Requires new `POST /api/v1/auth/phone-otp` endpoint.
Existing email-based auth stays for web.

### Change 3: Add `last_active_at` to User (Month 1)
**Why:** "Active 3 days ago" is a top engagement signal.
**How:** Simple column + update on every authenticated request.
**Impact:** Migration + one `before_request` hook.

### Change 4: Migrate to `dob` Date everywhere (Month 1)
**Why:** `date_of_birth` String causes age filter inaccuracies.
**How:** Stop writing to `date_of_birth`. All code reads `dob`.
**Impact:** Migration + search route update + profile route update.

### Change 5: Daily Match Email via Celery Beat (Month 1)
**Why:** Single highest-ROI re-engagement feature.
**How:** Add `celery.conf.beat_schedule`, run celery beat process.
**Impact:** +40% re-engagement, drives Silver upgrades.

---

## TARGET ARCHITECTURE (12 months)

```
                    ┌─────────────────────────────────────────┐
                    │         iJodidar Platform                │
                    │                                         │
  Web Browser ──→   │  Nginx                                  │
  Android App ──→   │   ├── /          → Flask (HTML)        │ ←── PostgreSQL
  iOS App ──→       │   ├── /api/v1/   → Flask (JSON+JWT)    │ ←── Redis
                    │   ├── /console/  → Flask + IP check     │ ←── S3 (photos)
                    │   └── /ws/       → SocketIO (JWT auth)  │ ←── SES (email)
                    │                                         │
                    │  Celery Worker                          │ ←── MSG91 (SMS)
                    │   ├── Email (SES)                       │ ←── FCM (push)
                    │   ├── SMS (MSG91)                       │ ←── Razorpay
                    │   ├── Push (FCM)                        │
                    │   └── Match scoring (pre-compute)       │
                    │                                         │
                    │  Celery Beat                            │
                    │   ├── Daily match emails (8 AM IST)     │
                    │   ├── Subscription expiry check (daily) │
                    │   └── Match score refresh (hourly)      │
                    └─────────────────────────────────────────┘
```

---

## DATABASE ARCHITECTURE RECOMMENDATIONS

### Tables to Add

```sql
-- 1. User devices (FCM push notifications)
CREATE TABLE user_devices (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) NOT NULL,
    fcm_token   VARCHAR(255) NOT NULL,
    platform    VARCHAR(10),        -- ios / android / web
    app_version VARCHAR(20),
    last_seen   TIMESTAMP DEFAULT NOW()
);
CREATE UNIQUE INDEX ON user_devices(user_id, fcm_token);

-- 2. Saved searches (power user feature)
CREATE TABLE saved_searches (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) NOT NULL,
    name        VARCHAR(100),
    params      JSONB NOT NULL,    -- search parameters as JSON
    last_run    TIMESTAMP,
    result_count INTEGER,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 3. Profile view deduplication
-- Current: profile_views has no daily deduplication
CREATE UNIQUE INDEX ix_profile_views_daily ON profile_views(viewer_id, viewed_id, DATE(timestamp));

-- 4. Match score cache (computed, not real-time)
-- For scale: pre-compute top matches per user, refresh hourly
CREATE TABLE match_score_cache (
    user_id     INTEGER REFERENCES users(id),
    candidate_id INTEGER REFERENCES users(id),
    score       SMALLINT,
    computed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, candidate_id)
);
CREATE INDEX ON match_score_cache(user_id, score DESC);
```

### Columns to Add

```sql
-- User
ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP;
CREATE INDEX ix_users_last_active ON users(last_active_at);

-- Profile
ALTER TABLE profiles ADD COLUMN profile_for VARCHAR(20) DEFAULT 'Self';
-- Self / Son / Daughter / Brother / Sister / Relative

-- PartnerPreference (upgrade from String income to Integer range)
ALTER TABLE partner_preferences ADD COLUMN min_income_lpa INTEGER;
ALTER TABLE partner_preferences ADD COLUMN max_income_lpa INTEGER;
ALTER TABLE partner_preferences ADD COLUMN religion_list TEXT;  -- JSON
ALTER TABLE partner_preferences ADD COLUMN city_list TEXT;      -- JSON
```

---

## MATCH SCORING ARCHITECTURE (Improved)

### Current: Real-time calculation on every home feed load
### Problem: At 5K users, 80 candidates × Python calculation = slow

### Recommended: Hybrid approach

```python
# app/tasks.py — Celery task
@celery.task
def refresh_match_scores_for_user(user_id):
    """
    Pre-compute top 100 match scores for a user.
    Run: on profile update, on partner pref change, hourly for active users.
    """
    from app.models import User, MatchScoreCache, Profile
    user = User.query.get(user_id)
    
    # Get candidates (same filter as home feed)
    candidates = (User.query.join(Profile)
                  .filter(User.id != user_id, User.is_active_acc == True)
                  .limit(200).all())
    
    scores = []
    for c in candidates:
        score = calculate_match_score(user, c)
        scores.append({'user_id': user_id, 'candidate_id': c.id, 'score': score})
    
    # Upsert to cache
    for s in scores:
        db.session.merge(MatchScoreCache(**s, computed_at=datetime.utcnow()))
    db.session.commit()

# app/main/routes.py — home feed reads from cache
def home():
    cached = (MatchScoreCache.query
              .filter_by(user_id=current_user.id)
              .order_by(MatchScoreCache.score.desc())
              .limit(24).all())
    # Fall back to real-time if cache empty
    ...
```

### When to trigger cache refresh
- User updates profile → `refresh_match_scores_for_user.delay(user.id)`
- User updates partner preferences → same
- New user registers → `refresh_match_scores_for_user.delay(new_user.id)` for all potentially matching users
- Celery Beat: hourly for users active in last 7 days

---

## API LAYER DESIGN

### Flask-JWT-Extended integration

```python
# requirements.txt additions
Flask-JWT-Extended==4.6.0
marshmallow==3.22.0
marshmallow-sqlalchemy==1.1.0

# app/__init__.py
from flask_jwt_extended import JWTManager
jwt = JWTManager()

# In create_app():
jwt.init_app(app)
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Register API blueprint
from app.api.routes import api_v1_bp
app.register_blueprint(api_v1_bp)
```

### Marshmallow Schema pattern

```python
# app/api/schemas.py
from marshmallow import Schema, fields

class ProfileSchema(Schema):
    id           = fields.Int(dump_only=True)
    username     = fields.Str()
    first_name   = fields.Str()
    age          = fields.Method('get_age')
    religion     = fields.Str(attribute='profile.religion')
    caste        = fields.Str(attribute='profile.caste')
    city         = fields.Method('get_city')
    occupation   = fields.Method('get_occupation')
    photo_url    = fields.Method('get_photo_url')
    trust_score  = fields.Method('get_trust_score')
    
    def get_age(self, obj):
        # use dob Date column
        if obj.profile and obj.profile.dob:
            from datetime import date
            today = date.today()
            dob = obj.profile.dob
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None
    
    def get_photo_url(self, obj):
        for img in obj.profile_images:
            if img.is_primary:
                from app.utils import get_signed_image_url
                return get_signed_image_url(img.card_url or img.image_url, expiry=3600)
        return None
```

---

## CELERY BEAT SCHEDULE

```python
# config.py — add to Config class
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    # Daily match emails — 8:00 AM IST = 2:30 UTC
    'daily-match-emails': {
        'task': 'app.tasks.send_daily_match_emails',
        'schedule': crontab(hour=2, minute=30),
    },
    # Subscription expiry check — midnight IST
    'subscription-expiry-check': {
        'task': 'app.tasks.check_subscription_expiry',
        'schedule': crontab(hour=18, minute=30),  # 18:30 UTC = midnight IST
    },
    # Refresh match scores for active users — every 2 hours
    'refresh-match-scores': {
        'task': 'app.tasks.refresh_active_user_scores',
        'schedule': crontab(minute=0, hour='*/2'),
    },
    # Clean expired OTPs — every 30 min
    'clean-expired-otps': {
        'task': 'app.tasks.clean_expired_otps',
        'schedule': 30 * 60,  # seconds
    },
}
```

### New Celery tasks needed

```python
# app/tasks.py additions

@celery.task
def send_daily_match_emails():
    """Send 5 curated match suggestions to active users who haven't logged in today."""
    from wsgi import app
    with app.app_context():
        from app.models import User
        from datetime import datetime, timedelta
        
        # Active in last 30 days, haven't logged in today
        cutoff = datetime.utcnow() - timedelta(days=30)
        today  = datetime.utcnow().date()
        users  = User.query.filter(
            User.is_verified == True,
            User.is_active_acc == True,
            User.last_active_at >= cutoff,
            db.func.date(User.last_active_at) < today,
        ).limit(1000).all()
        
        for user in users:
            send_match_digest_email_task.delay(user.id)


@celery.task
def check_subscription_expiry():
    """Expire subscriptions past their expiry date."""
    from wsgi import app
    with app.app_context():
        from app.models import UserSubscription
        from datetime import datetime
        
        expired = UserSubscription.query.filter(
            UserSubscription.is_active == True,
            UserSubscription.expires_at <= datetime.utcnow(),
            UserSubscription.expires_at != None,
        ).all()
        
        for sub in expired:
            sub.is_active = False
        db.session.commit()
```

---

## SECURITY ARCHITECTURE (No Changes Needed)

Current security is well-implemented:
- bcrypt password hashing ✅
- Account lockout ✅
- TOTP 2FA for console ✅
- OTP hashed before storage ✅
- Session invalidation on password change ✅
- CSRF protection ✅
- Rate limiting (Redis) ✅
- S3 private photos + signed URLs ✅
- Admin audit log ✅

Only addition needed for API: JWT token revocation list in Redis.

---

## INFRASTRUCTURE SCALING PLAN

### Current (0-2K users): Single EC2 + PostgreSQL on same instance
**Cost: ~₹957/month. No changes needed.**

### Phase 2 (2K-10K users): Separate PostgreSQL to RDS
**When to migrate:** Monthly revenue > ₹15,000 OR 500+ active users
```
EC2 t3.small (app + Celery) ~₹700/month
RDS t3.micro PostgreSQL     ~₹1,400/month
Redis (same EC2)            ₹0
TOTAL: ~₹2,100/month
```

### Phase 3 (10K-50K users): Add read replica + CDN
```
EC2 t3.medium (app)         ~₹1,400/month
EC2 t3.small (Celery)       ~₹700/month
RDS t3.small (write)        ~₹2,800/month
RDS t3.micro (read replica) ~₹2,800/month
ElastiCache t3.micro        ~₹1,400/month
CloudFront                  ~₹500/month
TOTAL: ~₹9,600/month
```

### Phase 4 (50K+ users): Load balancer + horizontal scaling
- Multiple app EC2 instances behind ALB
- SocketIO needs Redis adapter (flask-socketio + Redis pub/sub)
- Match scoring pre-computed and cached in Redis
- Consider: Extract messaging as a separate service

---

*Recommended Architecture | iJodidar | June 2026*
*Review: Every 6 months or at 5× user growth*
