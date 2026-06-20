# iJodidar v2 Migration Blueprint
## Enterprise Transformation Blueprint | Board-Level Strategy Document
## Phase D | June 2026

---

# SECTION 1 — EXECUTIVE SUMMARY

## Current Maturity Assessment

iJodidar is a functional matrimonial platform built on a sound technical foundation.
The monolith architecture is correct for the current scale. The Guna Milan engine,
RBAC console, Celery async queue, and DPDP compliance exceed most competitors at
this stage. However, five structural deficiencies prevent growth beyond 500 active users.

### Current Maturity Level: 4 / 10 (Early-Stage Web-Only Product)

| Dimension | Current | Target (v2) |
|-----------|---------|-------------|
| API Maturity | 1 / 10 — 4 JSON endpoints, session auth only | 7 / 10 — Full REST API, JWT, versioned |
| Mobile Readiness | 1 / 10 — Zero mobile API surface | 7 / 10 — React Native ready |
| Engagement Automation | 1 / 10 — No scheduled tasks, no push | 7 / 10 — Celery Beat, FCM, daily digest |
| Profile Completion UX | 2 / 10 — 22 separate pages | 8 / 10 — Single AJAX editor, 5 sections |
| Discovery Depth | 2 / 10 — Single feed, no tabs | 7 / 10 — 4-tab discovery, Who Viewed Me |
| Trust Infrastructure | 3 / 10 — Badges exist, not visible | 7 / 10 — Trust tiers on every card |
| Conversion Mechanics | 2 / 10 — No pricing psychology | 7 / 10 — Per-day pricing, social proof |
| Competitive Standing | 40 / 100 | 78 / 100 |

### Five Transformation Blockers (must resolve in order)

1. **No REST API** — Android/iOS app impossible
2. **No Celery Beat** — daily digest, subscription expiry, score refresh impossible
3. **Email gate on registration** — 40-60% registration drop-off
4. **22-page profile editor** — profile completion under 20%
5. **Income filter not wired** — top matrimony search filter broken

### Transformation Strategy

Execute in 6 sprints across 3 months. Each sprint is independently deployable.
No sprint requires the next to be complete. Revenue impact compounds with each sprint.

---

## Subsystem Disposition Summary

| Subsystem | Disposition | Sprint |
|-----------|------------|--------|
| Authentication (web) | MODIFY | 1 |
| Authentication (JWT/API) | NEW | 2 |
| Registration (phone-first) | MODIFY | 1 |
| Onboarding wizard | MODIFY | 1 |
| Profile model | MODIFY | 1 |
| Profile editor (22 pages) | REPLACE | 3 |
| Search & discovery | MODIFY | 2 |
| Discovery tabs | NEW | 2 |
| Match scoring | MODIFY | 2 |
| Match score cache | NEW | 4 |
| Interests system | KEEP | — |
| Messaging (web) | MODIFY | 1 |
| Messaging (mobile/JWT) | MODIFY | 2 |
| Membership & payments | MODIFY | 2 |
| Subscription expiry | NEW | 1 |
| Kundli / Guna Milan | KEEP | — |
| Family system | KEEP | — |
| Notifications (web) | MODIFY | 1 |
| FCM push notifications | NEW | 3 |
| Referral system | KEEP | — |
| Console (staff) | KEEP | — |
| Admin blueprint | REMOVE | 0 (pre-sprint) |
| REST API layer | NEW | 2 |
| Celery Beat | NEW | 1 |
| UserDevice model | NEW | 3 |
| CSS design system | MODIFY | 2 |
| Test suite | NEW | All sprints |
| `/ijodidar/` directory | REMOVE | 0 (pre-sprint) |

---

# SECTION 2 — CURRENT VS TARGET ARCHITECTURE

## Flask Architecture

| Dimension | Current State | Target State | Migration Path |
|-----------|--------------|--------------|---------------|
| Blueprint count | 13 (including deprecated admin) | 14 (add api_v1; remove admin) | Add `app/api/` blueprint; delete `app/admin/` |
| Route count | ~80 HTML routes + 6 JSON | ~80 HTML + ~35 JSON API routes | New `/api/v1/` prefix for all JSON |
| Auth mechanism | Flask-Login sessions | Sessions (web) + JWT (mobile/API) | Flask-JWT-Extended alongside Flask-Login |
| Serialization | Jinja2 templates only | Jinja2 (web) + Marshmallow schemas (API) | New `app/api/schemas.py` |
| Service layer | None — logic in routes | Extract domain services gradually | `app/services/` directory, Sprint 3+ |
| models.py | 34 models, 800+ lines, 1 file | Domain-split: `models/user.py`, `models/profile.py`, etc. | Split in Sprint 3; high-risk change |

## Database Architecture

| Component | Current | Target | Risk |
|-----------|---------|--------|------|
| `Profile.date_of_birth` | String(15) — legacy | Deprecated; all reads use `dob` Date | MEDIUM — 2-hour code migration |
| `Profile.dob` | Date — exists | Primary DOB column | LOW — already exists |
| `PartnerPreference.min_income` | String "3 LPA" | Deprecated | MEDIUM — search query change |
| `PartnerPreference.min_income_lpa` | Missing | Integer column | LOW — additive migration |
| `PartnerPreference.max_income_lpa` | Missing | Integer column | LOW — additive migration |
| `PartnerPreference.religion` | String(50) single value | Kept; add `religion_list` JSON column | LOW — additive |
| `User.last_active_at` | Missing | DateTime column | LOW — additive |
| `UserDevice` table | Missing | New table for FCM tokens | LOW — additive |
| `MatchScoreCache` table | Missing | Optional in Sprint 4 | LOW — additive |
| `SavedSearch` table | Not planned | Defer to v3 | NONE |
| `profile_views` daily unique index | Missing | Add unique index on (viewer_id, viewed_id, DATE(timestamp)) | LOW |

## Redis Usage

| Current Usage | Target Usage |
|--------------|-------------|
| Rate limiting (DB 0) | Rate limiting (DB 0) — unchanged |
| Celery broker (DB 1) | Celery broker (DB 1) — unchanged |
| — | Notification badge cache (DB 2) |
| — | Match score cache (DB 3) — Sprint 4 |
| — | JWT token revocation list (DB 4) — Sprint 2 |

## Celery Architecture

| Current | Target |
|---------|--------|
| 9 on-demand tasks (email, SMS, WhatsApp) | 9 existing + 5 new tasks |
| No Celery Beat | Celery Beat with 5 scheduled tasks |
| `from wsgi import app` pattern | `ContextTask` pattern (fix Sprint 1) |

New tasks required:
1. `send_daily_match_digest` — 8:00 AM IST daily
2. `check_subscription_expiry` — 00:30 IST daily
3. `refresh_active_user_scores` — hourly (Sprint 4)
4. `cleanup_expired_otps` — every 30 minutes
5. `send_fcm_push_notification` — on-demand (Sprint 3)

## SocketIO Authentication

| Current | Target |
|---------|--------|
| Flask-Login session only | Session (web) + JWT token (mobile) |
| `current_user.is_authenticated` check | Session check first; JWT fallback |
| Mobile app blocked | Mobile app can connect with Bearer token |

---

