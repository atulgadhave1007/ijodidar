# SYSTEM_ARCHITECTURE.md
## iJodidar v2 — System Architecture
## Target State | June 2026

---

## ARCHITECTURE PHILOSOPHY

iJodidar uses a **Flask monolith with domain-layered blueprints**.
This is the correct architecture for 0-50K users. Microservices at this scale
add operational complexity without proportional benefit. The monolith is
enhanced with async task offloading (Celery), real-time messaging (SocketIO),
and a parallel API layer (REST/JWT) for mobile.

---

## CURRENT SYSTEM DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│  USER TIER                                                       │
│  Web Browser ──→ HTTPS ──→ ijodidar.com (Route 53 → EC2)       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  EDGE TIER                                                       │
│  Nginx 1.24                                                      │
│  ├── SSL termination (Let's Encrypt, auto-renew)                 │
│  ├── /console/ → IP allowlist check → proxy                      │
│  ├── /static/  → serve directly (no Flask overhead)             │
│  └── All other → Gunicorn unix socket                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  APPLICATION TIER                                                │
│  Gunicorn 23.0 (3 workers, gevent async mode)                   │
│  └── Flask 3.1 Application                                       │
│      ├── 13 Blueprints (~80 HTML routes + 6 JSON routes)        │
│      ├── Flask-SQLAlchemy ORM                                    │
│      ├── Flask-Login (session auth)                              │
│      ├── Flask-WTF (CSRF)                                        │
│      ├── Flask-Limiter (rate limiting → Redis)                   │
│      └── Flask-SocketIO (gevent async)                           │
└──────────────┬───────────────┬──────────────────────────────────┘
               │               │
    ┌──────────▼───┐    ┌──────▼──────────────────────────────┐
    │  DATA TIER   │    │  EXTERNAL SERVICES                   │
    │              │    │  ├── AWS SES (email)                 │
    │  PostgreSQL  │    │  ├── AWS S3 (photos, private ACL)   │
    │  16 (same EC2│    │  ├── Razorpay (payments)            │
    │  port 5432)  │    │  ├── MSG91 (SMS OTP)                │
    │              │    │  ├── Sentry (error monitoring)       │
    │  Redis       │    │  └── WhatsApp Business (future)      │
    │  (same EC2   │    └──────────────────────────────────────┘
    │  port 6379)  │
    └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  WORKER TIER                                                     │
│  Celery Worker (separate process, same EC2)                      │
│  ├── Queue: default (email, SMS, WhatsApp tasks)                │
│  ├── Redis DB 1 as broker                                        │
│  └── 9 on-demand tasks                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## TARGET SYSTEM DIAGRAM (v2)

```
┌─────────────────────────────────────────────────────────────────┐
│  USER TIER                                                       │
│  Web Browser ──────→ HTTPS → ijodidar.com                      │
│  Android App ──────→ HTTPS → api.ijodidar.com (same EC2)       │
│  iOS App ──────────→ HTTPS → api.ijodidar.com                  │
└──────────────┬──────────────────┬──────────────────────────────┘
               │                  │
┌──────────────▼──────────────────▼──────────────────────────────┐
│  EDGE TIER                                                       │
│  Nginx 1.24                                                      │
│  ├── /           → Flask HTML routes (sessions)                  │
│  ├── /api/v1/    → Flask JSON routes (JWT Bearer token)         │
│  ├── /ws/        → SocketIO (session OR JWT)                    │
│  ├── /console/   → IP allowlist → Flask                        │
│  └── /static/    → Nginx direct serve                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  APPLICATION TIER                                                │
│  Gunicorn (3-5 workers, gevent)                                  │
│  └── Flask 3.1                                                   │
│      ├── 13 HTML blueprints (unchanged web app)                  │
│      ├── app/api/ blueprint (NEW — /api/v1/ prefix)             │
│      │   ├── JWT authentication (Flask-JWT-Extended)             │
│      │   ├── Marshmallow serialization schemas                   │
│      │   └── ~35 REST endpoints                                  │
│      └── Flask-SocketIO (session + JWT dual auth)               │
└──────────────┬───────────────┬──────────────────────────────────┘
               │               │
    ┌──────────▼───┐    ┌──────▼──────────────────────────────┐
    │  DATA TIER   │    │  EXTERNAL SERVICES                   │
    │              │    │  ├── AWS SES (email, async)          │
    │  PostgreSQL  │    │  ├── AWS S3 (photos, private)        │
    │  16 → RDS    │    │  ├── CloudFront (CDN for S3)         │
    │  (Phase 2)   │    │  ├── Razorpay (payments)             │
    │              │    │  ├── MSG91 (SMS OTP, live)           │
    │  Redis       │    │  ├── Firebase FCM (push, mobile)     │
    │  DB 0: rates │    │  ├── Sentry (errors + perf)          │
    │  DB 1: celery│    │  ├── Surepass (Aadhaar KYC)         │
    │  DB 2: cache │    │  └── WhatsApp Business API          │
    │  DB 3: scores│    └──────────────────────────────────────┘
    │  DB 4: jwt   │
    └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  WORKER TIER (expanded)                                          │
│  Celery Worker — on-demand tasks                                 │
│  Celery Beat — scheduled tasks (5 schedules)                    │
│  ├── Daily match digest (8:00 AM IST)                           │
│  ├── Subscription expiry check (00:30 IST)                      │
│  ├── Monthly interest reset (1st of month)                      │
│  ├── OTP cleanup (every 30 minutes)                             │
│  └── Match score refresh (hourly, Sprint 4)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## BLUEPRINT ARCHITECTURE

### Current Blueprints (13)

| Blueprint | Prefix | Status |
|-----------|--------|--------|
| auth_bp | (root) | KEEP |
| main_bp | (root) | KEEP |
| profile_bp | (root) | MODIFY |
| search_bp | (root) | MODIFY |
| connect_bp | (root) | KEEP |
| messaging_bp | (root) | MODIFY |
| membership_bp | (root) | KEEP |
| family_bp | (root) | KEEP |
| kundli_bp | (root) | KEEP |
| notifications_bp | (root) | KEEP |
| onboarding_bp | /onboarding | MODIFY |
| console_bp | /console | KEEP |
| admin_bp | /admin | REMOVE |

### Target Blueprints (14)

Same as current minus admin, plus api_v1.

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| api_v1_bp | /api/v1 | NEW — all mobile REST endpoints, JWT auth |

---

## APPLICATION LAYERS

### Current (Flat)

```
HTTP Request → Blueprint Route → Model Query → Jinja2 Template → HTTP Response
```

### Target (Layered)

```
HTTP Request
    ↓
Blueprint Route (thin — input validation only)
    ↓
Service Function (business logic — testable without Flask context)
    ↓
Model / Repository (DB queries via SQLAlchemy)
    ↓
Serializer (Marshmallow for API) / Template (Jinja2 for web)
    ↓
HTTP Response
```

Service layer introduced in Sprint 3. Priority: `InterestService`, `ProfileService`, `MatchService`.

---

## PERFORMANCE CHARACTERISTICS

| Operation | Current | Target |
|-----------|---------|--------|
| Home feed load | 80 candidates × score × Guna Milan query = ~400ms at 100 users | Score cached → <50ms |
| Profile view | ~80ms (joinedload) | ~50ms |
| Search (no income filter) | ~200ms | ~150ms (with index on income_lpa) |
| Send message (SocketIO) | ~300ms (sync email in handler) | ~10ms (async task) |
| OTP verification | ~50ms | ~50ms |
| Kundli calculation | ~1ms (pure Python) | ~1ms |
| Photo upload | S3 network time | S3 network time (CloudFront read in Phase 3) |

---

*SYSTEM_ARCHITECTURE.md | iJodidar v2 | June 2026*
