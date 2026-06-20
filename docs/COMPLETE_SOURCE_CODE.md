# iJodidar — Complete Source Code Reference
## v25 Auto-Kundli | June 2026
## 45 Python Files | 78 Templates | 34 Models | 5 Migrations

---

## ARCHITECTURE OVERVIEW

```
ijodidar/
├── wsgi.py                   Entry point (Gunicorn + SocketIO)
├── config.py                 Dev / Prod configs
├── seed.py                   Seed DB with cities, plans, admin
├── requirements.txt          Production dependencies
├── requirements-dev.txt      Dev-only dependencies
├── .env.example              Environment variable template
├── celery.service            Systemd service for Celery worker
│
├── app/
│   ├── __init__.py           Flask app factory, blueprints, hooks
│   ├── models.py             34 SQLAlchemy models
│   ├── utils.py              Shared utilities (email, S3, scoring)
│   ├── utils_kundli.py       Guna Milan engine (8 Ashta Koota)
│   ├── vedic_engine.py       Auto nakshatra from DOB+Time+City
│   ├── tasks.py              Celery async tasks
│   │
│   ├── auth/                 Registration, login, OTP, Aadhaar
│   ├── main/                 Landing, home feed, profile views
│   ├── profile/              22 profile edit pages, data export
│   ├── search/               15-filter search
│   ├── connect/              Interests, shortlist, block, report
│   ├── messaging/            Real-time chat (SocketIO)
│   ├── membership/           Plans, Razorpay, Spotlight, Assisted
│   ├── kundli/               Guna Milan, auto-calculate, match
│   ├── family/               Family tree management
│   ├── notifications/        Real-time alerts
│   ├── onboarding/           5-step wizard for new users
│   ├── admin/                Legacy (redirects to /console/)
│   └── console/              Staff console (RBAC, TOTP, audit)
│
├── migrations/
│   └── versions/             5 Alembic migration files
│
├── templates/                78 Jinja2 HTML templates
├── static/                   CSS, JS, PWA manifest, service worker
└── translations/             Marathi UI translations
```

---

## KEY DESIGN DECISIONS

### 1. No Separate Microservices
Single Flask monolith — correct for 0-50K users.
Celery task queue handles async without microservice complexity.

### 2. SQLite in Dev, PostgreSQL in Prod
`DATABASE_URL` empty → SQLite at `instance/dev.db`
`DATABASE_URL` set → PostgreSQL
Zero friction for local testing.

### 3. Celery for All Blocking I/O
Every external call (SES, MSG91, S3, WhatsApp) is async.
Gunicorn gevent workers return in <1ms from any external API call.

### 4. Pure-Python Vedic Engine
No ephem, pyswisseph, or external APIs.
Jean Meeus Ch47 Moon algorithm in pure Python.
±0.3° accuracy, 0.025ms per calculation, works offline.

### 5. Separate AdminUser Model
Console staff ≠ matrimony users.
`admin_users` table completely separate from `users`.
Staff cannot appear in search results, feeds, or statistics.

### 6. Signal-Boosted Matching
`user_signals` table records 7 event types.
`calculate_match_score()` includes signal boost (±10 pts) + Guna Milan (±5 pts).
No ML required — simple weighted scoring is sufficient.

---

## CORE FILE SUMMARIES

### app/__init__.py (301 lines)
- Flask app factory `create_app(env)`
- Registers 13 blueprints
- `before_request`: session_version validation + onboarding gate
- Context processors: globals, console sidebar counts, language
- Template filters: `|signed_url`, `|from_json`, `|age`, `|t` (translate)
- Error handlers: 404, 403, 500, 429
- SocketIO events registration

### app/models.py (800 lines) — 34 models
- `MembershipPlan` — plan configuration
- `UserSubscription` — active plan per user + monthly limit tracking
- `User` — auth core with lockout, session_version, DPDP fields
- `Profile` — all matrimony attributes (gender, religion, caste, etc.)
- `Interest` — send/accept/decline workflow
- `Conversation` + `Message` — chat
- `Shortlist`, `BlockList`, `UserReport` — social actions
- `KundliDetail` — birth chart + auto-calculated nakshatra
- `UserSignal` — behavioral ranking signals
- `Referral` — code + dual-reward tracking
- `AssistedRequest` + `RMContactLog` — RM workflow
- `AdminAuditLog` — immutable staff action trail
- `AdminUser` — console staff with TOTP 2FA
- 10+ supporting models (Address, Education, FamilyDetails, etc.)