# SECTION 3 — MATRIMONY DOMAIN GAP SUMMARY

Derived from Phase C findings. Classified by urgency.

## Critical Missing Features

| Feature | Domain | Sprint | Effort |
|---------|--------|--------|--------|
| Income filter wired in search | Discovery | Pre-sprint | S |
| Subscription auto-expiry (Celery Beat) | Conversion | 1 | M |
| Daily match email digest | Engagement | 1 | M |
| Who Viewed Me surfaced in feed | Discovery | 2 | S |
| Trust tier badge on profile cards | Trust | 2 | S |
| Per-day pricing + social proof | Conversion | 2 | S |
| Discovery tabs (Best/New/Mutual/Near) | Discovery | 2 | M |
| Phone-first registration | Onboarding | 1 | M |
| REST API for mobile | API | 2 | L |
| FCM push notifications | Engagement | 3 | M |

## Important Missing Features

| Feature | Domain | Sprint | Effort |
|---------|--------|--------|--------|
| `last_active_at` on User | Discovery | 1 | S |
| Match score on profile cards | Discovery | 2 | S |
| Profile completion ring in navbar | Engagement | 2 | S |
| Interest-remaining counter in feed | Conversion | 2 | S |
| Mobile filter bottom sheet | Discovery | 2 | M |
| PartnerPreference multi-religion | Profile | 3 | M |
| Message soft-delete | Messaging | 4 | S |
| Annual plan option | Conversion | 4 | M |
| Aadhaar KYC live (API key) | Trust | Business | S |

## Nice-to-Have Features

| Feature | Sprint |
|---------|--------|
| Photo watermark | v3 |
| Private profile mode | v3 |
| Reverse matches | v3 |
| Background verification | v3 |
| WhatsApp re-engagement | Business configuration |

---

# SECTION 4 — DATABASE MIGRATION PLAN

## Tables — Disposition and Changes

### KEEP — No Schema Changes

| Table | Reason |
|-------|--------|
| interests | Correct schema; UniqueConstraint present |
| conversations | Correct; UniqueConstraint on user pair |
| shortlists | Correct; UniqueConstraint on user pair |
| block_list | Correct; UniqueConstraint on blocker/blocked |
| user_reports | Correct |
| countries / states / cities | Reference data; no changes |
| relation_categories / relation_types | Reference data; seeded |
| family_relations | Correct |
| phone_alternates | Correct |
| profile_images | Correct; 3-URL pattern |
| languages | Correct |
| kundli_details | Correct |
| referrals | Correct; dual reward columns present |
| assisted_requests | Correct |
| rm_contact_logs | Correct |
| admin_audit_logs | Correct; INSERT-only |
| admin_users | Correct; TOTP columns present |
| success_stories | Correct |
| user_signals | Correct; composite indexes present |
| notifications | Keep; add pagination in query layer only |

### MODIFY — Column Changes Required

**users table**

| Change | Type | Column | Notes |
|--------|------|--------|-------|
| ADD | DateTime | `last_active_at` | NULL; index; updated hourly by before_request |
| MIGRATION ORDER | After Sprint 1 column add |

**profiles table**

| Change | Type | Column | Notes |
|--------|------|--------|-------|
| ADD | Integer | `completeness_pct` | Cache of computed completeness; updated on save |
| ADD | Varchar(20) | `profile_for` | Self / Son / Daughter / Brother / Sister / Relative |
| DEPRECATE | (keep column) | `date_of_birth` | All code reads `dob` Date; `date_of_birth` frozen |
| MIGRATION ORDER | After Sprint 1 (completeness_pct), Sprint 3 (profile_for) |

**partner_preferences table**

| Change | Type | Column | Notes |
|--------|------|--------|-------|
| ADD | Integer | `min_income_lpa` | Replace min_income String |
| ADD | Integer | `max_income_lpa` | New upper bound |
| ADD | Text | `religion_list` | JSON array — multiple religions acceptable |
| ADD | Text | `city_list` | JSON array — multiple preferred cities |
| DEPRECATE | (keep) | `min_income` | String column frozen; reads migrated to `min_income_lpa` |
| MIGRATION ORDER | Sprint 1 |

**family_details table**

| Change | Type | Column | Notes |
|--------|------|--------|-------|
| ADD | Boolean | `consent_given` | DPDP compliance; default False |
| MIGRATION ORDER | Sprint 2 |

**messages table**

| Change | Type | Column | Notes |
|--------|------|--------|-------|
| ADD | Boolean | `deleted_for_user1` | Soft delete; default False |
| ADD | Boolean | `deleted_for_user2` | Soft delete; default False |
| MIGRATION ORDER | Sprint 4 |

**user_subscriptions table**

| Change | Type | Column | Notes |
|--------|------|--------|-------|
| NO CHANGES | — | — | Schema correct; auto-expiry via Celery Beat |

### NEW TABLES

**user_devices** (Sprint 3)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| user_id | Integer FK → users | |
| fcm_token | Varchar(255) | Device FCM token |
| platform | Varchar(10) | ios / android / web |
| app_version | Varchar(20) | For targeted push |
| last_seen | DateTime | Update on every API auth |
| UNIQUE INDEX | (user_id, fcm_token) | Prevent duplicates |

**match_score_cache** (Sprint 4 — optional)

| Column | Type | Notes |
|--------|------|-------|
| user_id | Integer FK → users | |
| candidate_id | Integer FK → users | |
| score | SmallInt | 0-100 |
| computed_at | DateTime | Invalidate on profile save |
| PRIMARY KEY | (user_id, candidate_id) | |
| INDEX | (user_id, score DESC) | Feed query |

### NEW INDEXES

| Table | Columns | Purpose |
|-------|---------|---------|
| users | last_active_at | "Active recently" sort |
| profile_views | (viewer_id, viewed_id, DATE(timestamp)) UNIQUE | Daily dedup |
| profiles | completeness_pct | Completeness-based queries |
| user_devices | (user_id, fcm_token) UNIQUE | Prevent FCM duplicate |

### Migration Execution Order

```
Pre-Sprint 0:
  ALTER TABLE profiles ADD completeness_pct INTEGER;
  ALTER TABLE users ADD last_active_at TIMESTAMP;
  ALTER TABLE partner_preferences ADD min_income_lpa INTEGER;
  ALTER TABLE partner_preferences ADD max_income_lpa INTEGER;
  ALTER TABLE partner_preferences ADD religion_list TEXT;
  ALTER TABLE partner_preferences ADD city_list TEXT;

Sprint 2:
  ALTER TABLE family_details ADD consent_given BOOLEAN DEFAULT FALSE;
  CREATE UNIQUE INDEX ix_profile_views_daily ON profile_views(viewer_id, viewed_id, DATE(timestamp));

Sprint 3:
  CREATE TABLE user_devices (...);
  ALTER TABLE profiles ADD profile_for VARCHAR(20);

Sprint 4:
  CREATE TABLE match_score_cache (...);
  ALTER TABLE messages ADD deleted_for_user1 BOOLEAN DEFAULT FALSE;
  ALTER TABLE messages ADD deleted_for_user2 BOOLEAN DEFAULT FALSE;
```

---

# SECTION 5 — MODEL MIGRATION PLAN

## User Model

