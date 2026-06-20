# REPOSITORY_DISCOVERY.md
## iJodidar v2 — Complete Repository Discovery
## Phase 0 | Enterprise Transformation Audit | June 2026

---

## EXECUTIVE SUMMARY

iJodidar is a Flask monolith with 13 registered blueprints, 34 SQLAlchemy models, 5 Alembic migrations, 45 Python files, 78 HTML templates, and 1 CSS file. The repository exists in two states simultaneously — a root-level working copy (`/`) and a nested duplicate (`/ijodidar/`) — representing an unresolved structural artifact from development history. This duplication is the first critical finding and must be resolved before any v2 migration begins.

---

## 1. INFRASTRUCTURE FILES

### Verified Present

| File | Location | Purpose | Status |
|------|----------|---------|--------|
| `requirements.txt` | Root | Production Python dependencies | Present |
| `requirements-dev.txt` | Root | Development extras | Present |
| `requirements-windows.txt` | Root | Windows-compatible deps (no gevent) | Present |
| `config.py` | Root | Flask configuration (Dev/Prod) | Present |
| `wsgi.py` | Root | Gunicorn/SocketIO entry point | Present |
| `seed.py` | Root | Database seed script | Present |
| `Procfile` | Root | Process declaration (Heroku-style) | Present |
| `celery.service` | Root | systemd Celery worker definition | Present |
| `.env.example` | Root | Environment variable template | Present |
| `static/manifest.json` | Root | PWA manifest | Present |
| `static/sw.js` | Root | Service worker | Present |
| `static/robots.txt` | Root | Search engine directives | Present |

### Verified Missing

| Missing File | Business Impact | Severity |
|-------------|-----------------|----------|
| `Dockerfile` | Cannot containerise — no Docker deployment path | HIGH |
| `docker-compose.yml` | No local container orchestration | MEDIUM |
| `nginx.conf` | Nginx configuration not in version control | HIGH |
| `gunicorn.conf.py` | Gunicorn configuration not version-controlled | MEDIUM |
| `.github/workflows/deploy.yml` | No CI/CD automation | HIGH |
| `pytest.ini` or `pyproject.toml` | No test framework configuration | CRITICAL |
| `tests/` directory | No test suite exists | CRITICAL |
| `.gitignore` | Not confirmed in scan | MEDIUM |
| `CHANGELOG.md` | No change history | LOW |

---

## 2. FLASK ARCHITECTURE

### Application Factory

- **Pattern:** Application Factory (`create_app(env)`) — Correct pattern
- **Location:** `app/__init__.py`
- **Environment handling:** `FLASK_ENV` → selects `DevelopmentConfig` or `ProductionConfig`
- **Extensions initialised:** SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF/CSRF, Flask-Limiter, Flask-SocketIO, Sentry

### Blueprints — 13 Registered

| Blueprint | Prefix | Primary Responsibility |
|-----------|--------|----------------------|
| `auth_bp` | (root) | Login, Register, OTP, Password Reset |
| `profile_bp` | (root) | 22 profile editing routes |
| `family_bp` | (root) | Family tree management |
| `search_bp` | (root) | 15-filter profile search |
| `main_bp` | (root) | Landing, home feed, profile view |
| `connect_bp` | (root) | Interests, shortlist, block, report |
| `messaging_bp` | (root) | SocketIO chat, WebRTC calls |
| `membership_bp` | (root) | Plans, Razorpay, Spotlight, Assisted |
| `admin_bp` | `/admin` | Deprecated — redirects to console |
| `notifications_bp` | (root) | Notification count, list, mark-read |
| `kundli_bp` | (root) | Guna Milan + Vedic auto-calculation |
| `console_bp` | `/console` | Staff admin console (RBAC, TOTP) |
| `onboarding_bp` | `/onboarding` | 5-step new user onboarding wizard |

### Middleware and Before-Request Hooks

| Hook | Function | Registration |
|------|----------|-------------|
| Session version validation | `validate_session_version()` | before_request |
| Onboarding enforcement | `enforce_onboarding()` | before_request |
| Last active update | **MISSING** | Not implemented |
| ProxyFix | `werkzeug.ProxyFix` | wsgi.py |

### Extension Configuration

| Extension | Version | Configuration | Notes |
|-----------|---------|---------------|-------|
| Flask-SQLAlchemy | 3.1.1 | pool_size=10, max_overflow=20 | Correct |
| Flask-Migrate | 4.1.0 | Standard | Correct |
| Flask-Login | 0.6.3 | login_view='auth.login' | Correct |
| Flask-WTF/CSRF | 1.3.0 | Disabled in dev | Acceptable |
| Flask-Limiter | 3.8.0 | Redis storage (with memory fallback) | Risk: fallback |
| Flask-SocketIO | 5.3.6 | gevent (prod) / threading (dev) | Correct |
| Sentry | 2.19.2 | traces_sample_rate=0.1, PII=False | Correct |

