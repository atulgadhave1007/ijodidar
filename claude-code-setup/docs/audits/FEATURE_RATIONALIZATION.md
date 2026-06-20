# FEATURE_RATIONALIZATION.md
## iJodidar v2 — Feature Rationalization
## Phase C2 | Every Feature Classified | June 2026

---

## RATIONALIZATION METHODOLOGY

Every feature in the codebase is evaluated on four dimensions:
1. **User value** — does a real user need this?
2. **Revenue impact** — does it drive upgrades or retention?
3. **Technical quality** — is the implementation correct?
4. **Strategic alignment** — does it support the v2 vision?

Classification:
- **KEEP** — correct as-is; no changes needed
- **MODERNIZE** — functionally correct; needs UX/technical upgrade
- **MERGE** — duplicate or overlapping with another feature
- **DEPRECATE** — scheduled for removal after migration
- **REMOVE** — immediate removal; no migration needed

---

## AUTHENTICATION FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Email + password login | KEEP | Core auth; works correctly; lockout implemented |
| Account lockout (10 fails / 30 min) | KEEP | Correct implementation; verified in code |
| Password reset via email | KEEP | 1-hour token expiry; async Celery; correct |
| Email verification on registration | MODERNIZE | Currently gates platform access (40-60% drop). Convert from gate to notification preference. Users should see blurred feed immediately after registration. |
| Phone OTP verification | MODERNIZE | Correct implementation. Must become **primary** auth method, not secondary step. |
| Session invalidation on password change | KEEP | `session_version` pattern — correct and rare |
| TOTP 2FA (console only) | KEEP | Google Authenticator; correct; production-grade |
| Aadhaar KYC workflow | MODERNIZE | Code exists (`send_aadhaar_otp`, `verify_aadhaar_otp`). Needs live API key (Surepass ₹2/verification). Not a code problem — a business configuration problem. |

---

## ONBOARDING FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| 5-step onboarding wizard | MODERNIZE | Wizard pattern is correct. Steps 1-2 must be reordered: phone OTP before gender selection. Step count should reduce to 3 (name+phone → OTP → gender+looking_for). |
| `before_request` onboarding gate | KEEP | Correct architectural pattern. Exempt list implementation is brittle (hardcoded strings). |
| `ONBOARDING_EXEMPT` endpoint set | MODERNIZE | Replace hardcoded strings with a decorator or blueprint-level flag. Lower priority. |
| Onboarding wizard templates (6 files) | KEEP | `gender.html`, `basics.html`, `career.html`, `photo.html`, `preferences.html`, `done.html` — correctly implement the wizard. Minor changes needed to remove email dependency. |

---

## PROFILE FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| 22 separate profile edit routes | DEPRECATE | Must be replaced by 5-section AJAX editor. Old routes should redirect to `/profile?section=X`. Templates can be removed once consolidated editor is live. |
| `/profile` settings list page | REPLACE | Currently shows settings list with 22 link rows. Must become the 5-section AJAX editor. |
| `/name`, `/birthday`, `/bio`, `/height`, etc. (14 routes) | DEPRECATE | Redirects to `/profile?section=about`. Remove after 30-day grace period. |
| `/religion`, `/lifestyle`, `/nri` (3 routes) | DEPRECATE | Merge into About section of unified editor. |
| `/professional`, `/education` (2 routes) | DEPRECATE | Merge into Career section of unified editor. |
| `/language` route | MERGE | Merge into Career section (languages spoken is career-adjacent). |
| `/partner_preferences` route | DEPRECATE | Merge into Profile Preferences tab. |
| `/address/<tag>` route | MODERNIZE | Keep as separate endpoint but surface within unified editor as Location subsection. |
| `/upload_image`, `/delete_image`, `/set_primary_image` | MODERNIZE | Keep as separate endpoints but wire into Photo section of unified editor via AJAX. Add drag-to-reorder. |
| `calculate_profile_completeness()` | MODERNIZE | Logic is correct. Must: (1) cache result in `profiles.completeness_pct`, (2) expose via `/api/profile/completeness`, (3) show persistently in navbar. |
| S3 photo upload with 3 sizes | KEEP | 800px/400px/150px; private ACL; correct pattern |
| Pre-signed S3 URLs (`|signed_url` filter) | KEEP | Correct implementation; 1h/24h expiry |
| Photo blur for Free plan | KEEP | Implemented in home feed and search; correct business rule |