**Required changes:**
- ADD `last_active_at` DateTime column
- ADD `trust_score` property (computed from existing columns; no DB change)
- ADD `trust_label` property (returns string: "Phone Verified", "ID Verified", etc.)
- ADD `trust_tier` property (returns string: "registered", "phone", "id", "full")
- MODIFY `active_subscription` property — stop calling `db.session.commit()` inside model property
- No breaking changes to existing relationships

## UserSubscription Model

**Required changes:**
- MODIFY `interests_remaining()` — remove `db.session.commit()` from inside property
- Interest reset moved to Celery Beat task `reset_monthly_interests`
- No schema changes

## Profile Model

**Required changes:**
- ADD `completeness_pct` Integer column (cached)
- ADD `profile_for` Varchar(20) column
- FREEZE `date_of_birth` String — all new writes use `dob` Date only
- No relationship changes

## PartnerPreference Model

**Required changes:**
- ADD `min_income_lpa` Integer
- ADD `max_income_lpa` Integer
- ADD `religion_list` Text (JSON array)
- ADD `city_list` Text (JSON array)
- FREEZE `min_income` String — deprecated

## FamilyDetails Model

**Required changes:**
- ADD `consent_given` Boolean (DPDP)

## Message Model

**Required changes:**
- ADD `deleted_for_user1` Boolean (Sprint 4)
- ADD `deleted_for_user2` Boolean (Sprint 4)

## NEW: UserDevice Model (Sprint 3)

New model for FCM push notification token storage.
Fields: id, user_id FK, fcm_token, platform, app_version, last_seen.
Unique constraint on (user_id, fcm_token).

## NEW: MatchScoreCache Model (Sprint 4)

Optional caching table. Fields: user_id, candidate_id, score SmallInt, computed_at.
Composite primary key (user_id, candidate_id).

## Models to Split (Sprint 3 — High Risk)

`app/models.py` (800+ lines, 34 models) should be split into:
- `app/models/__init__.py` — re-exports all models
- `app/models/auth.py` — User, UserSubscription, MembershipPlan
- `app/models/profile.py` — Profile, ProfileImage, Address, Education, ProfessionalDetails, Language, ProfileView, PartnerPreference, KundliDetail
- `app/models/social.py` — Interest, Conversation, Message, Shortlist, BlockList, UserReport, Notification, UserSignal
- `app/models/family.py` — FamilyDetails, FamilyRelation, RelationType, RelationCategory, PhoneAlternate
- `app/models/location.py` — Country, State, City
- `app/models/business.py` — Referral, AssistedRequest, RMContactLog, SuccessStory
- `app/models/admin.py` — AdminUser, AdminAuditLog, UserDevice

**Risk:** High. Every blueprint imports from `app.models`. Split requires updating every import statement. Must be done atomically with full test coverage.

---

# SECTION 6 — ROUTE MIGRATION MATRIX

## Routes to KEEP (no change)

| Route | Blueprint | Reason |
|-------|-----------|--------|
| `/login`, `/register` | auth | Keep; add phone-first alongside |
| `/verify/<token>` | auth | Keep |
| `/forgot-password`, `/reset-password/<token>` | auth | Keep |
| `/home` | main | Keep; add `?tab=` parameter |
| `/`, `/my_profile`, `/<username>` | main | Keep |
| `/privacy-policy`, `/terms` | main | Keep |
| `/account/delete` | main/profile | Keep |
| `/search` | search | Keep; add income filter |
| `/interest/*`, `/interests` | connect | Keep |
| `/shortlist/*` | connect | Keep |
| `/block/*`, `/unblock/*`, `/report/*` | connect | Keep |
| `/messages`, `/messages/<id>` | messaging | Keep |
| `/messages/<id>/poll` | messaging | Keep |
| `/messages/<id>/call` | messaging | Keep |
| `/plans`, `/plans/*` | membership | Keep |
| `/webhook/razorpay` | membership | Keep |
| `/spotlight/*` | membership | Keep |
| `/plans/assisted` | membership | Keep |
| `/family`, `/family/edit`, `/family/delete/<id>` | family | Keep |
| `/kundli/*` | kundli | Keep |
| `/notifications/*` | notifications | Keep |
| `/onboarding/*` | onboarding | Keep; modify phone-first |
| `/console/*` | console | Keep |
| `/sitemap.xml`, `/success-stories` | main | Keep |

## Routes to MODIFY

| Current Route | Change | Reason |
|--------------|--------|--------|
| `GET /home` | Add `?tab=best\|new\|mutual\|near` | Discovery tabs |
| `GET /search` | Wire income_lpa filter | Income filter broken |
| `GET /profile` | Replace settings list with AJAX editor | 22 pages → 1 |
| `POST /send-phone-otp` | Promote to primary registration path | Phone-first |

## Routes to DEPRECATE (redirect, not remove)

All 14 individual profile edit routes will redirect to `/profile?section=X`.
After 60-day grace period, templates are deleted.

| Old Route | Redirect Target |
|-----------|----------------|
| `/name` | `/profile?section=about` |
| `/birthday` | `/profile?section=about` |
| `/gender` | `/profile?section=about` |
| `/looking_for` | `/profile?section=about` |
| `/height` | `/profile?section=about` |
| `/bio` | `/profile?section=about` |
| `/religion` | `/profile?section=about` |
| `/lifestyle` | `/profile?section=about` |
| `/email` | `/profile?section=about` |
| `/phone` | `/profile?section=about` |
| `/professional` | `/profile?section=career` |
| `/education` | `/profile?section=career` |
| `/language` | `/profile?section=career` |
| `/nri` | `/profile?section=about` |
| `/hobbies` | `/profile?section=about` |
| `/partner_preferences` | `/profile?section=prefs` |
| `/address/<tag>` | `/profile?section=about` |

## Routes to REMOVE

| Route | Blueprint | Reason |
|-------|-----------|--------|
| `GET /admin/` | admin | Redirects to `/console/` |
| `GET /admin/users` | admin | Redirects to `/console/users` |
| `GET /admin/plans` | admin | Redirects to `/console/` |
| `GET /admin/reports` | admin | Redirects to `/console/reports` |
| `GET /admin/stories` | admin | Redirects to `/console/stories` |
| `GET /admin/analytics` | admin | Redirects to `/console/analytics` |
| All 14 admin routes | admin | Remove entire blueprint |

## New Routes Required

