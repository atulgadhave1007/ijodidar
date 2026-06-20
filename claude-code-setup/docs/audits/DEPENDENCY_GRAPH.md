# DEPENDENCY_GRAPH.md
## iJodidar v2 — Module Dependency Analysis
## Phase 0 | June 2026

---

## 1. EXTERNAL DEPENDENCY MAP

```
iJodidar Application
│
├── RUNTIME DEPENDENCIES
│   ├── Flask 3.1.0
│   │   ├── Werkzeug 3.1.3
│   │   ├── Flask-SQLAlchemy 3.1.1 → SQLAlchemy 2.0.36
│   │   ├── Flask-Migrate 4.1.0 → Alembic 1.16.4
│   │   ├── Flask-Login 0.6.3
│   │   ├── Flask-WTF 1.3.0 → WTForms 3.2.1
│   │   ├── Flask-Limiter 3.8.0
│   │   └── Flask-SocketIO 5.3.6
│   │
│   ├── ASYNC / QUEUE
│   │   ├── Celery 5.4.0
│   │   └── Redis 5.2.1
│   │
│   ├── AWS
│   │   ├── boto3 1.38.46
│   │   └── botocore 1.38.46
│   │
│   ├── PAYMENTS
│   │   └── razorpay 1.4.2
│   │
│   ├── SECURITY
│   │   ├── pyotp 2.9.0
│   │   └── qrcode[pil] 8.0
│   │
│   ├── MONITORING
│   │   └── sentry-sdk[flask] 2.19.2
│   │
│   ├── IMAGE
│   │   └── Pillow 11.1.0
│   │
│   └── UTILITIES
│       ├── python-dotenv 1.1.1
│       ├── email-validator 2.2.0
│       └── requests 2.32.3
│
├── PRODUCTION SERVER
│   ├── gunicorn 23.0.0
│   ├── gevent 24.11.1
│   ├── gevent-websocket 0.10.1
│   └── psycopg2-binary 2.9.10
│
└── MISSING CRITICAL DEPENDENCIES
    ├── Flask-JWT-Extended (mobile REST API)
    ├── marshmallow (API serialization)
    ├── flask-cors (mobile CORS)
    └── firebase-admin (FCM push)
```

---

## 2. INTERNAL MODULE DEPENDENCY MAP

```
app/__init__.py (APPLICATION CORE — all blueprints depend on this)
│
├── app/models.py (SHARED DEPENDENCY — imported by ALL modules)
│   └── Imports: app.db, app.login_mgr, werkzeug.security
│
├── app/utils.py (UTILITY LAYER — imported by most modules)
│   └── Imports: app.db, app.models (CIRCULAR RISK), boto3, requests
│
├── app/utils_kundli.py (KUNDLI ENGINE)
│   └── No external imports — pure calculation
│
├── app/vedic_engine.py (VEDIC ASTRONOMY ENGINE)
│   └── No external imports — pure calculation + optional urllib
│
├── app/tasks.py (CELERY TASKS)
│   └── Imports: wsgi.app (CIRCULAR), app.models, app.utils
│
└── BLUEPRINTS (each imports models + utils)
    ├── app/auth/routes.py
    │   └── Imports: app.models, app.utils, app.tasks, app.auth.forms
    ├── app/profile/routes.py
    │   └── Imports: app.models, app.utils, app.limiter
    ├── app/connect/routes.py
    │   └── Imports: app.models, app.utils, app.tasks
    ├── app/messaging/routes.py
    │   └── Imports: app.models, app.utils, app.tasks
    ├── app/messaging/socket_events.py
    │   └── Imports: app.db, app.models, app.utils
    ├── app/main/routes.py
    │   └── Imports: app.models, app.utils
    ├── app/search/routes.py
    │   └── Imports: app.models, app.utils_kundli
    ├── app/kundli/routes.py
    │   └── Imports: app.models, app.utils_kundli, app.vedic_engine
    ├── app/membership/routes.py
    │   └── Imports: app.models, app.utils, razorpay
    ├── app/console/routes.py
    │   └── Imports: app.models, app.db, app.limiter
    ├── app/onboarding/routes.py
    │   └── Imports: app.models, app.db, app.utils
    ├── app/family/routes.py
    │   └── Imports: app.models, app.db
    ├── app/notifications/routes.py
    │   └── Imports: app.models, app.db
    └── app/admin/routes.py
        └── Imports: app.models, app.db [DEPRECATED — all redirect to console]
```

---

## 3. CIRCULAR DEPENDENCY ANALYSIS

### Critical Circular Dependencies Found

| Dependency | Files Involved | Risk |
|------------|---------------|------|
| tasks.py imports wsgi.app | `app/tasks.py` → `wsgi.py` → `app/__init__.py` → `app/tasks.py` | HIGH |
| utils.py imports from models inside functions | `app/utils.py` → `app/models.py` → `app/__init__.py` (db) | LOW (deferred) |
| Models imported inside route functions | All blueprints use deferred `from app.models import X` pattern | LOW |

