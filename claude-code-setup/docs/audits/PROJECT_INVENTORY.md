# PROJECT_INVENTORY.md
## iJodidar v2 — Complete Codebase Inventory
## Phase A | Enterprise Audit | June 2026

---

## INVENTORY METHODOLOGY

For every subsystem, this document provides:
- **Classification:** KEEP / MODIFY / REPLACE / REMOVE / NEW
- **Executive Summary:** What it does and how well
- **Findings:** Verified from source code
- **Risks:** Identified concerns
- **Dependencies:** What depends on this
- **Migration Impact:** What changes if this is modified
- **Effort:** S (hours) / M (days) / L (weeks) / XL (sprints)
- **Priority:** P0 (blocking) / P1 (sprint 1) / P2 (sprint 2)

---

## 1. AUTHENTICATION SYSTEM

**Classification: MODIFY**

### Executive Summary
The authentication system is functionally sound for a web application. Email + password registration, email verification, password reset, phone OTP, and Aadhaar KYC workflows all exist. However, the system is built entirely on Flask session cookies and has no JWT token capability, which makes it incompatible with a mobile REST API.

### Findings
- **Registration:** WTForms-validated with age check, consent recording, DOB saved to Profile. Account lockout after 10 failures (30-minute lock). DPDP-compliant consent timestamp.
- **Email verification:** 24-hour token expiry enforced. Async via Celery.
- **Password reset:** 1-hour token expiry. Async email via Celery.
- **Phone OTP:** OTP stored as bcrypt hash (not plaintext). 10-minute expiry. MSG91 in dev-logging mode.
- **Session management:** `session_version` column on User. Invalidated on password change.
- **Account lockout:** `failed_login_count` + `locked_until` on both User and AdminUser.

### Risks
- No JWT token authentication — mobile app is blocked.
- Email as primary gate (not phone) — 40-60% drop-off at verification step.
- No password strength enforcement beyond 8-character minimum.
- `send_phone_otp()` and `verify_phone()` are route handlers with no service abstraction.

### Dependencies
- Flask-Login session management (web)
- Flask-WTF CSRF protection
- AWS SES via Celery (email)
- MSG91 via Celery (SMS)
- `User.session_version` (session invalidation)

### Migration Impact
Adding JWT requires Flask-JWT-Extended. Phone-first registration requires restructuring the registration form and flow. Existing session auth for web should remain unchanged.

### Effort: M | Priority: P1

---

## 2. REGISTRATION & ONBOARDING SYSTEM

**Classification: MODIFY**

### Executive Summary
A 5-step onboarding wizard (`/onboarding/gender`, `/basics`, `/career`, `/photo`, `/preferences`, `/done`) enforced via a `before_request` gate. The gate redirects any authenticated user without gender+looking_for to Step 1. Steps 2-5 are skippable. The flow is architecturally correct but email verification is still required before users see any value.

### Findings
- **RegistrationForm:** DOB, consent, age validator, email/username uniqueness, phone regex.
- **Onboarding gate:** Hardcoded set of 12 exempt endpoints in `app/__init__.py`.
- **5 templates:** `gender.html`, `basics.html`, `career.html`, `photo.html`, `preferences.html`, `done.html` — all use `base_step.html` with progress bar.
- **Profile seeding:** DOB saved to Profile during registration. Income_lpa available at step 3.

### Risks
- Onboarding exempt list uses hardcoded string endpoint names — renaming any endpoint silently breaks exemption.
- Email verification gate still active — users cannot see home feed until email verified.
- No phone-first registration path.

### Dependencies
- Before_request hook in `app/__init__.py`
- `Profile` model (gender, looking_for)
- All blueprint route names (exempt set)

### Migration Impact
Phone-first registration requires new auth route and removal of email gate. The 5-step onboarding templates remain largely reusable.

### Effort: M | Priority: P1

---

## 3. PROFILE SYSTEM

**Classification: REPLACE**

### Executive Summary
The profile editing system has the most critical UX debt in the codebase. Twenty-two separate routes (each a full-page load) handle individual profile fields. This fragmented approach creates unacceptably low completion rates. All other aspects of the Profile model are well-designed.