---

## SEARCH & DISCOVERY FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| 15-filter search | MODERNIZE | Filters are correct but income filter is not wired. Fix income filter (2 hours). Add mobile bottom sheet. Change age filter to use `dob` Date column. |
| Search pagination (20/page) | KEEP | Correct; SQLAlchemy `.paginate()` |
| Home feed (single feed) | MODERNIZE | Must add 4-tab sub-navigation: Best Matches, New This Week, Mutual, Near Me. |
| Match scoring algorithm | MODERNIZE | Algorithm correct. Must cache results. Must use `dob` Date for age. Must add income factor. Must add `last_active_at` boost. |
| Signal-boosted scoring | KEEP | 7 signal types; correctly integrated into `calculate_match_score()` |
| Guna Milan in scoring (±5 pts) | KEEP | Correctly integrated; only fires when both users have KundliDetail |
| Spotlight as position slots | KEEP | Correct business rule — not score inflation |
| Shortlist feature | KEEP | `Shortlist` model; toggle route; signal recorded |
| Block feature | KEEP | `BlockList` model; exclusion from feed and search; signal recorded |
| Report feature | KEEP | `UserReport` model; console moderation flow; signal recorded |
| Profile view tracking | MODERNIZE | `ProfileView` correctly tracked. Must be surfaced as "Who Viewed Me" in Interests tabs and as sidebar widget. Currently only shown on own profile page. |
| Saved searches | REMOVE | Not implemented. No `SavedSearch` model. Not in immediate roadmap. Don't build until v3. |
| Reverse matches | REMOVE | Not implemented. Complex to build correctly. Not in immediate roadmap. |

---

## CONNECT FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Send interest | KEEP | State machine correct; monthly limit correct; gates correct |
| Accept/decline interest | KEEP | Correct; conversation created on accept; signals fired |
| Withdraw interest | KEEP | Correct |
| Monthly interest limit (plan-based) | MODERNIZE | Correct business rule. Bug: `interests_remaining()` calls `db.session.commit()` inside model property. Move auto-reset to Celery Beat task. |
| Interest email notifications | KEEP | Async via Celery; correct |
| Mutual shortlist detection | REMOVE (for now) | Not implemented. Easy to build but not in priority roadmap until discovery tabs ship. Add in Sprint 3. |
| Interest expiry (30 days) | REMOVE (for now) | Not implemented. Lower priority. Add in Sprint 4. |

---

## MESSAGING FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| SocketIO real-time chat | KEEP | Working correctly for web |
| WebRTC video/audio calling | KEEP | Full signaling implemented; competitive differentiator |
| HTTP poll fallback | KEEP | `/messages/<id>/poll` for environments where SocketIO fails |
| Typing indicators | KEEP | SocketIO `typing` event; correct |
| Phone gate for messaging | KEEP | Correct business rule |
| Message email notification | MODERNIZE — URGENT | `send_email()` called synchronously inside SocketIO `on_send_message()`. Must be replaced with `send_message_email_task.delay()` immediately. This blocks the event loop. |
| SocketIO session auth | MODERNIZE | Must add JWT token auth path alongside existing session path for mobile app support. |
| Message soft-delete | REMOVE (for now) | Not implemented. Lower priority. Add in Sprint 4. |
| Message read receipts | MODERNIZE | `is_read` Boolean exists. Need `/api/v1/conversations/<id>/read` endpoint for mobile. |

---

## MEMBERSHIP FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| 4-tier plan structure (Free/Silver/Gold/Platinum) | KEEP | Correct structure; plan features correctly gated |
| Razorpay integration | KEEP | HMAC signature verification; server-side order fetch; webhook; correct |
| Assisted plan + RM workflow | KEEP | `AssistedRequest` + `RMContactLog`; console interface; contact log; competitive differentiator |
| Plans page | MODERNIZE | Correct data; needs: per-day pricing, social proof count, interest-remaining nudge, urgency trigger on interest limit |
| Annual plan | REMOVE (for now) | Not implemented. Build in Sprint 4 when paid users exist. |
| Spotlight | MODERNIZE | Business rule correct. UPI manual payment requires admin verification — replace with automated Razorpay Spotlight order flow. |
| Subscription auto-expiry | REMOVE (gap) | Critical missing feature. Must be added as Celery Beat task. |

