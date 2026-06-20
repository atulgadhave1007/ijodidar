# TECHNICAL_DEBT_REPORT.md
## iJodidar v2 — Technical Debt Classification
## Phase 0 | June 2026

---

## SUMMARY SCORECARD

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 6 | Blocks v2 development or mobile app launch |
| HIGH | 9 | Must resolve before production scale |
| MEDIUM | 11 | Should resolve in first 3 sprints |
| LOW | 8 | Resolve when opportunity allows |
| **TOTAL** | **34** | |

---

## CRITICAL DEBT ITEMS

### TD-C01 — No Test Suite
**Severity:** CRITICAL
**Location:** Entire repository
**Finding:** Zero test files exist. No pytest configuration. No unit tests, integration tests, or API tests anywhere in the repository.
**Impact:** Every change carries unknown regression risk. Cannot safely refactor models, routes, or utilities. Cannot validate Guna Milan calculation correctness programmatically. No confidence in deployment.
**Migration Effort:** XL — requires test strategy definition, test fixtures, and writing tests for all critical paths.
**Priority:** P0 — Required before v2 development begins.

### TD-C02 — No REST API Layer
**Severity:** CRITICAL
**Location:** All blueprints return HTML only
**Finding:** The platform has no JSON API endpoints except 4 Kundli utility routes. Every route returns HTML via Jinja2 templates. The planned React Native mobile app cannot function without a REST API. Flask-JWT-Extended, Marshmallow, and Flask-CORS are absent from requirements.
**Impact:** Android/iOS app development is completely blocked.
**Migration Effort:** L — 2-3 weeks to build minimum viable API surface.
**Priority:** P0

### TD-C03 — Duplicate Repository Structure
**Severity:** CRITICAL
**Location:** `/ijodidar/` subdirectory
**Finding:** A nested `/ijodidar/` directory contains an older version of the codebase (1 migration, no tasks.py, no vedic_engine.py, no onboarding module). This will cause confusion in any deployment pipeline, CI/CD, or Docker build.
**Impact:** Deploy scripts targeting wrong directory. Developers unsure which version to edit.
**Migration Effort:** S — Delete `/ijodidar/` directory.
**Priority:** P0 — Do before any other work.

### TD-C04 — No Celery Beat (No Scheduled Tasks)
**Severity:** CRITICAL
**Location:** `app/tasks.py`, `celery.service`
**Finding:** Celery worker is configured for on-demand tasks only. No Celery Beat process exists. The following scheduled tasks are completely absent: daily match email digest, subscription expiry check, match score pre-computation, OTP cleanup, and stale data removal. Daily match emails are the single highest-ROI re-engagement feature on matrimony platforms.
**Impact:** No automated user re-engagement. No subscription expiry enforcement.
**Migration Effort:** M — 1 week to implement beat schedule + 4 task implementations.
**Priority:** P0

### TD-C05 — tasks.py Circular App Context Pattern
**Severity:** CRITICAL
**Location:** `app/tasks.py`
**Finding:** Every Celery task uses `from wsgi import app` and `with app.app_context()` inside the task body. This creates a circular import through `wsgi.py` → `app/__init__.py` → `app/tasks.py`. The correct pattern is to bind the Flask app at Celery initialisation time using the `ContextTask` pattern, with the Flask app created in a Celery worker startup hook.
**Impact:** If wsgi.py is renamed or restructured, all 9 tasks break. Deployment is fragile.
**Migration Effort:** M — 1-2 days to restructure task initialization.
**Priority:** P1

### TD-C06 — Single-File Models (34 Models, 800+ Lines)
**Severity:** CRITICAL
**Location:** `app/models.py`
**Finding:** All 34 SQLAlchemy models live in a single file. This creates maximum coupling between unrelated domains. A change to the User model requires understanding its proximity to RMContactLog. A syntax error anywhere in the file breaks the entire application.
**Impact:** Refactoring is dangerous. Code review is difficult. Module boundaries are invisible.
**Migration Effort:** M — 2-3 days to split into domain model files.
**Priority:** P1

---

## HIGH DEBT ITEMS

### TD-H01 — Profile Editing: 22 Separate Routes
**Severity:** HIGH
**Location:** `app/profile/routes.py` (22 GET/POST route pairs)
**Finding:** Each profile field (name, birthday, bio, height, religion, etc.) is a separate Flask route with its own template. Completing a full profile requires 22 full-page HTTP round-trips. Industry abandoned this pattern in 2016.
**Impact:** Profile completion rates are critically low. Mobile experience is unusable.
**Migration Effort:** L — 1 week to consolidate into AJAX section-based editor.
**Priority:** P1