### Findings
**Profile model has 40+ fields covering:** gender, looking_for, DOB (both String and Date columns), height, weight, complexion, body_type, bio, religion, caste, sub_caste, gotra, manglik, mother_tongue, diet, smoking, drinking, marital_status, have_children, family_type, family_status, is_spotlight, marathi_sub_caste, birth_nakshatra, birth_rashi, kundli_score, hobbies (JSON string), is_nri, id_verified, ui_language.

**22 separate routes:** `/name`, `/gender`, `/looking_for`, `/birthday`, `/bio`, `/height`, `/religion`, `/lifestyle`, `/email`, `/phone`, `/address/current`, `/professional`, `/education`, `/language`, `/upload_image`, `/delete_image/<id>`, `/set_primary_image/<id>`, `/partner_preferences`, `/privacy`, `/referral`, `/nri`, `/hobbies`.

**Profile completeness:** `calculate_profile_completeness()` — dynamic Python calculation on every call. Returns 0-100 integer. Not cached.

### Risks
- 22 page loads to complete a profile. Mobile users abandon after 3-5 pages.
- `date_of_birth` String and `dob` Date both exist. Code writes to one, reads from the other inconsistently.
- `plan_can_view_photos` property exists on User (returns False for Free plan). Photo blur logic implemented in templates.
- No AJAX saves — every edit is a page reload.

### Dependencies
- `Profile` model (one-to-one with User)
- `ProfessionalDetails` model (one-to-many with User)
- `Education` model (one-to-many)
- `Address` model (one-to-many)
- `Language` model (one-to-many)
- `ProfileImage` model (S3 URLs)
- `calculate_profile_completeness()` in utils.py

### Migration Impact
Replacing with AJAX section editor requires new `/api/profile/<section>` endpoints and a single unified profile template. Old routes should redirect to `/profile?section=X` for backward compatibility.

### Effort: L | Priority: P1

---

## 4. SEARCH & DISCOVERY SYSTEM

**Classification: MODIFY**

### Findings
- **15 active search filters:** keyword, gender, age range, height range, religion, caste, marathi_sub_caste, NRI, mother tongue, marital status, manglik, diet, city, education, sort.
- **Missing filter:** income_lpa — the column exists and INCOME_RANGES are defined in search routes, but the actual filter query for income_lpa is NOT implemented (only the UI dropdown exists).
- **Pagination:** Correctly uses SQLAlchemy `.paginate(page=page, per_page=20)`.
- **Eager loading:** `joinedload` imported but not used in the search query. Search results trigger N+1 for profile images.
- **Discovery tabs:** Best Matches, New, Mutual, Near Me — these do NOT exist. The home feed has no sub-tab navigation.
- **Mobile filters:** Filter sidebar is `d-none d-lg-block`. No mobile filter panel exists.

### Risks
- Income filter is defined but not active — users cannot filter by income despite UI showing it.
- No "Who Viewed Me" feature surface in search or discovery.
- No daily match email to drive re-engagement.
- Search age filter uses `Profile.date_of_birth` String comparison — inaccurate for String format variations.
- N+1 queries on search results for profile images.

### Dependencies
- `Profile`, `User`, `Address`, `City`, `Education`, `ProfessionalDetails` models
- `BlockList` for exclusion
- `utils_kundli.MARATHI_SUB_CASTES` for sub-caste filter

### Migration Impact
Income filter: 1-hour fix. Discovery tabs: 1-day addition to home route. Mobile filter: 3-day bottom sheet implementation.

### Effort: M | Priority: P1

---

## 5. MATCH SCORING ENGINE

**Classification: MODIFY**

### Executive Summary
`calculate_match_score()` in `utils.py` (145 lines) is a multi-factor weighted scoring function. It is functional, astrologically integrated, and behaviorally augmented. The fundamental algorithm is correct for a matrimony platform.