| Route | Blueprint | Sprint |
|-------|-----------|--------|
| `POST /api/v1/auth/send-otp` | api | 2 |
| `POST /api/v1/auth/verify-otp` | api | 2 |
| `POST /api/v1/auth/refresh` | api | 2 |
| `POST /api/v1/auth/logout` | api | 2 |
| `GET /api/v1/profiles/me` | api | 2 |
| `PATCH /api/v1/profiles/me` | api | 2 |
| `GET /api/v1/profiles/feed` | api | 2 |
| `GET /api/v1/profiles/completeness` | api | 2 |
| `GET /api/v1/profiles/@<username>` | api | 2 |
| `POST /api/v1/profiles/photos` | api | 2 |
| `POST /api/v1/interests` | api | 2 |
| `GET /api/v1/interests/received` | api | 2 |
| `GET /api/v1/interests/sent` | api | 2 |
| `PATCH /api/v1/interests/<id>` | api | 2 |
| `GET /api/v1/conversations` | api | 2 |
| `GET /api/v1/conversations/<id>/messages` | api | 2 |
| `POST /api/v1/conversations/<id>/messages` | api | 2 |
| `PATCH /api/v1/conversations/<id>/read` | api | 2 |
| `GET /api/v1/notifications` | api | 2 |
| `GET /api/v1/notifications/unread-count` | api | 2 |
| `POST /api/v1/devices` | api | 3 |
| `DELETE /api/v1/devices/<token>` | api | 3 |
| `GET /api/v1/plans` | api | 3 |
| `POST /api/v1/plans/<id>/order` | api | 3 |
| `POST /api/v1/kundli` | api | 3 |
| `GET /api/v1/kundli/match/<id>` | api | 3 |
| `POST /api/profile/about` | profile (AJAX) | 3 |
| `POST /api/profile/career` | profile (AJAX) | 3 |
| `POST /api/profile/family` | profile (AJAX) | 3 |
| `POST /api/profile/photos` | profile (AJAX) | 3 |
| `POST /api/profile/preferences` | profile (AJAX) | 3 |
| `GET /api/profile/completeness` | profile (AJAX) | 3 |

---

# SECTION 7 — TEMPLATE MIGRATION MATRIX

## Templates to KEEP

| Template | Keep Reason |
|----------|------------|
| `base.html` | Modify — add completeness ring, trust badge CSS |
| `main/landing.html` | Keep — add social proof counter |
| `main/home.html` | Modify — add discovery tabs |
| `main/my_profile.html` | Modify — replace Bootstrap card classes |
| `auth/login.html` | Keep |
| `auth/register.html` | Modify — add phone-first flow |
| `auth/verify_phone.html` | Keep |
| `auth/forgot_password.html` | Keep |
| `auth/reset_password.html` | Keep |
| `auth/verify_id.html` | Keep |
| `connect/interests.html` | Modify — add Viewers tab |
| `connect/shortlist.html` | Keep |
| `messaging/inbox.html` | Keep |
| `messaging/conversation.html` | Keep |
| `messaging/call.html` | Keep |
| `membership/plans.html` | Modify — add per-day pricing, social proof |
| `membership/checkout.html` | Keep |
| `membership/spotlight.html` | Keep |
| `membership/assisted.html` | Keep |
| `kundli/edit.html` | Keep |
| `kundli/match.html` | Keep |
| `family/family.html` | Keep |
| `family/family_form.html` | Keep |
| `console/*` (11 templates) | Keep |
| `onboarding/*` (7 templates) | Modify — phone-first step 1 |
| `errors/*` (4 templates) | Keep |
| `main/privacy_policy.html` | Keep |
| `main/terms.html` | Keep |
| `main/success_stories.html` | Keep |

## Templates to MODIFY

| Template | Changes |
|----------|---------|
| `base.html` | Add completeness ring in navbar; add `.ij-tabs` CSS; add spacing tokens; add `@media (hover: none)` |
| `main/home.html` | Add discovery tab nav; add trust badge on cards; add match score badge; add `last_active_at` display |
| `main/my_profile.html` | Replace Bootstrap `card shadow-sm rounded-4` with `ij-card`; add sticky CTA bottom bar on mobile |
| `membership/plans.html` | Add per-day pricing; add social proof count field; add interest-remaining trigger |
| `search/search_results.html` | Add income filter to sidebar; add mobile filter trigger button |
| `connect/interests.html` | Add Viewers tab (Who Viewed Me); add Sent/Received/Accepted tabs |
| `auth/register.html` | Add phone-first registration path alongside email path |
| `profile/profile.html` | Complete replacement — tabbed AJAX editor |
| `static/css/style.css` | Add 22 missing token/component definitions; add mobile breakpoints |

## Templates to REMOVE

| Template | Reason |
|----------|--------|
| `templates/admin/analytics.html` | Deprecated admin blueprint |
| `templates/admin/assisted.html` | Deprecated |
| `templates/admin/dashboard.html` | Deprecated |
| `templates/admin/plans.html` | Deprecated |
| `templates/admin/reports.html` | Deprecated |
| `templates/admin/stories.html` | Deprecated |
| `templates/admin/users.html` | Deprecated |
| `templates/profile/name.html` | Merged into AJAX editor |
| `templates/profile/birthday.html` | Merged |
| `templates/profile/gender.html` | Merged |
| `templates/profile/looking_for.html` | Merged |
| `templates/profile/height.html` | Merged |
| `templates/profile/bio.html` | Merged |
| `templates/profile/religion.html` | Merged |
| `templates/profile/lifestyle.html` | Merged |
| `templates/profile/email.html` | Merged |
| `templates/profile/phone.html` | Merged |
| `templates/profile/professional.html` | Merged |
| `templates/profile/education.html` | Merged |
| `templates/profile/language.html` | Merged |
| `templates/profile/hobbies.html` | Merged |
| `templates/profile/nri.html` | Merged |

**Total templates after v2: 57 (down from 78)**

## Duplicate Templates (ijodidar/ subdirectory)

All 69 templates in `/ijodidar/templates/` — DELETE ENTIRE DIRECTORY.

---

# SECTION 8 — API TRANSFORMATION PLAN

## Phase 1 — Foundation (Sprint 2, Week 3-4)

**Install:**
- `Flask-JWT-Extended==4.6.0`
- `marshmallow==3.22.0`
- `marshmallow-sqlalchemy==1.1.0`
- `flask-cors==4.0.0`

**Create:** `app/api/` blueprint directory

**Endpoints — Required for Mobile App (Phase 1):**

| Endpoint | Auth | Mobile Required | Web Required |
|----------|------|----------------|-------------|
| `POST /api/v1/auth/send-otp` | None | ✅ | ✅ |
| `POST /api/v1/auth/verify-otp` | None | ✅ | ✅ |
| `POST /api/v1/auth/refresh` | Refresh token | ✅ | ✅ |
| `POST /api/v1/auth/logout` | Access token | ✅ | ✅ |
| `GET /api/v1/profiles/feed` | JWT | ✅ | Optional |
| `GET /api/v1/profiles/@<username>` | JWT | ✅ | Optional |
| `GET /api/v1/profiles/me` | JWT | ✅ | Optional |
| `POST /api/v1/interests` | JWT | ✅ | Optional |
| `GET /api/v1/interests/received` | JWT | ✅ | Optional |
| `PATCH /api/v1/interests/<id>` | JWT | ✅ | Optional |
| `GET /api/v1/conversations` | JWT | ✅ | Optional |
| `POST /api/v1/conversations/<id>/messages` | JWT | ✅ | Optional |
| `GET /api/v1/notifications/unread-count` | JWT | ✅ | ✅ (already exists) |

## Phase 2 — Complete API Surface (Sprint 3)