### TD-H02 — No Service Layer
**Severity:** HIGH
**Location:** All route files
**Finding:** Business logic — authorization, validation, DB writes, email dispatch, signal recording — all live directly in route handler functions. `send_interest()` in `connect/routes.py` contains 9 distinct business logic steps in one function. Cannot be unit tested without a Flask request context.
**Impact:** Cannot test business logic. Cannot reuse logic in API routes. Technical debt compounds with every feature.
**Migration Effort:** XL — Architectural refactor across all blueprints.
**Priority:** P1

### TD-H03 — Profile.date_of_birth: Dual Column Technical Debt
**Severity:** HIGH
**Location:** `app/models.py` — Profile model
**Finding:** Two columns exist for the same data: `date_of_birth` (String, legacy) and `dob` (Date, new). Code writes to both in some places, only one in others. Template filters handle both formats. Age range search uses the String column for comparison, which is unreliable.
**Impact:** Age filter inaccuracy. Code complexity. Maintenance burden.
**Migration Effort:** M — 1 week data migration + code cleanup.
**Priority:** P1

### TD-H04 — PartnerPreference Single-Value Fields
**Severity:** HIGH
**Location:** `app/models.py` — PartnerPreference model
**Finding:** `pref.religion` is a single String(50). A user who would accept Hindu, Jain, or Buddhist partners can only express one preference. Same issue with `min_income` (String instead of Integer) and `location_preference` (single city string).
**Impact:** Match quality is degraded. Income filtering is broken because String comparison fails.
**Migration Effort:** M — 2 days model migration + search route update.
**Priority:** P1

### TD-H05 — No Mobile Filter Panel
**Severity:** HIGH
**Location:** `templates/search/search_results.html`
**Finding:** The search filter sidebar is `d-none d-lg-block`. On any screen smaller than 1024px, users see search results with zero ability to apply filters. Given 73% mobile traffic on Indian matrimony platforms, this is a critical UX failure.
**Impact:** Mobile search is unusable.
**Migration Effort:** M — 3-4 days to implement filter bottom sheet.
**Priority:** P1

### TD-H06 — No Completeness Ring in Navigation
**Severity:** HIGH
**Location:** `templates/base.html`
**Finding:** Profile completeness is calculated via `calculate_profile_completeness()` but is only shown on the `/profile` settings page. It is not visible in the navbar, home feed sidebar, or anywhere persistent. Users have no persistent awareness of what to complete.
**Impact:** Low profile completion rates. Missing engagement driver.
**Migration Effort:** S — 2 hours template change.
**Priority:** P1

### TD-H07 — Context Processor Makes DB Query on Every Request
**Severity:** HIGH
**Location:** `app/__init__.py` — `inject_globals()`
**Finding:** The global context processor executes 3 DB queries (unread messages count, pending interests count, unread notifications count) on every single authenticated request, regardless of whether the template needs these values. At 100 concurrent users this is 300 extra queries per second.
**Impact:** Performance degradation at scale. Database pressure increases linearly with traffic.
**Migration Effort:** M — Replace with Redis caching (invalidate on change).
**Priority:** P1

### TD-H08 — Bootstrap CDN Dependency
**Severity:** HIGH
**Location:** `templates/base.html`
**Finding:** Bootstrap CSS, Bootstrap JS, Bootstrap Icons, and Google Fonts all load from external CDNs with no local fallback. If any CDN is slow or unavailable, the entire UI degrades.
**Impact:** UI failure on CDN outages. Performance variability.
**Migration Effort:** S — Bundle and serve locally.
**Priority:** P2

### TD-H09 — admin Blueprint: Deprecated But Not Removed
**Severity:** HIGH
**Location:** `app/admin/routes.py`
**Finding:** The `/admin/` blueprint still has 14 routes, each redirecting to `/console/` equivalents. The templates in `templates/admin/` are also still present (7 files). This is dead code maintained alongside the console blueprint.
**Impact:** Confusion. Security surface area. Dead template maintenance.
**Migration Effort:** S — Remove admin blueprint and templates.
**Priority:** P2

---

## MEDIUM DEBT ITEMS

### TD-M01 — No `last_active_at` on User
All competitor platforms show "Active 3 days ago." This column is missing entirely.

### TD-M02 — No UserDevice Model for FCM Push
FCM push notifications require a `user_devices` table to store FCM tokens. Missing.

### TD-M03 — Profile completeness calculated dynamically
`calculate_profile_completeness()` in utils.py computes completeness fresh on every call via Python logic. Should be cached in `profiles.completeness_pct` and invalidated on save.

### TD-M04 — Message soft-delete missing
Users cannot delete their side of a conversation. No `deleted_for_user1`, `deleted_for_user2` columns on Message model.

### TD-M05 — ProfileView has no daily deduplication at DB level
Multiple profile views per viewer per day are stored. Only deduplicated in Python. Race condition possible.

### TD-M06 — Interest monthly reset uses app-level timer
`UserSubscription.interests_remaining()` calls `db.session.commit()` directly inside a model property — a violation of the separation of concerns. Properties should be read-only.