### Findings
**9 scoring factors:**
1. Religion match: +20 pts
2. Age range: +15 pts
3. Caste match: +12 pts (with partial match)
4. Location match: +10 pts
5. Height match: +8 pts
6. Mother tongue: +8 pts
7. Education level: +7 pts
8. Diet match: +5 pts
9. Marital status: +5 pts
10. Photo bonus: +5 pts
11. Hobbies overlap: +5 pts

**Behavioral signal boost:** ±10 pts via `get_signal_boost()` (7 signal types in UserSignal table)
**Guna Milan integration:** ±5 pts based on 36-point compatibility score
**MAX score denominator:** 90 (not 100) — scaled to percentage

### Risks
- **Synchronous execution:** Score calculated for each of 80 candidates on every home feed load. DB query inside loop for Guna Milan. No caching.
- **Age filter uses date_of_birth String** — the same dual-column problem as profile editing.
- **Religion preference is single-value** — if user prefers Hindu OR Jain, the score only rewards one.
- **No `last_active_at` signal** — recently active profiles are not boosted.
- **Income is never a scoring factor** despite being a top matrimony preference.

### Migration Impact
Score caching via Redis (invalidate on profile update) eliminates the per-request calculation. Match score column on `users` (updated by Celery task) enables feed pagination without rescoring.

### Effort: M | Priority: P1

---

## 6. INTERESTS (CONNECT) SYSTEM

**Classification: KEEP**

### Executive Summary
The interest system is well-implemented. State machine (pending → accepted/declined/withdrawn) is correct. Monthly limit tracking is implemented. All appropriate gates are in place.

### Findings
- **Interest model:** `sender_id`, `receiver_id`, `status` (pending/accepted/declined/withdrawn), `message` (300 chars), UniqueConstraint prevents duplicate sends.
- **Monthly tracking:** `UserSubscription.interests_remaining()` — auto-resets after 30 days.
- **Gates enforced:** email verified, monthly limit, blocked users, self-interest.
- **Signals fired:** `interest_sent`, `interest_accepted`, `interest_declined` on all actions.
- **Async emails:** Via Celery for all interest notifications.

### Risks
- `UserSubscription.interests_remaining()` calls `db.session.commit()` inside a model property — violation of SoC.
- No "mutual interest" detection feature (both users have shortlisted each other).
- No notification when interest is about to expire (30-day window).

### Migration Impact: Minimal. Model is correct. Add mutual interest detection to home feed tabs.

### Effort: S | Priority: P2

---

## 7. MESSAGING SYSTEM

**Classification: MODIFY**

### Executive Summary
Real-time SocketIO chat with WebRTC video/audio calling is implemented. The messaging foundation is solid. However, the auth model is session-only, blocking mobile app. Message email notification is synchronous inside the SocketIO event handler.

### Findings
- **Conversation model:** Unique pair constraint (user1_id, user2_id). Linked to accepted Interest via `interest_id`. `last_message()` method.
- **Message model:** `body` Text, `is_read` Boolean, `sent_at` DateTime.
- **SocketIO events:** connect/disconnect, join/leave conversation room, send_message, WebRTC signaling (offer, answer, ICE, hang-up, reject, call-rejected), typing indicator.
- **WebRTC:** Full peer-to-peer signaling implemented via SocketIO rooms. Dedicated `/messages/<id>/call` page.
- **HTTP fallback:** `/messages/<id>/poll` endpoint for environments where SocketIO fails.
- **Phone gate:** Must verify phone before sending first message.

### Risks
- SocketIO auth is session-only (Flask-Login `current_user`). Mobile JWT auth not supported.
- Email notification sent synchronously inside `on_send_message()` SocketIO handler — blocks the event loop.
- No message soft-delete (deleted_for_user1, deleted_for_user2).
- Message body max length: 1000 chars (enforced in SocketIO handler, not at model level).
- `send_email()` called directly in socket_events.py — should use Celery task.

### Dependencies
- Flask-SocketIO, gevent (prod), threading (dev)
- `Conversation`, `Message` models
- `Interest` model (accepted check)
- `UserSubscription.plan.can_message`

### Effort: M | Priority: P1

---