| Endpoint | Auth | Mobile Required |
|----------|------|----------------|
| `PATCH /api/v1/profiles/me` | JWT | ✅ |
| `POST /api/v1/profiles/photos` | JWT | ✅ |
| `GET /api/v1/profiles/completeness` | JWT | ✅ |
| `GET /api/v1/conversations/<id>/messages` | JWT | ✅ |
| `PATCH /api/v1/conversations/<id>/read` | JWT | ✅ |
| `GET /api/v1/notifications` | JWT | ✅ |
| `POST /api/v1/devices` | JWT | ✅ |
| `GET /api/v1/plans` | JWT | ✅ |
| `POST /api/v1/kundli` | JWT | ✅ |
| `GET /api/v1/kundli/match/<id>` | JWT | ✅ |
| `GET /api/v1/profiles/viewers` | JWT | ✅ |

## Phase 3 — Enhanced API (Sprint 4+)

| Endpoint | Notes |
|----------|-------|
| `POST /api/v1/plans/<id>/order` | Razorpay order via mobile |
| `DELETE /api/v1/devices/<token>` | Deregister FCM on logout |
| `GET /api/v1/search` | Search via mobile |
| `PATCH /api/v1/profiles/me/preferences` | Partner prefs via mobile |

## Standard Response Contract

All API responses follow this exact format:

```
Success:  { "success": true, "data": {...}, "meta": {...} }
Error:    { "success": false, "error": { "code": "ERROR_CODE", "message": "...", "field": "..." } }
List:     { "success": true, "data": [...], "meta": { "page": 1, "total": 142, "pages": 8 } }
```

---

# SECTION 9 — FRONTEND COMPONENT INVENTORY

## Navbar
**Classification:** REUSABLE — modify only
**Changes:** Add completeness ring; simplify mobile to logo + bell only; reduce avatar dropdown to 5 items

## Left Sidebar
**Classification:** NEEDS REDESIGN — contextual per section
**Changes:** Remove global nav links; each section owns its sidebar content via template blocks

## Bottom Navigation
**Classification:** REUSABLE — minor changes
**Changes:** Increase height from estimated 56px to 64px; ensure all 5 items have distinct active states

## Profile Cards (home feed)
**Classification:** NEEDS REDESIGN
**Changes:** Add `.ij-profile-card` CSS class; add trust badge; add match score badge; add `last_active_at` display; maintain 3:4 photo ratio

## Profile Card (search results)
**Classification:** NEEDS REDESIGN — same as home feed cards

## Forms
**Classification:** PARTIAL — `.ij-input` partially defined
**Changes:** Complete `.ij-input`, `.ij-field`, `.ij-field-error`, `.ij-select` definitions

## Modals
**Classification:** REUSABLE — keep Bootstrap modals where used
**Changes:** Replace modal pattern with bottom sheet on mobile for filters

## Toasts
**Classification:** REUSABLE — no changes needed
**Evidence:** Correctly implemented in `base.html` with auto-dismiss at 5s

## Profile Editor Sections (NEW)
**Classification:** NEW — 5 tabbed section components
**Required for:** Sprint 3 profile editor consolidation

## Guna Milan Report
**Classification:** REUSABLE — no changes needed

## Discovery Tab Nav
**Classification:** NEW — `.ij-tabs` CSS component
**Required for:** Sprint 2 discovery tabs

## Trust Badge
**Classification:** NEW — `.trust-badge` CSS component
**Required for:** Sprint 2

## Completeness Ring
**Classification:** NEW — `.completeness-ring-wrap` SVG component
**Required for:** Sprint 2

## Filter Bottom Sheet (mobile)
**Classification:** NEW — `.ij-bottom-sheet` CSS + JS component
**Required for:** Sprint 2

---

# SECTION 10 — CSS DESIGN SYSTEM MIGRATION

## Tokens to Keep (verified in style.css)

Brand, neutrals, status colors, shadow scale, radius scale, transition tokens.
Total: 28 tokens — all correct.

## Tokens to Add (missing from style.css)

```
Spacing: --space-1 through --space-16 (13 tokens)
Typography: --text-xs through --text-5xl (9 tokens)
Z-index: --z-base through --z-nav (6 tokens)
Trust: --trust-registered, --trust-phone, --trust-id, --trust-full (4 tokens)
Score: --score-low, --score-mid, --score-high (3 tokens)
Screen: --screen-sm through --screen-2xl (5 tokens)
Total missing: 40 tokens
```

## Components to Add (missing from style.css)

```
Layout: .ij-two-col, .card-grid, .ij-container (responsive)
Navigation: .ij-tabs, .ij-tab, .filter-pills, .filter-pill
Cards: .ij-profile-card, .card-photo, .card-photo-overlay, .card-info, .card-actions
Trust: .trust-badge (4 modifiers)
Completeness: .completeness-ring-wrap, .completeness-pct
Mobile: .ij-bottom-sheet, .ij-sheet-panel, .ij-sheet-handle
Forms: .ij-field, .ij-field-error, .ij-field-hint, .ij-input (complete), .ij-select
Buttons: .btn-interest, .btn-ij-icon
Safe areas: .safe-top, .safe-bottom, .safe-left, .safe-right
Touch: @media (hover: none) block, -webkit-tap-highlight-color global
Total missing: ~30 component definitions
```

## Bootstrap Dependencies to Manage

Bootstrap 5.3.3 CDN loaded in `base.html`. Used for:
grid layout, modal, carousel, dropdown, form-select, spinner, badge.

**Decision:** Keep CDN for now. In Sprint 4, download and serve locally.
Replace `my_profile.html` Bootstrap card classes with `ij-card` in Sprint 2.

## Technical Debt in CSS

- 907-line single file mixes tokens + components + Bootstrap overrides
- No CSS build process; no PostCSS; no purge
- Refactor into `tokens.css`, `components.css`, `overrides.css` in Sprint 4

---

# SECTION 11 — MOBILE READINESS ASSESSMENT

## Overall Mobile Readiness Score: 28 / 100

| Category | Score | Blocker |
|----------|-------|---------|
| Navigation | 55/100 | Bottom nav exists but overlaps content on some screens |
| Forms | 30/100 | 22 separate page loads; no native input optimization |
| Search | 10/100 | No mobile filter panel — complete failure |
| Messaging | 60/100 | SocketIO works; WebRTC works; no JWT auth |
| Profile Management | 15/100 | 22-page editor unusable on mobile |
| Photo Uploads | 40/100 | Upload works via form; no client-side preview |
| REST API | 0/100 | Does not exist |
| Push Notifications | 0/100 | FCM not implemented |
| PWA | 45/100 | Manifest + SW exist; icons unconfirmed; no offline page |
| Performance | 40/100 | No lazy loading; no pagination optimization |

### Blockers (must fix before mobile app launch)

1. REST API does not exist (entire mobile app blocked)
2. JWT authentication does not exist
3. SocketIO JWT auth path does not exist
4. FCM push notification infrastructure does not exist
5. `UserDevice` model does not exist

### Quick Wins (mobile UX improvement, no API required)

1. Fix `send_email()` synchronous call in SocketIO handler (1 hour, immediate performance gain)
2. Add income filter to search (2 hours)
3. Add `@media (hover: none)` to style.css (30 minutes)
4. Fix profile card photo ratio to 3:4 (1 hour)
5. Add completeness ring to navbar (2 hours)

### Required Redesigns (before mobile app)

1. Profile editor: 22 pages → 5-section AJAX editor
2. Search: filter sidebar → filter bottom sheet on mobile
3. Registration: email-first → phone-OTP-first