### TD-M07 — Onboarding gate exemption list is hardcoded strings
The `ONBOARDING_EXEMPT` set in `app/__init__.py` contains hardcoded endpoint strings. If any blueprint or function is renamed, the exemption silently breaks.

### TD-M08 — CSS design system has Bootstrap overrides mixed with custom styles
`style.css` contains both the iJodidar design system and Bootstrap overrides in the same file. No clear separation. Upgrading Bootstrap requires careful review of the entire 907-line file.

### TD-M09 — SocketIO authentication is session-only
Mobile app cannot use SocketIO because it requires Flask session cookies. No JWT token authentication path in socket_events.py.

### TD-M10 — Spotlight uses price variable not defined in route
`SPOTLIGHT_PRICE_INR` referenced in `membership/routes.py` but defined as a module-level constant. Not configurable via admin console.

### TD-M11 — Multiple `check_gotra_compatibility` definitions
`check_gotra_compatibility` is defined both in `utils_kundli.py` (lines 244 and 357) and referenced from `kundli/routes.py`. Function is duplicated. Only one should exist.

---

## LOW DEBT ITEMS

### TD-L01 — No API versioning prefix
No `/api/v1/` prefix hierarchy. When REST API is added, there is no version namespace.

### TD-L02 — No OpenAPI specification
No Swagger/OpenAPI documentation file. When REST API is built, documentation requires separate effort.

### TD-L03 — Translations: single Marathi file, no proper i18n framework
Marathi translations use a custom dict in `translations/mr/messages.py`. No Flask-Babel or standard i18n framework. Adding a third language requires rebuilding the mechanism.

### TD-L04 — Procfile lacks Celery Beat worker
Procfile defines web worker only. Does not include Celery worker or Celery Beat process. Deployment automation will miss async tasks.

### TD-L05 — `require` passwords not enforced by form validation
Registration form validates age, consent, and DOB. Does not enforce password strength beyond minimum length.

### TD-L06 — S3 ACL change required one-time script
Making existing photos private requires a manual script. No automated migration. New uploads use private ACL but old photos remain public until manual script is run.

### TD-L07 — `/set-language/<lang>` route registered in `__init__.py`
A utility route is registered directly in the application factory rather than in a blueprint. This is an architectural inconsistency.

### TD-L08 — No loading states on UI
No skeleton loading screens, no spinners on form submission, no optimistic UI updates. All interactions wait for full page reload.

---

## DEBT RESOLUTION PRIORITY ORDER

```
IMMEDIATE (Before v2 development)
  TD-C03 — Delete /ijodidar/ duplicate directory
  TD-C01 — Define test strategy (minimum: smoke tests)

SPRINT 1 (Foundation)
  TD-C06 — Split models.py into domain files
  TD-C05 — Fix Celery app context pattern
  TD-H09 — Remove admin blueprint
  TD-H03 — Migrate to dob Date column exclusively
  TD-H04 — Fix PartnerPreference field types

SPRINT 2 (API + Mobile Readiness)
  TD-C02 — Add REST API layer (/api/v1/)
  TD-M02 — Add UserDevice model
  TD-M09 — Add SocketIO JWT auth
  TD-H07 — Cache context processor counts in Redis
  TD-M01 — Add last_active_at column

SPRINT 3 (UX + Engagement)
  TD-H01 — Consolidate profile editing (22 pages → 1)
  TD-H05 — Add mobile filter bottom sheet
  TD-H06 — Add completeness ring to navbar
  TD-C04 — Implement Celery Beat scheduled tasks
  TD-H08 — Bundle Bootstrap locally
```

---

CHECKPOINT_STATUS
Current Phase: 0 — Repository Discovery
Current Section: TECHNICAL_DEBT_REPORT.md Complete
Completed: REPOSITORY_DISCOVERY.md, DEPENDENCY_GRAPH.md, TECHNICAL_DEBT_REPORT.md
Remaining: Awaiting Phase 0 approval before Phase A
Files Generated: 3
Progress Percent: 22%

---

## PHASE 0 STOP — AWAITING APPROVAL

Phase 0 is complete. Three documents have been generated:

1. **REPOSITORY_DISCOVERY.md** — Complete inventory of all infrastructure, Flask architecture, models, templates, integrations, and the critical finding of the duplicate `/ijodidar/` directory.

2. **DEPENDENCY_GRAPH.md** — Module dependency tree, circular dependency analysis, tight coupling map, and integration risk register.

3. **TECHNICAL_DEBT_REPORT.md** — 34 classified technical debt items: 6 Critical, 9 High, 11 Medium, 8 Low.

**Critical findings requiring decision before Phase A:**
- 6 CRITICAL debt items including no test suite, no REST API, duplicate directory structure
- 4 missing integrations that block mobile app development
- No scheduled task infrastructure (Celery Beat)

Reply **CONTINUE** to proceed to Phase A — Complete Codebase Inventory.