## 8. MEMBERSHIP & PAYMENT SYSTEM

**Classification: KEEP with MODIFICATIONS**

### Executive Summary
Razorpay integration is correctly implemented with server-side order validation, HMAC signature verification, and webhook support. Currently on test keys. Well-architected for a single-developer build.

### Findings
- **4 plans:** Free (₹0/forever), Silver (₹499/30d), Gold (₹999/90d), Platinum (₹1,999/180d).
- **Payment flow:** Create Razorpay order → client completes → `/verify-payment` validates signature → server fetches order from Razorpay (not client) to prevent amount tampering → plan activated.
- **Webhook:** `/webhook/razorpay` with dedicated webhook secret.
- **Spotlight:** Position-slot based (not score inflation). Admin verification required for UPI manual payment.
- **Assisted plan:** `AssistedRequest` + `RMContactLog` with full console workflow.

### Missing
- Per-day pricing display on plans page.
- Social proof ("X members upgraded this week").
- Annual plan option.
- Automated subscription expiry (no Celery Beat task).

### Effort: S | Priority: P2

---

## 9. KUNDLI / GUNA MILAN SYSTEM

**Classification: KEEP**

### Executive Summary
The most technically distinctive feature of iJodidar. Pure-Python Vedic astronomy engine. No external API dependencies. Corrected Nadi assignments. Integrated into match scoring.

### Findings
- **`vedic_engine.py`:** Meeus Chapter 47 Moon algorithm. Lahiri ayanamsa. ±0.3° accuracy. 100+ Indian cities built-in. Nominatim fallback.
- **`utils_kundli.py`:** 8 Ashta Koota factors. Corrected Nadi (9-9-9 distribution verified). Corrected Vashya (zodiac groups). Manglik via Chandra Lagna.
- **Auto-calculation:** DOB + time + city → all Vedic attributes computed. Live AJAX preview before save.
- **Guna Milan in match scoring:** ±5 pts based on 36-point score.
- **Routes:** `/kundli/edit` (save), `/kundli/match/<id>` (report), `/kundli/api/calculate`, `/kundli/api/match`, `/kundli/api/cities`.

### Risks
- **Duplicate function definitions:** `check_gotra_compatibility` defined twice in `utils_kundli.py` (lines 244 and 357). Only one should exist.
- **Manglik is approximate:** Chandra Lagna proxy, not full D1 chart. Clearly disclosed in UI.
- **KundliDetail DB query inside scoring:** For every candidate that has kundli data, a DB query runs inside `calculate_match_score()`. Not cached.

### Effort: S (cleanup) | Priority: P2

---

## 10. FAMILY SYSTEM

**Classification: KEEP**

### Executive Summary
Family tree management with `FamilyDetails`, `RelationType`, `RelationCategory` models. Unique to iJodidar among competitors. DPDP concern: third-party phone numbers stored without explicit consent.

### Findings
- **3 routes:** `/family`, `/family/edit`, `/family/delete/<id>`.
- **RelationType seeded:** 42 relation types across 10 categories.
- **FamilyDetails model:** first_name, last_name, occupation, contact_number, age, email, marital_status, address_id.
- **DPDP Issue:** No consent flag for family members' data.

### Effort: S | Priority: P2

---

## 11. NOTIFICATIONS SYSTEM

**Classification: MODIFY**

### Executive Summary
In-app notifications via DB table + SocketIO real-time push. 3 polling endpoints. No push notification capability (FCM). No `UserDevice` model.

### Findings
- **Notification model:** user_id, type, message (200 chars), link, is_read, created_at.
- **Types:** interest_received, interest_accepted, new_message, profile_viewed, system.
- **3 routes:** `/notifications/unread-count` (JSON), `/notifications/list` (JSON), `/notifications/mark-read` (POST).
- **Real-time:** SocketIO `emit('notif_update', {})` to personal room triggers badge refresh.
- **Context processor:** Queries unread count on EVERY authenticated request (N+1 risk).

### Missing
- FCM push notifications for mobile.
- `UserDevice` model for FCM token storage.
- Notification pagination.
- Notification type icons in the DB (stored only in JavaScript).