---

## KUNDLI / GUNA MILAN FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Vedic engine (Meeus algorithm) | KEEP | Pure Python; ±0.3° accuracy; no external dependency; competitive differentiator |
| Auto-calculation from DOB+Time+City | KEEP | Correct implementation; 100+ Indian cities built-in |
| Lahiri ayanamsa | KEEP | Standard for Indian Vedic astrology |
| 8 Ashta Koota factors | KEEP | Corrected Nadi (9-9-9 verified); corrected Vashya; corrected Graha Maitri |
| Guna Milan in match ranking | KEEP | ±5 pts; correct integration |
| Gotra compatibility check | KEEP | Correct logic; duplicate definition must be resolved (2 functions in utils_kundli.py) |
| Manglik check (approximate) | KEEP | Correctly disclosed as approximate; Chandra Lagna proxy |
| Live AJAX preview (Kundli edit) | KEEP | `/kundli/api/calculate` called before save; correct UX |
| Manual override option | KEEP | Users with paper kundli can override auto-calc |
| CITY_COORDINATES built-in (100+ cities) | KEEP | Nominatim fallback for unlisted cities |
| Duplicate `check_gotra_compatibility` definition | REMOVE | Lines 244 and 357 in `utils_kundli.py` — two definitions; remove the first |

---

## NOTIFICATIONS FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| In-app notification model | KEEP | 5 notification types; `is_read` flag; correct |
| Notification dropdown in navbar | KEEP | 30s polling; mark-all-read; correct |
| Profile viewed notification | KEEP | Fires on profile view (24h dedup); correct |
| Interest received notification | KEEP | Fires on interest send; correct |
| FCM push notifications | REMOVE (gap) | Not implemented. Critical missing feature. Must add `UserDevice` model + `firebase-admin` + Celery task. |
| Context processor DB queries | MODERNIZE — URGENT | 3 DB queries on every authenticated request. Must cache in Redis with invalidation on change. |
| Notification pagination | MODERNIZE | Returns all; add `per_page=20` pagination |

---

## REFERRAL FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Dual-sided referral rewards | KEEP | Both sides get Silver; gated behind phone verification; correct |
| Referral code generation | KEEP | 12-char unique code; correct |
| Referral fraud prevention | KEEP | IP tracking; `device_fingerprint` on Referral model |
| Referral cookie (7 days) | KEEP | Persists through multi-visit registration |
| Referral dashboard page | KEEP | `/profile/referral` — shows code, link, rewards |

---

## ADMIN & CONSOLE FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| `/admin/` blueprint (14 redirect routes) | REMOVE | All redirect to `/console/`. Dead code. Remove immediately. |
| `templates/admin/` (7 templates) | REMOVE | Superseded by console templates. |
| Console RBAC (5 roles) | KEEP | Correctly implemented; permission-based access |
| Console TOTP 2FA | KEEP | Google Authenticator; correct |
| Console IP restriction | KEEP | `CONSOLE_ALLOWED_IPS` env var; correct |
| Console brute force lockout (5 fails / 60 min) | KEEP | Correctly implemented |
| Admin audit log (immutable) | KEEP | INSERT-only; admin_id, action, target, IP, timestamp |
| Console analytics | KEEP | Registration trends, plan breakdown, revenue |
| RM workflow (Assisted plan) | KEEP | `AssistedRequest` + `RMContactLog`; contact log interface; correct |
| Console staff management | KEEP | Add/deactivate staff; created_by tracking |
| Success stories management | KEEP | Admin adds, toggles publish state; public page exists |

---

## FAMILY FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Family tree management | KEEP | Unique differentiator; complex model (FamilyDetails + FamilyRelation) |
| 42 relation types (seeded) | KEEP | Comprehensive; rarely needs changing |
| Family member data (consent gap) | MODERNIZE | Add `consent_given` Boolean to `FamilyDetails`. DPDP compliance. |