---

# SECTION 12 — SECURITY REVIEW

## Authentication Security

| Item | Status | Risk | Action |
|------|--------|------|--------|
| bcrypt password hashing | ✅ Correct | None | Keep |
| Password minimum 8 chars | ✅ Correct | Low | Add strength meter in Sprint 3 |
| Account lockout (10 fails / 30 min) | ✅ Correct | None | Keep |
| Session invalidation on password change | ✅ Correct | None | Keep |
| Email verification token expiry (24h) | ✅ Correct | None | Keep |
| Password reset token expiry (1h) | ✅ Correct | None | Keep |
| OTP stored as bcrypt hash | ✅ Correct | None | Keep |
| TOTP 2FA for console | ✅ Correct | None | Keep |
| Console lockout (5 fails / 60 min) | ✅ Correct | None | Keep |
| Console IP restriction | ✅ Correct | None | Keep |
| No JWT implementation | ❌ Missing | CRITICAL | Add Flask-JWT-Extended Sprint 2 |
| No token revocation | ❌ Missing | HIGH | Redis revocation list Sprint 2 |

## Authorization Security

| Item | Status | Risk | Action |
|------|--------|------|--------|
| CSRF protection (Flask-WTF) | ✅ Correct | None | Keep |
| IDOR prevention on image delete | ✅ Correct | None | Keep |
| IDOR prevention on conversation | ✅ Correct | None | Keep |
| IDOR prevention on interest | ✅ Correct | None | Keep |
| Staff excluded from feeds | ✅ Correct | None | Keep |
| Console RBAC (5 roles) | ✅ Correct | None | Keep |
| No API authorization (no API exists) | N/A | — | JWT in Sprint 2 |

## Data Security

| Item | Status | Risk | Action |
|------|--------|------|--------|
| S3 private ACL on uploads | ✅ Correct | None | Keep |
| Pre-signed URL expiry (1h) | ✅ Correct | None | Keep |
| Admin audit log (INSERT-only) | ✅ Correct | None | Keep |
| No PII in Sentry | ✅ Correct (`send_default_pii=False`) | None | Keep |
| Razorpay HMAC verification | ✅ Correct | None | Keep |
| Razorpay server-side order fetch | ✅ Correct | None | Keep |
| SECRET_KEY validated at startup | ✅ Correct | None | Keep |

## Critical Risk Items

| Risk | Severity | Evidence | Mitigation |
|------|----------|----------|-----------|
| Synchronous email in SocketIO handler | CRITICAL | `send_email()` in `on_send_message()` — blocks event loop | Replace with `send_message_email_task.delay()` — Sprint 1 |
| Rate limiter falls back to in-memory | HIGH | `RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')` | Ensure Redis configured in production |
| Bootstrap served from CDN | MEDIUM | base.html loads Bootstrap 5.3.3 from jsdelivr | Serve locally Sprint 4 |
| No JWT revocation list | HIGH (future) | No revocation infrastructure | Redis revocation list Sprint 2 |
| `db.session.commit()` inside model property | MEDIUM | `UserSubscription.interests_remaining()` | Refactor Sprint 1 |

---

# SECTION 13 — CELERY & REDIS ROADMAP

## Current State

9 tasks, on-demand only, Redis DB 1 as broker.
No Celery Beat. No scheduled tasks.
Structural flaw: `from wsgi import app` pattern.

## Target State

14 tasks (9 existing + 5 new), Redis DB 1 as broker.
Celery Beat process with 5 scheduled tasks.
Correct ContextTask pattern.

## New Task Definitions

```
send_daily_match_digest(user_id)     — Sprint 1
  Schedule: Daily 8:00 AM IST (02:30 UTC)
  Logic: Top 5 scored matches for user → email

check_subscription_expiry()          — Sprint 1
  Schedule: Daily 00:30 IST (19:00 UTC)
  Logic: UserSubscription.expires_at <= now() → set is_active=False

reset_monthly_interests()            — Sprint 1
  Schedule: 1st of each month 00:01 IST
  Logic: interests_this_month = 0 for all active subscriptions
  (Removes db.session.commit() from UserSubscription model property)

cleanup_expired_otps()               — Sprint 1
  Schedule: Every 30 minutes
  Logic: User.phone_otp = NULL where phone_otp_expiry <= now()

send_fcm_push_notification(user_id, title, body, data)  — Sprint 3
  Schedule: On-demand (called from routes and other tasks)
  Logic: Fetch UserDevice records → send FCM via firebase-admin

refresh_match_scores_for_user(user_id)  — Sprint 4 (optional)
  Schedule: On profile save, on preference change
  Logic: Recalculate and cache top 100 scores for user
```

## Queue Architecture

```
Queue: default          — all on-demand tasks
Queue: scheduled        — Celery Beat tasks
Queue: push             — FCM push tasks (higher priority)

Worker command: celery -A app.tasks.celery worker --queues default,scheduled,push
Beat command:   celery -A app.tasks.celery beat --schedule /tmp/celerybeat-schedule
```

## ContextTask Fix

Replace `from wsgi import app` pattern with Flask application factory binding:

```
Create flask_celery.py with make_celery(app) returning a Celery instance
where every task runs inside with app.app_context().
Register celery in app/__init__.py.
Import from flask_celery in tasks.py.
```

## Monitoring Strategy

- Celery Flower dashboard (install `flower` package)
- Failed task alerts via Sentry (already configured)
- Redis memory monitoring via AWS CloudWatch (after RDS migration)

---

# SECTION 14 — AWS INFRASTRUCTURE ROADMAP

## Current Infrastructure

Single EC2 t3.small (Mumbai, ap-south-1):
- Application (Gunicorn + gevent)
- PostgreSQL 16
- Redis
- Celery worker

Cost: ~₹957/month

## Phase 1 — Current (0-2K users): No Changes
The monolith on a single EC2 is correct.
No infrastructure changes needed until revenue > ₹25,000/month or 500+ active users.

**Immediate additions (no cost):**
- Add Celery Beat to existing Celery service file
- Configure SES production access (free up to 62K/month from EC2)
- Create S3 bucket + IAM role for EC2 (pay-per-use, ~₹150/month)
- Add UptimeRobot monitoring (free tier)

## Phase 2 — Growth (2K-10K users, ~Month 4-8)
**Trigger:** Monthly revenue > ₹25,000 OR 500+ active daily users

| Change | Service | Monthly Cost |
|--------|---------|-------------|
| PostgreSQL → RDS t3.micro | AWS RDS | +₹1,400/month |
| Redis → ElastiCache t3.micro | AWS ElastiCache | +₹1,400/month |
| Celery → separate t3.micro | EC2 t3.micro | +₹700/month |
| **New total** | | **~₹4,500/month** |

RDS migration steps:
1. Take pg_dump from EC2 PostgreSQL
2. Create RDS instance in same VPC
3. Restore dump
4. Update `DATABASE_URL` in .env
5. Restart app; verify connection
6. Stop EC2 PostgreSQL service

## Phase 3 — Scale (10K-50K users, ~Month 12+)
**Trigger:** Monthly revenue > ₹1,50,000 OR 2,000+ concurrent users