### Notes on tasks.py Circular Dependency

`app/tasks.py` creates standalone Celery tasks that use `from wsgi import app` to obtain an application context. This creates a dependency on the entry point (`wsgi.py`), which is not the correct pattern. The standard pattern uses `celery.Task` with a Flask app context binding. This is a technical debt item but is currently functional.

---

## 4. TIGHT COUPLING ANALYSIS

### Highly Coupled Components

| Component | Coupled To | Nature | Risk |
|-----------|-----------|--------|------|
| All blueprints | `app/models.py` | Direct model imports | Any model change breaks all routes |
| All blueprints | `app/utils.py` | Utility function imports | Refactoring utils breaks all callers |
| Home feed | `calculate_match_score()` | Score calculated synchronously | Performance bottleneck at scale |
| Guna Milan in home feed | `KundliDetail` queries | Per-candidate DB query inside scoring | N+1 risk at scale |
| SocketIO events | Session-based auth | Flask session required | Blocks mobile JWT auth |
| Celery tasks | `wsgi.py` (app context) | Non-standard context pattern | Deployment complexity |

### Loosely Coupled Components (Good)

| Component | Why Decoupled |
|-----------|--------------|
| `vedic_engine.py` | Pure Python, zero imports, standalone |
| `utils_kundli.py` | Pure calculation, no DB dependencies |
| Console blueprint | Separate AdminUser model, separate auth |
| Celery tasks | Executes asynchronously, isolated |

---

## 5. DEPENDENCY RISKS

### Risk 1 — Single models.py file (34 models, 800+ lines)
All 34 SQLAlchemy models in one file. Any syntax error brings down the entire application. Any model change requires understanding the full file.

**Migration:** Split into domain-specific model files: `models/user.py`, `models/profile.py`, `models/messaging.py`, `models/membership.py`, `models/admin.py`.

### Risk 2 — No service layer
Business logic lives directly in route handlers. The `send_interest()` route contains: authorization check, monthly limit check, duplicate check, DB insert, signal recording, email dispatch, notification creation. This cannot be unit-tested without a full Flask context.

**Migration:** Extract `InterestService`, `ProfileService`, `MatchingService` as separate classes with no Flask dependency.

### Risk 3 — No API serialization layer
Without Marshmallow schemas, adding a REST API requires duplicating all the rendering logic currently in Jinja2 templates. Every route returns HTML. There is no shared data contract.

**Migration:** Define Marshmallow schemas for all domain objects before REST API work begins.

### Risk 4 — gevent mode incompatibility with Windows
`wsgi.py` conditionally applies `monkey.patch_all()` based on `FLASK_ENV`. This works but means development and production run in different async modes. A Windows developer using SQLite cannot test gevent behavior.

### Risk 5 — Bootstrap 5 CDN dependency
All templates load Bootstrap 5.3.3 from `cdn.jsdelivr.net`. If CDN is unavailable, the entire UI breaks. No local copy, no fallback.

---

## 6. FRONTEND DEPENDENCY MAP

```
base.html (loaded on every authenticated page)
│
├── EXTERNAL (CDN — no local fallback)
│   ├── Bootstrap 5.3.3 CSS
│   ├── Bootstrap 5.3.3 JS Bundle
│   ├── Bootstrap Icons 1.11.3
│   └── Google Fonts (Inter)
│
├── INTERNAL
│   └── static/css/style.css (907 lines — all custom design tokens + components)
│
└── JAVASCRIPT (inline in base.html)
    ├── Navbar scroll elevation
    ├── Toast auto-dismiss
    ├── Notification polling (30s interval)
    └── Mark-all-read handler

Templates that load additional JS:
├── my_profile.html → Cropper.js (CDN), Chart.js (CDN)
├── upload_cropper.js → Cropper.js dependency
└── location_cascade.js → City/state cascade dropdowns
```

---

## 7. INTEGRATION DEPENDENCY RISKS

| Integration | Risk | Current Mitigation | Required Mitigation |
|-------------|------|-------------------|---------------------|
| AWS SES | Email completely disabled if not configured | Guard in send_email() | Celery task with fallback logging |
| S3 | Photo upload returns error message | Guard in upload_image_to_s3() | Graceful degradation |
| Redis | Falls back to in-memory rate limiting | Memory fallback | Redis required in production |
| Razorpay | Test keys in production = no real payments | Test-only for now | Live KYC needed |
| MSG91 | OTP logged to console, not sent | Dev-mode logging | DLT registration needed |
| Aadhaar KYC | Returns mock data without API key | Dev-mode stub | Surepass key needed |

---

CHECKPOINT_STATUS
Current Phase: 0 — Repository Discovery
Current Section: DEPENDENCY_GRAPH.md Complete
Completed: REPOSITORY_DISCOVERY.md, DEPENDENCY_GRAPH.md
Remaining: TECHNICAL_DEBT_REPORT.md, then await approval
Files Generated: 2
Progress Percent: 16%