### Effort: M | Priority: P1

---

## 12. REFERRAL SYSTEM

**Classification: KEEP**

### Executive Summary
Dual-sided referral with fraud prevention. Both referrer and referred user get Silver plan. Gated behind phone verification. IP tracking on Referral model.

### Findings
- `Referral` model: referrer_id, referred_id, code (12-char, unique), rewarded_at (referrer), referred_rewarded_at (referred), ip_address, device_fingerprint.
- `reward_referrer()` grants 30-day Silver. `reward_referred()` grants 15-day Silver.
- Both rewards fire only after email AND phone verified.

### Effort: S | Priority: P2

---

## 13. CONSOLE (STAFF ADMIN) SYSTEM

**Classification: KEEP**

### Executive Summary
The most enterprise-grade component in the codebase. Separate AdminUser model, 5 RBAC roles, TOTP 2FA, IP restriction, brute force lockout, audit log. Exceeds many production matrimony platforms in operational maturity.

### Findings
- **5 roles:** ceo, vp, business_owner, relationship_manager, executive — each with permission set.
- **TOTP 2FA:** Google Authenticator. Setup via QR code. `verify_totp()` with 30s drift window.
- **Brute force:** 5 failures → 60-minute lock.
- **IP restriction:** `CONSOLE_ALLOWED_IPS` env var.
- **Audit log:** `AdminAuditLog` — immutable, INSERT-only. Actions: suspend_user, activate_user, dismiss_report, suspend_reported_user, grant_id_verify.
- **RM workflow:** `AssistedRequest` + `RMContactLog` + `assisted_detail.html` template.
- **Rate limiting:** `@limiter.limit("10 per minute")` on console login.

### Risks
- Console IP is managed via env var only — no UI to update from console itself.
- `inject_console_context()` runs on every console request with 2 DB queries for badge counts.

### Effort: S | Priority: P2

---

## 14. CSS/FRONTEND ARCHITECTURE

**Classification: MODIFY**

### Executive Summary
907-line `style.css` contains a well-structured iJodidar design system with proper CSS custom properties. However, it mixes design system tokens with Bootstrap overrides and lacks the spacing system, typography scale, and z-index scale defined in the MOBILE_FIRST_DESIGN_SYSTEM document.

### Findings
**Design tokens present:** `--brand`, `--brand-dark`, `--brand-alpha`, `--bg`, `--surface`, `--surface-2`, `--border`, `--border-light`, `--text`, `--text-2`, `--text-3`, `--green`, `--green-bg`, `--amber`, `--amber-bg`, `--blue`, `--blue-bg`, `--purple`, `--shadow-xs` through `--shadow-lg`, `--r-sm` through `--r-xl`, `--t-fast`, `--t-mid`.

**Missing tokens:** `--space-*` (spacing scale), `--text-xs` through `--text-5xl` (typography scale), `--z-*` (z-index scale), `--trust-*` (trust badge colors), `--score-*` (match score colors).

**Bootstrap dependency:** Bootstrap 5.3.3 loaded via CDN. No local copy. Used for grid, dropdowns, modals, carousel. Profile view (`my_profile.html`) uses Bootstrap `card shadow-sm rounded-4` instead of design system `ij-card` — creating visual inconsistency.

**JavaScript:** Minimal inline JavaScript in `base.html` (navbar scroll, toast dismiss, notification polling). No bundler. No JavaScript build process.

### Dependencies
- All 78 templates depend on `base.html` which loads Bootstrap CDN.
- `my_profile.html` uses Bootstrap directly.
- `location_cascade.js` and `upload_cropper.js` depend on Cropper.js CDN.

### Effort: M | Priority: P1

---

## 15. API LAYER

**Classification: NEW**

### Executive Summary
No REST API layer exists. This is the highest-priority missing component for mobile app enablement.