### Missing Extensions / Patterns

| Missing | Needed For | Priority |
|---------|------------|---------|
| Flask-JWT-Extended | REST API for mobile app | CRITICAL |
| Marshmallow | API serialization | CRITICAL |
| Flask-CORS | Mobile API cross-origin | HIGH |
| Service layer | Business logic separation | HIGH |
| Repository pattern | DB query abstraction | MEDIUM |
| Interface/contract definitions | Testability | MEDIUM |

---

## 3. DATABASE

### SQLAlchemy Models — 34 Models

| # | Model | Table | Purpose |
|---|-------|-------|---------|
| 1 | MembershipPlan | membership_plans | Plan config |
| 2 | UserSubscription | user_subscriptions | Active plans + monthly limits |
| 3 | User | users | Core auth + account state |
| 4 | Profile | profiles | All matrimony attributes (40+ fields) |
| 5 | Interest | interests | Send/accept/decline connect requests |
| 6 | Conversation | conversations | Chat thread per pair |
| 7 | Message | messages | Chat messages |
| 8 | Shortlist | shortlists | Saved profiles |
| 9 | Country | countries | Reference data |
| 10 | State | states | Reference data |
| 11 | City | cities | Reference data |
| 12 | Address | addresses | User address (current/native/work) |
| 13 | Education | educations | Degree history |
| 14 | ProfessionalDetails | professional_details | Career + income |
| 15 | RelationCategory | relation_categories | Family relation groups |
| 16 | RelationType | relation_types | Specific relation types |
| 17 | FamilyDetails | family_details | Family member records |
| 18 | FamilyRelation | family_relations | Member-to-type mapping |
| 19 | PhoneAlternate | phone_alternates | Extra phones |
| 20 | ProfileImage | profile_images | S3 photo references |
| 21 | Language | languages | Languages spoken |
| 22 | ProfileView | profile_views | View tracking |
| 23 | PartnerPreference | partner_preferences | Match criteria |
| 24 | BlockList | block_list | Blocked users |
| 25 | UserReport | user_reports | Abuse reports |
| 26 | KundliDetail | kundli_details | Birth chart data |
| 27 | Notification | notifications | In-app alerts |
| 28 | SuccessStory | success_stories | Published couples |
| 29 | UserSignal | user_signals | Behavioral ranking |
| 30 | Referral | referrals | Referral codes + rewards |
| 31 | AssistedRequest | assisted_requests | RM plan requests |
| 32 | RMContactLog | rm_contact_logs | RM interaction history |
| 33 | AdminAuditLog | admin_audit_logs | Immutable staff action trail |
| 34 | AdminUser | admin_users | Console staff accounts (TOTP, RBAC) |

### Known Data Type Issues

| Field | Current Type | Required Type | Risk |
|-------|-------------|--------------|------|
| `Profile.date_of_birth` | String(15) | Date (migrated to `dob`) | Age filter accuracy |
| `PartnerPreference.min_income` | String | Integer | Income filter broken |
| `PartnerPreference.religion` | String(50) | JSON Array | Single-value limitation |
| `PartnerPreference.location_preference` | String(100) | JSON Array | Single-location limitation |
| `Profile.hobbies` | Text (JSON string) | JSONB or separate table | Unindexed |

### Alembic Migrations — 5 Versions

| Version | Description | Status |
|---------|-------------|--------|
| 258790d00566 | Initial schema — all 34 tables | Base |
| a1b2c3d4e5f6 | Phase 17 security fixes — lockout, indexes | Applied |
| b2c3d4e5f6a7 | Phase 1 Strategic — session_version | Applied |
| c3d4e5f6a7b8 | Phase 2 Strategic — dob Date, income_lpa, audit_logs | Applied |
| d4e5f6a7b8c9 | Phase 3 Strategic — user_signals, rm_contact_logs, TOTP | Applied |

---

## 4. FRONTEND ARCHITECTURE

### Templates — 78 HTML Files

| Directory | Count | Purpose |
|-----------|-------|---------|
| `templates/auth/` | 6 | Login, register, verify, reset |
| `templates/console/` | 11 | Staff admin console |
| `templates/admin/` | 7 | Deprecated admin (pre-console) |
| `templates/profile/` | 21 | 22 separate profile edit pages |
| `templates/main/` | 7 | Landing, home, profile view, legal |
| `templates/messaging/` | 3 | Inbox, conversation, video call |
| `templates/membership/` | 4 | Plans, checkout, spotlight, assisted |
| `templates/connect/` | 2 | Interests, shortlist |
| `templates/onboarding/` | 7 | 5-step onboarding wizard |
| `templates/kundli/` | 2 | Guna Milan edit, match report |
| `templates/family/` | 2 | Family tree view, form |
| `templates/search/` | 1 | Search results |
| `templates/errors/` | 4 | 403, 404, 429, 500 |
| `base.html` | 1 | Shared layout — navbar, footer, scripts |