| Addition | Service | Purpose |
|----------|---------|---------|
| S3 + CloudFront CDN | CDN | Photo delivery edge cache |
| Application Load Balancer | ALB | Multiple app instances |
| Second EC2 (app) | t3.medium | Horizontal scaling |
| RDS read replica | RDS | Separate read load |
| Redis cluster | ElastiCache | SocketIO horizontal scaling |
| **New total** | | **~₹15,000/month** |

**SocketIO horizontal scaling requirement:**
When multiple app servers exist, SocketIO requires Redis pub/sub adapter.
`flask-socketio` supports this with `message_queue=redis://`.
Must configure before adding second app server.

## Disaster Recovery

| Component | Backup Strategy | RTO | RPO |
|-----------|----------------|-----|-----|
| PostgreSQL | Daily pg_dump to S3 | 2 hours | 24 hours |
| S3 photos | Cross-region replication (S3 CRR) | Minutes | Minutes |
| Redis | No persistence needed — rate limits are ephemeral | — | — |
| Application code | GitHub + deployment script | 30 minutes | — |

## Monitoring Stack

| Tool | Purpose | Cost |
|------|---------|------|
| Sentry | Error monitoring, performance traces | Free tier |
| UptimeRobot | Uptime alerts | Free tier |
| AWS CloudWatch | EC2 CPU/memory alerts | Free tier |
| Celery Flower | Task queue monitoring | Free (self-hosted) |

---

# SECTION 15 — DEVELOPMENT ROADMAP

## Pre-Sprint 0 — Immediate Actions (Week 1, Before Any Feature Work)

These must complete before Sprint 1 begins:

| Action | Effort | Risk |
|--------|--------|------|
| Delete `/ijodidar/` subdirectory | S | LOW — dead code |
| Remove `app/admin/` blueprint + templates | S | LOW — all redirect |
| Fix: `send_email()` → `send_message_email_task.delay()` in socket_events.py | S | LOW — bug fix |
| Fix: Remove `db.session.commit()` from `UserSubscription.interests_remaining()` | S | LOW — refactor |
| Wire income filter in search/routes.py | S | LOW — 2-hour fix |
| Remove duplicate `check_gotra_compatibility` from utils_kundli.py | S | LOW — cleanup |
| Confirm PWA icons exist at expected paths | S | LOW — verify |

**These 7 actions can be completed in 1 working day.**

---

## Sprint 1 — Foundation (Weeks 2-3)

**Objective:** Stabilise existing platform; add Celery Beat; fix critical UX gaps.

**Deliverables:**

| Item | Effort | Dependencies |
|------|--------|-------------|
| Celery ContextTask pattern fix | S | None |
| Celery Beat configuration (5 scheduled tasks) | M | ContextTask fix |
| Daily match email task | M | Celery Beat |
| Subscription expiry task | S | Celery Beat |
| Monthly interest reset task | S | Celery Beat |
| OTP cleanup task | S | Celery Beat |
| `User.last_active_at` column + before_request update | S | Migration |
| `PartnerPreference` income + religion columns | S | Migration |
| Phone-first registration flow | M | None |
| Trust tier properties on User model | S | None |
| Completeness ring in navbar | S | None |
| Profile completeness cached to `profiles.completeness_pct` | S | None |

**Expected outcomes:**
- Re-engagement from daily emails begins (40% lift in returning users)
- Subscription revenue protected by auto-expiry
- Registration drop-off reduced from 60% to 35%

---

## Sprint 2 — Discovery + Conversion (Weeks 4-5)

**Objective:** Fix the three discovery gaps; improve conversion mechanics.

**Deliverables:**

| Item | Effort | Dependencies |
|------|--------|-------------|
| Discovery tabs in home feed (Best/New/Mutual/Near) | M | last_active_at (Sprint 1) |
| Who Viewed Me in Interests tabs | S | ProfileView model (exists) |
| Trust tier badge on profile cards | S | User.trust_tier (Sprint 1) |
| Match score badge on profile cards | S | None |
| Per-day pricing on plans page | S | None |
| Social proof field + display on plans | S | None |
| Interest-remaining counter in feed | S | None |
| Mobile filter bottom sheet for search | M | None |
| CSS design system completion (40 missing tokens, 30 components) | M | None |
| Replace Bootstrap classes in my_profile.html | S | CSS work |
| REST API foundation: install JWT + Marshmallow | S | None |
| `app/api/` blueprint: Phase 1 endpoints (13 endpoints) | L | JWT installed |
| SocketIO JWT auth path | M | JWT installed |

**Expected outcomes:**
- Profile conversion from "view" to "interest" improves 25-40%
- Plans page conversion improves 15-20%
- REST API Phase 1 complete — mobile app development can begin

---

## Sprint 3 — Profile Editor + API Complete (Weeks 6-7)

**Objective:** Replace the 22-page profile editor; complete the REST API.

**Deliverables:**

| Item | Effort | Dependencies |
|------|--------|-------------|
| Unified profile editor template (5 AJAX sections) | L | AJAX endpoints |
| `POST /api/profile/about` AJAX endpoint | M | None |
| `POST /api/profile/career` AJAX endpoint | M | None |
| `POST /api/profile/family` AJAX endpoint | M | None |
| `POST /api/profile/photos` AJAX endpoint | M | None |
| `POST /api/profile/preferences` AJAX endpoint | M | None |
| `GET /api/profile/completeness` endpoint | S | None |
| Redirect all 22 old profile routes | S | New editor live |
| REST API Phase 2: complete surface (11 more endpoints) | L | Sprint 2 API |
| UserDevice model + FCM infrastructure | M | firebase-admin |
| FCM push task | M | UserDevice model |
| `FamilyDetails.consent_given` column | S | Migration |

**Expected outcomes:**
- Profile completion rate increases from <20% to 60%+
- REST API complete — React Native development can begin
- Push notifications operational for mobile

---

## Sprint 4 — Optimisation + Mobile Polish (Weeks 8-9)

**Objective:** Performance; message improvements; annual plan; mobile polish.

**Deliverables:**

| Item | Effort | Dependencies |
|------|--------|-------------|
| Context processor Redis caching (3 queries → cache) | M | Redis |
| Message soft-delete (deleted_for_user1/2) | M | Migration |
| Annual membership plan | M | Razorpay |
| Bootstrap served locally (remove CDN) | S | None |
| PWA offline page | S | None |
| Aadhaar KYC live (Surepass API key) | S | Business |
| N+1 fix: joinedload on search results for images | S | None |
| ProfileView daily unique index | S | Migration |

---

## Sprint 5 — Mobile App (Weeks 10-12)

**Objective:** React Native app (Android + iOS).

**Deliverables:**

| Item | Effort | Dependencies |
|------|--------|-------------|
| React Native project setup (Expo) | S | Sprint 2-3 API |
| Auth flow (phone OTP → JWT) | M | API Sprint 2 |
| Home feed (profile cards, discovery tabs) | M | API Sprint 2 |
| Profile view | M | API Sprint 2 |
| Interest send/accept | M | API Sprint 2 |
| Chat (SocketIO JWT) | M | SocketIO JWT Sprint 2 |
| Push notifications (FCM) | M | Sprint 3 FCM |
| Profile editor (5 sections) | M | API Sprint 3 |
| Kundli / Guna Milan | S | API Sprint 3 |
| Play Store submission | S | Android build |
| App Store submission | S | iOS build |