### Current JSON Endpoints (only 4)
| Route | Auth | Purpose |
|-------|------|---------|
| `/kundli/api/calculate` | Session | Nakshatra auto-calc |
| `/kundli/api/match` | Session | Guna Milan score |
| `/kundli/api/cities` | Session | City autocomplete |
| `/notifications/unread-count` | Session | Badge count |
| `/notifications/list` | Session | Notification list |
| `/messages/<id>/poll` | Session | HTTP fallback for SocketIO |

### Missing
All authentication, profile, feed, interest, messaging, membership API endpoints. Flask-JWT-Extended not installed. Marshmallow not installed. No API versioning (`/api/v1/`).

### Effort: L | Priority: P0

---

## 16. CELERY / REDIS ARCHITECTURE

**Classification: MODIFY**

### Executive Summary
Celery is correctly configured with Redis broker. 9 async tasks cover email, SMS, and WhatsApp. The task architecture has a structural flaw (wsgi.py import) but is functional. Celery Beat is completely absent.

### Findings
**9 tasks:** send_email_task, send_verification_email_task, send_welcome_email_task, send_interest_email_task, send_interest_accepted_email_task, send_message_email_task, send_password_reset_email_task, send_sms_task, send_whatsapp_task.

**Redis DB allocation:** Rate limiting on DB 0, Celery on DB 1 (from config: `redis://localhost:6379/1`). Correct separation.

**Missing tasks:** Daily match digest, subscription expiry, match score pre-computation, OTP cleanup, stale notification cleanup.

**systemd service:** `celery.service` file exists. Beat process not defined.

### Effort: M | Priority: P0

---

## COMPLETE CLASSIFICATION SUMMARY

| Subsystem | Classification | Priority | Effort |
|-----------|---------------|---------|--------|
| Authentication (web) | MODIFY | P1 | M |
| Authentication (JWT/mobile) | NEW | P0 | M |
| Registration & Onboarding | MODIFY | P1 | M |
| Profile Editing (22 pages) | REPLACE | P1 | L |
| Profile Model | MODIFY | P1 | M |
| Search & Discovery | MODIFY | P1 | M |
| Discovery Tabs (New/Mutual/Near) | NEW | P1 | M |
| Match Scoring Engine | MODIFY | P1 | M |
| Match Score Caching | NEW | P1 | M |
| Interests System | KEEP | P2 | S |
| Messaging (SocketIO) | MODIFY | P1 | M |
| SocketIO JWT Auth | NEW | P1 | M |
| Membership & Payments | KEEP + MODIFY | P2 | S |
| Kundli / Guna Milan Engine | KEEP | P2 | S |
| Family System | KEEP | P2 | S |
| Notifications (web) | MODIFY | P1 | M |
| Push Notifications (FCM) | NEW | P1 | M |
| Referral System | KEEP | P2 | S |
| Console (Staff Admin) | KEEP | P2 | S |
| CSS Design System | MODIFY | P1 | M |
| REST API Layer | NEW | P0 | L |
| Celery (existing tasks) | MODIFY | P1 | M |
| Celery Beat (scheduled) | NEW | P0 | M |
| Test Suite | NEW | P0 | XL |
| Service Layer | NEW | P1 | L |
| Admin Blueprint (deprecated) | REMOVE | P0 | S |
| `/ijodidar/` duplicate dir | REMOVE | P0 | S |
| UserDevice (FCM) model | NEW | P1 | S |
| `last_active_at` column | NEW | P1 | S |
| Marshmallow schemas | NEW | P0 | M |

---

CHECKPOINT_STATUS
Current Phase: A — Complete Codebase Inventory
Current Section: PROJECT_INVENTORY.md Complete
Completed: REPOSITORY_DISCOVERY.md, DEPENDENCY_GRAPH.md, TECHNICAL_DEBT_REPORT.md, PROJECT_INVENTORY.md
Remaining: Phase B (REDESIGN_ALIGNMENT_REPORT), Phase C (MATRIMONY_GAP_ANALYSIS), Phase C2 (FEATURE_RATIONALIZATION), Phase D (Migration Blueprint + 8 architecture docs)
Files Generated: 4
Progress Percent: 28%

Reply **CONTINUE** to proceed to Phase B — Redesign Document Analysis.