### app/utils.py (667 lines)
- `send_email()` — AWS SES with config guard
- `upload_image_to_s3()` — 3-size resize, private ACL
- `get_signed_image_url()` — pre-signed URL generation
- `calculate_match_score()` — 9-factor scoring + signal boost + Guna Milan
- `get_signal_boost()` — behavioral signal scoring
- `record_signal()` — fire-and-forget signal recording
- `reward_referrer()` + `reward_referred()` — dual referral rewards
- `calculate_profile_completeness()` — profile % calculation

### app/utils_kundli.py (314 lines)
- `NAKSHATRAS` — 27 entries with corrected Nadi, Gana, Varna, Yoni
- `calculate_guna_milan()` — all 8 Ashta Koota factors
- `check_gotra_compatibility()` — Sapinda rule check
- `manglik_compatible()` — Manglik × Non-Manglik warning

### app/vedic_engine.py (425 lines)
- `compute_vedic_birth_chart()` — DOB + Time + City → all Vedic attributes
- `compute_manglik_approximate()` — Chandra Lagna proxy
- `_moon_tropical_longitude()` — Meeus Ch47 (28 periodic terms)
- `_lahiri_ayanamsa()` — standard Indian ayanamsa
- `CITY_COORDINATES` — 100+ Indian cities built-in

### app/tasks.py (309 lines)
- Celery task queue with Redis broker
- 9 async tasks: verification email, welcome email, interest notifications,
  message notifications, password reset, SMS OTP, WhatsApp
- 3 retries with exponential backoff on all tasks

### config.py
- `DevelopmentConfig` — SQLite, no CSRF, debug True
- `ProductionConfig` — HTTPS cookies, SameSite Lax, 24h session
- All secrets via `os.environ.get()` — never hardcoded

---

## ROUTE MAP (All Blueprints)

### auth/ — /login, /register, /verify/<token>, /forgot-password
### /reset-password/<token>, /logout, /send-phone-otp, /verify-phone, /verify-id

### main/ — /, /home, /my_profile, /<username>, /privacy-policy, /terms, /success-stories

### profile/ — /profile, /name, /gender, /looking_for, /birthday, /bio, /height
### /religion, /lifestyle, /email, /phone, /address/<tag>, /professional
### /education, /language, /nri, /partner-preferences, /hobbies
### /photos, /delete_image/<id>, /set_primary/<id>, /privacy, /referral
### /account/export, /account/delete

### search/ — /search

### connect/ — /interest/send/<id>, /interest/respond/<id>/<action>
### /interest/withdraw/<id>, /interests, /shortlist/toggle/<id>
### /shortlist, /block/<id>, /unblock/<id>, /report/<id>

### messaging/ — /messages, /messages/<conv_id>, /messages/<conv_id>/poll

### membership/ — /plans, /plans/create-order/<id>, /plans/verify-payment
### /webhook/razorpay, /spotlight, /spotlight/create-order
### /spotlight/verify-payment, /spotlight/buy-manual, /plans/assisted

### kundli/ — /kundli/edit, /kundli/match/<id>
### /kundli/api/calculate, /kundli/api/match, /kundli/api/cities

### family/ — /family, /family/edit, /family/delete/<id>

### notifications/ — /notifications/unread-count, /notifications/list, /notifications/mark-read

### onboarding/ — /onboarding/gender, /onboarding/basics, /onboarding/career
### /onboarding/photo, /onboarding/preferences, /onboarding/done

### admin/ — / (→/console/), /users (→/console/users), /analytics (→/console/analytics)
### (all admin routes redirect to console equivalents)

### console/ — /console/login, /console/logout, /console/totp-verify, /console/totp-setup
### /console/, /console/analytics, /console/users, /console/users/<id>
### /console/reports, /console/reports/<id>/<action>
### /console/assisted, /console/assisted/<id>/update, /console/assisted/<id>
### /console/assisted/<id>/log, /console/staff, /console/staff/add
### /console/staff/<id>/toggle

---

## LOCAL DEVELOPMENT QUICK START

```bash
# 1. Clone
git clone https://github.com/atulgadhave1007/ijodidar.git
cd ijodidar

# 2. Setup
python -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Edit .env: set SECRET_KEY to any random string

# 4. Database
export FLASK_APP=wsgi.py
flask db upgrade
python seed.py

# 5. Run
python wsgi.py
# Open http://localhost:5000
```

---

## PRODUCTION DEPLOYMENT QUICK START

```bash
# On EC2
cd ~/ijodidar && git pull origin main
source venv/bin/activate
pip install -r requirements.txt -q
export FLASK_APP=wsgi.py && flask db upgrade
sudo systemctl restart ijodidar ijodidar-celery
```

---

*Complete Source Code Reference | iJodidar v25 | June 2026*