---

## Sprint 6 — Scale & Polish (Month 3+)

**Objective:** Infrastructure maturity; match score caching; competitive features.

**Deliverables:**

| Item | Effort |
|------|--------|
| RDS migration (PostgreSQL → AWS RDS) | M |
| Match score pre-computation + Redis cache | M |
| Celery Flower monitoring dashboard | S |
| Models.py split into domain files | L |
| PartnerPreference multi-religion matching | M |
| Mutual shortlist detection | S |
| Interest expiry (30-day pending limit) | S |

---

# SECTION 16 — DEPLOYMENT STRATEGY

## Local Testing Plan

```
1. Extract project zip
2. pip install -r requirements.txt
3. set FLASK_APP=wsgi.py (Windows) / export FLASK_APP=wsgi.py (Mac/Linux)
4. flask db upgrade
5. python seed.py
6. python wsgi.py → http://localhost:5000

SQLite used automatically when DATABASE_URL is empty.
No PostgreSQL, Redis, or AWS required for local testing.
```

## QA Plan

Before every sprint merge:
1. All 7 pre-sprint actions verified
2. TESTING_CHECKLIST.md — all 55 checks pass
3. No 500 errors in server logs
4. Kundli API returns correct Nadi (Ashwini × Ardra → Nadi Dosha)
5. Income filter returns filtered results

## Staging Plan

Staging environment: EC2 t3.micro (separate from production).
Deploy to staging from `staging` git branch.
Test all sprint deliverables on staging before production.

## Production Deployment

```
ssh -i key.pem ubuntu@13.205.222.218
cd ~/ijodidar && git pull origin main
source venv/bin/activate
pip install -r requirements.txt -q
flask db upgrade
sudo systemctl restart ijodidar ijodidar-celery ijodidar-beat
sudo systemctl status ijodidar
```

## Rollback Plan

1. `git revert HEAD` for code issues
2. `flask db downgrade -1` for migration issues
3. Restore from pre-deployment pg_dump for data issues
4. Celery Beat: `sudo systemctl stop ijodidar-beat` if tasks cause issues

---

# SECTION 17 — RISK REGISTER

| # | Risk | Impact | Probability | Mitigation | Priority |
|---|------|--------|-------------|-----------|---------|
| R01 | Income filter fix breaks search pagination | MEDIUM | LOW | Test with `LIMIT 20`; verify paginator |  P1 |
| R02 | Celery ContextTask refactor breaks existing tasks | HIGH | MEDIUM | Test all 9 tasks after fix; run in dev mode first | P0 |
| R03 | Phone-first registration loses email-registered users | LOW | LOW | Keep email path; phone is addition, not replacement | P1 |
| R04 | Profile editor consolidation breaks existing profile data | HIGH | MEDIUM | Keep old routes as redirects; data model unchanged | P0 |
| R05 | JWT token security misconfiguration | CRITICAL | LOW | Use Flask-JWT-Extended defaults; Redis revocation | P0 |
| R06 | models.py split breaks all imports | CRITICAL | HIGH | Only do after full test suite exists; do last | P2 |
| R07 | Daily email task sends duplicate emails | MEDIUM | MEDIUM | Idempotency check: last_digest_sent column | P1 |
| R08 | SocketIO JWT auth breaks web users | HIGH | LOW | Add JWT path alongside session; not replacing | P0 |
| R09 | S3 bucket not configured; photo uploads return error | HIGH | MEDIUM | Guard in upload function (already implemented) | P1 |
| R10 | Subscription expiry task runs in wrong timezone | HIGH | LOW | Use UTC; IST conversion only for email display | P1 |
| R11 | Celery Beat double-fires on restart | MEDIUM | MEDIUM | Use file-based beat schedule; not database | P1 |
| R12 | RDS migration data loss | CRITICAL | LOW | Full pg_dump before; verify row counts after | P0 |
| R13 | FCM token rotation invalidates push | LOW | HIGH | Delete on `messaging/registration-token-refresh` | P2 |
| R14 | React Native app store rejection | MEDIUM | MEDIUM | Review Apple/Google matrimony guidelines in advance | P1 |

---

# SECTION 18 — FINAL RECOMMENDED BUILD ORDER

## DO FIRST — Pre-Sprint 0 (This Week)

All items complete in 1 working day. No risk. Immediate benefit.

1. Delete `/ijodidar/` subdirectory
2. Remove `app/admin/` blueprint + 7 templates
3. Fix `send_email()` → `send_message_email_task.delay()` in socket_events.py
4. Remove `db.session.commit()` from `UserSubscription.interests_remaining()`
5. Wire `income_lpa` filter in `app/search/routes.py`
6. Remove duplicate `check_gotra_compatibility` definition in utils_kundli.py
7. Add `User.last_active_at` column + migration

## DO NEXT — Sprint 1-2 (Weeks 2-5)

Highest revenue impact. Lowest migration risk.

8. Celery ContextTask pattern fix
9. Celery Beat + 5 scheduled tasks (daily digest, expiry, reset, cleanup)
10. Phone-first registration (alongside, not replacing email)
11. Trust tier properties on User (no migration needed)
12. Completeness ring in navbar (template only)
13. PartnerPreference income + religion columns (migration)
14. Discovery tabs in home feed
15. Who Viewed Me in Interests tabs
16. Trust tier + match score badges on profile cards
17. Per-day pricing + social proof on plans page
18. Mobile filter bottom sheet
19. CSS design system completion (tokens + components)
20. REST API Phase 1 (JWT + 13 endpoints)
21. SocketIO JWT auth path

## DO LATER — Sprint 3-4 (Weeks 6-9)

Larger effort; depends on Sprint 1-2 being stable.

22. Unified profile editor (22 pages → 5 AJAX sections)
23. REST API Phase 2 (complete surface)
24. FCM push + UserDevice model
25. Context processor Redis cache
26. Message soft-delete
27. Annual membership plan
28. Bootstrap local serving

## DO NOT BUILD YET

These add complexity without proportional value at current scale.

| Item | Reason |
|------|--------|
| models.py domain split | Requires full test suite; massive blast radius |
| Match score caching (Redis/table) | Not needed until 5K+ users |
| Saved searches | Low value; build in v3 |
| Reverse matches | High complexity; low usage |
| Private profile mode | Build after 1K users confirm demand |
| Photo watermark | Low priority |
| Background verification (AuthBridge) | Business cost decision |
| WhatsApp business API | Meta review takes 2+ weeks; configure when ready |
| Video matrimony events | Too early; stabilise core first |
| Swipe-card gesture (Tinder-style) | Off-brand for matrimony; do not build |

---

CHECKPOINT_STATUS
Current Phase: D — Master Migration Blueprint
Current Section: iJodidar_v2_Migration_Blueprint.md Complete (18 Sections)
Completed: Phase 0 (3), Phase A (1), Phase B (1), Phase C (1), Phase C2 (1), Phase D Blueprint (1)
Remaining: 8 Architecture Documents
Files Generated: 8
Progress Percent: 62%