### Static Assets

| File | Purpose | Size |
|------|---------|------|
| `static/css/style.css` | Entire design system | 907 lines |
| `static/js/location_cascade.js` | City/state cascade | Present |
| `static/js/upload_cropper.js` | Photo cropping | Present |
| `static/manifest.json` | PWA manifest | Present |
| `static/sw.js` | Service worker | Present |
| `static/robots.txt` | SEO directives | Present |

**Finding:** No static icons directory confirmed. PWA requires 192px and 512px maskable icons. These may be missing.

---

## 5. INTEGRATIONS

### Verified Integrations

| Integration | Library | Version | Status |
|-------------|---------|---------|--------|
| AWS S3 | boto3 | 1.38.46 | Configured — requires IAM role |
| AWS SES | boto3 | 1.38.46 | Requires production approval |
| Redis | redis-py | 5.2.1 | Rate limiting + Celery broker |
| Celery | celery | 5.4.0 | 9 async tasks defined |
| Flask-SocketIO | flask-socketio | 5.3.6 | Real-time chat + WebRTC |
| Razorpay | razorpay | 1.4.2 | Test keys only |
| MSG91 | requests | — | Dev mode (OTP logged) |
| Sentry | sentry-sdk | 2.19.2 | Configured with Flask/SQLAlchemy/Redis |
| TOTP | pyotp | 2.9.0 | Console 2FA |
| QR Code | qrcode | 8.0 | TOTP setup |
| Pillow | Pillow | 11.1.0 | Image resize before S3 |

### Missing Integrations (Identified as Needed)

| Integration | Purpose | Priority |
|-------------|---------|---------|
| Firebase/FCM | Mobile push notifications | CRITICAL for mobile app |
| Flask-JWT-Extended | JWT tokens for REST API | CRITICAL for mobile app |
| Marshmallow | API serialization schemas | CRITICAL for REST API |
| Surepass / Signzy | Aadhaar KYC automation | HIGH |
| AuthBridge | Background verification | MEDIUM |
| Celery Beat | Scheduled tasks (daily digest) | HIGH |

---

## 6. DUPLICATE REPOSITORY STRUCTURE

**Critical Finding:** The repository contains a `/ijodidar/` subdirectory that mirrors the root structure. This nested copy appears to be an older version without the v2 additions:

| Difference | Root (`/`) | Nested (`/ijodidar/`) |
|------------|-----------|----------------------|
| Migrations | 5 versions | 1 version (initial only) |
| Onboarding templates | Present | Absent |
| Console templates | 11 files | 9 files (missing totp, assisted_detail) |
| `app/tasks.py` | Present | Absent |
| `app/vedic_engine.py` | Present | Absent |
| `app/onboarding/` | Present | Absent |
| `main/privacy_policy.html` | Present | Absent |
| `main/terms.html` | Present | Absent |

**Recommendation:** The `/ijodidar/` subdirectory must be deleted before v2 development begins. It will cause confusion in any deployment pipeline.

---

## 7. ENVIRONMENT CONFIGURATION

### Required Environment Variables

| Variable | Purpose | Current State |
|----------|---------|--------------|
| `SECRET_KEY` | Flask session encryption | Validated at startup |
| `DATABASE_URL` | PostgreSQL connection | Falls back to SQLite |
| `AWS_REGION` | SES + S3 region | Empty = disabled |
| `MAIL_FROM` | SES sender address | Empty = email disabled |
| `AWS_S3_BUCKET` | S3 bucket name | Default: ijodidar-images |
| `REDIS_URL` | Redis connection | Default: localhost:6379 |
| `RAZORPAY_KEY_ID` | Payment processing | Test key only |
| `RAZORPAY_KEY_SECRET` | Payment processing | Test key only |
| `RAZORPAY_WEBHOOK_SECRET` | Webhook validation | Not set |
| `MSG91_AUTH_KEY` | SMS OTP | Not set |
| `SENTRY_DSN` | Error monitoring | Not set |
| `CONSOLE_ALLOWED_IPS` | Admin IP restriction | Hardcoded elsewhere |
| `CONSOLE_CEO_EMAIL` | Initial admin account | Set in seed |
| `CONSOLE_CEO_PASSWORD` | Initial admin password | Set in seed |
| `KYC_API_KEY` | Aadhaar verification | Not set |
| `WHATSAPP_TOKEN` | WhatsApp Business | Not set |

---

CHECKPOINT_STATUS
Current Phase: 0 — Repository Discovery
Current Section: Complete
Completed: REPOSITORY_DISCOVERY.md
Remaining: DEPENDENCY_GRAPH.md, TECHNICAL_DEBT_REPORT.md, then await approval
Files Generated: 1
Progress Percent: 10%