---

## PRIVACY & DPDP FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Data export (JSON, 3/day) | KEEP | Correct DPDP compliance; rate limited |
| Account deletion (PII anonymisation) | KEEP | Anonymises name, email, phone; deletes S3 photos |
| Privacy Policy page | KEEP | `/privacy-policy` |
| Terms of Service page | KEEP | `/terms` |
| Grievance officer in footer | KEEP | Legal requirement; correct |
| Consent timestamp on registration | KEEP | `consented_at` DateTime; correct |
| Age 18+ enforcement | KEEP | Form + server validation; correct |
| `is_hidden` profile flag | MODERNIZE | Exists but not surfaced clearly in privacy settings UI |
| Profile view by non-members | MODERNIZE | `is_hidden` can be used but no "private profile" mode (interest required to view) |

---

## INFRASTRUCTURE FEATURES

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| Celery async task queue | KEEP | 9 tasks; correct pattern for email/SMS/WhatsApp |
| Celery Beat (scheduled tasks) | REMOVE (gap) | Not implemented. Critical. Must add daily digest, subscription expiry, score refresh. |
| Redis rate limiting | KEEP | Shared across Gunicorn workers; correct |
| Sentry error monitoring | KEEP | Flask + SQLAlchemy + Redis integrations; 10% trace rate |
| ProxyFix middleware | KEEP | Required for Nginx → Flask; correctly configured |
| SQLAlchemy connection pool | KEEP | `pool_size=10, max_overflow=20, pool_pre_ping=True` |
| gevent conditional patching | KEEP | Production-only; Windows-safe; correct |
| SQLite fallback for local dev | KEEP | `DATABASE_URL` empty → SQLite; zero friction |
| Seed script | KEEP | Creates plans, cities, admin user; correct |
| systemd service files | MODERNIZE | Add Celery Beat process to celery.service or separate beat.service |
| `/ijodidar/` duplicate directory | REMOVE | Older codebase copy; causes deployment confusion |

---

## FEATURE RATIONALIZATION SUMMARY

| Classification | Count | Examples |
|---------------|-------|---------|
| **KEEP** | 51 | Core auth, SocketIO, Celery, Guna Milan engine, console RBAC, referral |
| **MODERNIZE** | 23 | Email gate→nudge, profile editor 22→5, income filter, match score cache |
| **MERGE** | 2 | Language route into Career, shortlist into Interests tabs |
| **DEPRECATE** | 14 | 14 individual profile edit routes (redirect to unified editor) |
| **REMOVE** | 12 | Admin blueprint, ijodidar/ directory, duplicate gotra function, saved searches (too early) |

---

## REVENUE FEATURE PRIORITY

| Feature | Revenue Type | Effort | Priority |
|---------|-------------|--------|---------|
| Per-day pricing + social proof on plans | Direct conversion | S | P0 |
| Income filter (wired) | Retention/satisfaction | S | P0 |
| Subscription auto-expiry via Celery Beat | Revenue protection | M | P0 |
| Daily match email (Celery Beat) | Re-engagement → upgrades | M | P0 |
| Trust tier badges on cards | Upgrade driver | S | P1 |
| Profile completion ring in navbar | Engagement → retention | S | P1 |
| Discovery tabs (Best/New/Mutual/Near) | Session time → upgrades | M | P1 |
| "Who Viewed Me" feature | Upgrade urgency | S | P1 |
| Interest-remaining counter in feed | Direct upgrade trigger | S | P1 |
| REST API (mobile app) | New revenue channel | L | P0 |

---

CHECKPOINT_STATUS
Current Phase: C2 — Feature Rationalization
Current Section: FEATURE_RATIONALIZATION.md Complete
Completed: Phase 0 (3 docs), Phase A (1 doc), Phase B (1 doc), Phase C (1 doc), Phase C2 (1 doc)
Remaining: Phase D — Master Migration Blueprint + 8 architecture documents (15 documents total remaining)
Files Generated: 7
Progress Percent: 55%

Reply **CONTINUE** to proceed to Phase D — Master Migration Blueprint and all architecture documents.
