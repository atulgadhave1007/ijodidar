# REDESIGN_ALIGNMENT_REPORT.md
## iJodidar v2 — Redesign Document Alignment Analysis
## Phase B | Comparing Current Implementation Against All 8 Redesign Documents
## June 2026

---

## METHODOLOGY

Each of the 8 redesign documents is compared against verified codebase findings from Phase A.
Every item is classified as:
- **ALREADY IMPLEMENTED** — exists in code, working
- **PARTIALLY IMPLEMENTED** — exists but incomplete or incorrectly implemented
- **MISSING** — specified in redesign, absent from codebase
- **CONFLICTING** — redesign conflicts with current implementation requiring a deliberate choice
- **DEPRECATED** — in codebase but not in redesign (should be removed)

---

## DOCUMENT 1 — MASTER PRODUCT REDESIGN

### Already Implemented

| Item | Evidence |
|------|----------|
| Design tokens in CSS (`--brand`, `--surface`, `--shadow-*`) | `static/css/style.css` lines 1-50 |
| Bottom navigation (5 tabs) | `templates/base.html` — `#ij-bottom-nav` element |
| Frosted-glass navbar with scroll elevation | `static/css/style.css` + JS in `base.html` |
| Toast notification system | `base.html` — `#toast-stack`, auto-dismiss at 5s |
| SocketIO real-time messaging | `app/messaging/socket_events.py` |
| WebRTC video/audio calling | `socket_events.py` — webrtc_offer, answer, ICE events |
| Signal-boosted match scoring | `app/utils.py` — `get_signal_boost()` called inside `calculate_match_score()` |
| Guna Milan with corrected Vedic data | `app/utils_kundli.py` — corrected Nadi 9-9-9 verified |
| Photo blur for Free plan users | `templates/main/home.html` — `plan_can_view_photos` check |
| Spotlight as position slots | `app/membership/routes.py` — spotlight_buy_manual logic |
| Admin audit log (immutable) | `AdminAuditLog` model, INSERT-only design |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| Navigation architecture | Top nav + sidebar + bottom nav all present | 3 separate systems cause confusion; sidebar not contextual |
| Profile card design | Cards exist in home.html with photo, name, info | No trust badge; inconsistent between home feed and profile view |
| Discovery redesign | Single home feed only | No tab sub-navigation (Best/New/Mutual/Near) |
| Membership conversion | Plans page exists | No per-day pricing, no social proof count, no urgency nudge |
| Trust signal system | `id_verified` Boolean on Profile | Not computed as tier; not shown on cards |
| Onboarding wizard | 5-step wizard exists | Step 1 still requires email verification first; not phone-first |
| Profile completeness | `calculate_profile_completeness()` exists | Not shown persistently in navbar; ring not implemented |

### Missing

| Item | Redesign Specification | Priority |
|------|----------------------|---------|
| Phone-first registration | OTP → account created → value immediately | P0 |
| Per-day pricing on plans page | "₹16/day" beneath ₹499/month | P1 |
| Social proof on plans | "247 members upgraded this week" | P1 |
| Interest remaining counter in feed | "2 interests left this month" persistent nudge | P1 |
| Completeness ring in navbar | Persistent ring visible on every page | P1 |
| Who Viewed Me surface | Tracked in DB but never shown to users | P1 |
| Discovery tabs (Best/New/Mutual/Near) | Not implemented | P1 |
| Trust tier badge on profile cards | No `.trust-badge` component | P1 |
| Contextual sidebar (different per section) | Sidebar is static across all sections | P1 |
| Profile photo aspect ratio 3:4 | Current: square/undefined ratio | P2 |
| Swipe gestures on cards | Not implemented | P2 |
| Pull-to-refresh on feed | Not implemented | P2 |
| Infinite scroll | Currently paginated | P2 |

### Conflicting

| Conflict | Current State | Target State | Recommendation |
|----------|--------------|--------------|----------------|
| Email as primary verification gate | Email verification required before any profile access | Phone OTP as primary, email as notification preference | Migrate to phone-first. Breaking change to registration flow. |
| Sidebar as global navigation | Same sidebar component renders across all sections | Contextual sidebar per section (different content each time) | Redesign sidebar using block-level template override per section. |
| Profile card visual language | `my_profile.html` uses Bootstrap `card shadow-sm rounded-4` | All cards use iJodidar `ij-card` design system | Replace Bootstrap card classes in `my_profile.html`. |

### Deprecated

| Item | Current Location | Action |
|------|-----------------|--------|
| `/admin/` blueprint (all redirects) | `app/admin/routes.py` | REMOVE — 14 routes + 7 templates |
| `/ijodidar/` directory | Repository root | REMOVE |
| Hover-only states without active states | `style.css` | Replace with `:active` equivalents |

---

## DOCUMENT 2 — NAVIGATION ARCHITECTURE

### Already Implemented

| Item | Evidence |
|------|----------|
| 5-tab bottom navigation | `base.html` — `#ij-bottom-nav` with Home, Search, Interests, Messages, Profile |
| Bottom nav active state via endpoint check | `{{ 'active' if request.endpoint == '...' }}` |
| Badge on interests and messages tabs | `{% if pending_interests > 0 %}`, `{% if unread_messages > 0 %}` |
| Avatar dropdown with user info header | `base.html` — `.dropdown` block with plan chip |
| Notification dropdown in navbar | `base.html` — `#notifBtn` with dropdown panel |
| Top navbar fixed with frosted glass | `#ij-nav` — `position:fixed`, `backdrop-filter:blur` |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| 3-breakpoint navigation | Mobile bottom nav + desktop sidebar exist | Tablet (768-1023px) has no dedicated nav behaviour — shows sidebar |
| Bottom nav 64px height | Current: 56px (estimated from style.css) | Redesign spec: 64px for larger touch targets |
| Avatar dropdown | Contains 11 items | Redesign: 5 items + utility only; Interests/Family/Messages should NOT be in dropdown |
| Active state consistency | Some endpoints checked, not all | `messaging.inbox` check uses `'messaging' in (request.endpoint or '')` — string contains, not exact match |

### Missing

| Item | Specification | Priority |
|------|--------------|---------|
| Mobile top bar: logo + bell only | Mobile top nav should hide all icon buttons, show only logo + bell | P1 |
| Contextual sidebar (per section) | Sidebar content changes per section — not a global nav | P1 |
| Tab navigation component `.ij-tabs` | CSS class and HTML pattern not in `style.css` | P1 |
| Filter pill row for mobile search | Horizontal scrollable pill row for active filters | P1 |
| Clean URL: `/@username` for public profile | Currently `/<username>` — potential route conflicts | P2 |
| Language toggle moved to avatar utility | Currently a form inside dropdown | P2 |
| Kundli/Guna Milan in utility nav | Not in avatar dropdown | P2 |

### Conflicting

| Conflict | Current | Target | Recommendation |
|----------|---------|--------|----------------|
| Avatar dropdown scope | 11 items including Interests, Family, Messages | 5 account-level items only | Remove nav items from dropdown; they exist in primary navigation already |
| Shortlist in bottom nav | Shortlist accessible from sidebar only (not bottom nav) | Redesign places shortlist under Interests tab | Merge Shortlist into `/interests?tab=saved` |
| Search in sidebar AND bottom nav | Search appears in both desktop sidebar and bottom nav | Bottom nav is single source of truth for mobile | Remove Search from sidebar; sidebar is contextual on desktop only |

---

## DOCUMENT 3 — PROFILE MANAGEMENT REDESIGN

### Already Implemented

| Item | Evidence |
|------|----------|
| Profile model with 40+ fields | `app/models.py` — Profile class |
| `income_lpa` Integer column | `ProfessionalDetails.income_lpa` |
| `dob` Date column (alongside legacy String) | `Profile.dob = db.Column(db.Date, nullable=True, index=True)` |
| KundliDetail separate from Profile | Confirmed — separate model, separate route |
| PartnerPreference as separate model | Confirmed |
| Profile completeness scoring function | `calculate_profile_completeness()` in utils.py |
| S3 photo upload with 3 sizes | `upload_image_to_s3()` — 800px, 400px, 150px |
| Private ACL on S3 uploads | `ExtraArgs={'ACL': 'private'}` |
| Pre-signed URLs via `|signed_url` filter | `get_signed_image_url()` + template filter |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| Profile completeness scoring | Function exists, returns 0-100 | Not cached in `profiles.completeness_pct`; calculated on every call; not shown in navbar |
| AJAX profile saves | Not implemented | All edits are full page loads |
| Photo management | Upload/delete/set_primary exist as routes | No drag-to-reorder; no client-side preview before upload |

### Missing

| Item | Specification | Priority |
|------|--------------|---------|
| Single `/profile` page with 5 AJAX sections | Currently 22 separate pages | P1 |
| `POST /api/profile/about` AJAX endpoint | Not implemented | P1 |
| `POST /api/profile/career` AJAX endpoint | Not implemented | P1 |
| `POST /api/profile/family` AJAX endpoint | Not implemented | P1 |
| `POST /api/profile/photos` AJAX endpoint | Not implemented | P1 |
| `POST /api/profile/preferences` AJAX endpoint | Not implemented | P1 |
| `GET /api/profile/completeness` endpoint | Not implemented | P1 |
| Completeness ring per section (sidebar desktop) | Not implemented | P1 |
| `Profile.profile_for` field (Self/Son/Daughter) | Not in model | P2 |
| `Profile.completeness_pct` cached column | Not in model | P2 |
| `PartnerPreference.min_income_lpa` Integer | `min_income` is String | P1 |
| `PartnerPreference.max_income_lpa` Integer | Not in model | P1 |
| `PartnerPreference.religion_list` JSON Array | Single String only | P1 |
| `PartnerPreference.city_list` JSON Array | Single String only | P1 |
| SortableJS drag-to-reorder photos | Not implemented | P2 |
| `User.last_active_at` DateTime | Not in model | P1 |

### Conflicting

| Conflict | Current | Target | Risk | Recommendation |
|----------|---------|--------|------|----------------|
| `/profile` route currently shows settings list | Returns a settings-style list page | Should be the unified 5-section AJAX editor | HIGH — breaking change to primary profile route | Implement new template at same URL; add `?section=X` query param; old individual routes redirect to `/profile?section=about` |
| `date_of_birth` String vs `dob` Date | Both columns exist; code writes to `date_of_birth` in places | Use only `dob` Date everywhere; drop `date_of_birth` legacy | MEDIUM | Migration: set `date_of_birth = None` for all rows after confirming `dob` is populated |

---

## DOCUMENT 4 — COMPLETE UI/UX REDESIGN

### Already Implemented

| Item | Evidence |
|------|----------|
| Core brand tokens (`--brand`, `--surface`, `--text`, etc.) | `style.css` `:root` block |
| Shadow scale (`--shadow-xs` through `--shadow-lg`) | `style.css` |
| Radius scale (`--r-sm` through `--r-xl`) | `style.css` |
| Transition tokens (`--t-fast`, `--t-mid`) | `style.css` |
| Status colors (`--green`, `--green-bg`, `--blue`, `--blue-bg`) | `style.css` |
| `.btn-ij-primary` and `.btn-ij-ghost` components | `style.css` |
| `.ij-card`, `.ij-card-header`, `.ij-card-body` | `style.css` |
| `.ij-avatar` with size variants (xs, sm, md, lg, xl) | `style.css` |
| Toast system with slide-in animation | `style.css` + `base.html` JS |
| Custom scrollbar styling | `style.css` |
| Chip/badge components | `style.css` — `.chip`, `.chip-plan` |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| Profile card component | Cards exist in home.html | No `.ij-profile-card` reusable CSS class; inline styles used |
| Button variants | Primary and ghost exist | No `.btn-interest` (green) variant; no `.btn-ij-icon` (circle) |
| Avatar dropdown | Implemented | Does not use `.ij-dropdown` reusable class consistently |
| Form input styles | `.ij-input` referenced | Not fully defined in style.css (partial implementation) |
| Bottom sheet component | Not implemented | Mobile filter panel requires this |

### Missing

| Item | Specification | Priority |
|------|--------------|---------|
| Spacing token scale (`--space-1` through `--space-16`) | Not in style.css | P1 |
| Typography token scale (`--text-xs` through `--text-5xl`) | Not in style.css | P1 |
| Z-index token scale (`--z-base` through `--z-nav`) | Not in style.css | P1 |
| Trust badge colors (`--trust-registered` through `--trust-full`) | Not in style.css | P1 |
| Match score colors (`--score-low`, `--score-mid`, `--score-high`) | Not in style.css | P1 |
| `.ij-profile-card` reusable component class | Not in style.css | P1 |
| `.card-photo` with 3:4 aspect ratio | Not in style.css | P1 |
| `.trust-badge` component | Not in style.css | P1 |
| `.completeness-ring-wrap` component | Not in style.css | P1 |
| `.ij-bottom-sheet` component | Not in style.css | P1 |
| `.ij-tabs` horizontal tab component | Not in style.css | P1 |
| `.filter-pills` scrollable pill row | Not in style.css | P1 |
| `.ij-field` form field wrapper | Not in style.css | P1 |
| `@media (hover: none)` — remove hover on touch | Not in style.css | P1 |
| `-webkit-tap-highlight-color: transparent` | Not in style.css | P1 |
| `.ij-input` complete definition with focus ring | Partial — not complete | P1 |
| `.btn-ij-icon` circle button | Not in style.css | P2 |
| `.btn-interest` green variant | Not in style.css | P2 |
| Card grid (`grid-template-columns: repeat(2, 1fr)` mobile) | Not in style.css | P1 |
| Bootstrap served locally (no CDN) | CDN dependency | P2 |

### Conflicting

| Conflict | Current | Target | Recommendation |
|----------|---------|--------|----------------|
| `my_profile.html` uses Bootstrap card classes | `card shadow-sm rounded-4 overflow-hidden` | All cards use `ij-card` design system | Replace Bootstrap classes in `my_profile.html` — 1-hour fix |
| style.css mixes Bootstrap overrides with design system | Single 907-line file | Separate concerns: `tokens.css`, `components.css`, `overrides.css` | Refactor at CSS layer sprint |

---

## DOCUMENT 5 — SCREEN-BY-SCREEN WIREFRAMES (17 screens)

### Already Implemented

| Screen | Status | Evidence |
|--------|--------|----------|
| Screen 1: Landing page | ✅ Implemented | `templates/main/landing.html` — hero, CTA, features, plans |
| Screen 2: Registration | ✅ Implemented | `templates/auth/register.html` |
| Screen 3: OTP Verification | ✅ Implemented | `templates/auth/verify_phone.html` |
| Screen 4: Onboarding Gender | ✅ Implemented | `templates/onboarding/gender.html` |
| Screen 5: Onboarding Basics | ✅ Implemented | `templates/onboarding/basics.html` |
| Screen 6: Photo Upload | ✅ Implemented | `templates/onboarding/photo.html` |
| Screen 11: Interests | ✅ Implemented | `templates/connect/interests.html` |
| Screen 12: Messages Inbox | ✅ Implemented | `templates/messaging/inbox.html` |
| Screen 13: Conversation | ✅ Implemented | `templates/messaging/conversation.html` |
| Screen 15: Kundli Edit | ✅ Implemented | `templates/kundli/edit.html` |
| Screen 16: Guna Milan Report | ✅ Implemented | `templates/kundli/match.html` |

### Partially Implemented

| Screen | Current State | Gap |
|--------|--------------|-----|
| Screen 7: Home Feed Mobile | Home feed exists with cards | No discovery tabs; no 2-column grid CSS class; trust badges absent |
| Screen 8: Home Feed Desktop | Desktop layout with sidebar exists | Sidebar not contextual; 4-column card grid not implemented |
| Screen 9: Profile View | `my_profile.html` exists | Uses Bootstrap card classes; sticky CTA bottom bar absent on mobile |
| Screen 10: Profile Editor | `/profile` settings list exists | Not a tabbed AJAX editor; completeness ring missing |
| Screen 14: Membership Plans | Plans page exists | No per-day pricing; no social proof; no urgency display |
| Screen 17: Search + Filter Bottom Sheet | Search exists | No filter bottom sheet on mobile; income filter not wired |

### Missing

| Screen | Status | Priority |
|--------|--------|---------|
| Registration (OTP-first, 2-field) | Current registration has full form; no phone-OTP primary flow | P0 |
| Home feed discovery tabs sub-navigation | No `?tab=new`, `?tab=mutual`, `?tab=near` routes | P1 |
| Mobile filter bottom sheet | No `.ij-bottom-sheet` component or implementation | P1 |
| Profile editor tabbed AJAX sections | No tabbed profile editor template | P1 |
| Sticky profile CTA bar on mobile | No fixed bottom CTA on profile view mobile | P1 |

---

## DOCUMENT 6 — API-FIRST ARCHITECTURE

### Already Implemented

| Item | Evidence |
|------|----------|
| 4 JSON endpoints (Kundli) | `/kundli/api/calculate`, `/kundli/api/match`, `/kundli/api/cities`, `/notifications/unread-count` |
| HTTP polling fallback for messages | `/messages/<id>/poll` returns JSON |
| Standard JSON response pattern (partial) | Kundli API returns `{available, score, koots, ...}` |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| Notification JSON API | `/notifications/list` returns JSON | Uses session auth only; no JWT; no pagination |
| Rate limiting on API routes | Flask-Limiter applied to some routes | Not applied consistently across all JSON endpoints |

### Missing

| Item | Specification | Priority |
|------|--------------|---------|
| Flask-JWT-Extended installed | Not in requirements.txt | P0 |
| Marshmallow installed | Not in requirements.txt | P0 |
| Flask-CORS installed | Not in requirements.txt | P0 |
| `app/api/` blueprint directory | Does not exist | P0 |
| `POST /api/v1/auth/send-otp` | Not implemented | P0 |
| `POST /api/v1/auth/verify-otp` → JWT tokens | Not implemented | P0 |
| `POST /api/v1/auth/refresh` | Not implemented | P0 |
| `GET /api/v1/profiles/feed` | Not implemented | P0 |
| `GET /api/v1/profiles/@username` | Not implemented | P0 |
| `POST /api/v1/profiles/photos` | Not implemented | P0 |
| `GET /api/v1/profiles/completeness` | Not implemented | P0 |
| `POST /api/v1/interests` | Not implemented | P0 |
| `GET /api/v1/interests/received` | Not implemented | P0 |
| `PATCH /api/v1/interests/<id>` | Not implemented | P0 |
| `GET /api/v1/conversations` | Not implemented | P0 |
| `POST /api/v1/conversations/<id>/messages` | Not implemented | P0 |
| `POST /api/v1/devices` (FCM tokens) | Not implemented | P0 |
| `GET /api/v1/plans` | Not implemented | P1 |
| `POST /api/v1/kundli/calculate` (JWT-authenticated) | Exists but session-only | P1 |
| Standard `{success, data, meta}` response format | Not standardised | P0 |
| API error code constants (`INVALID_OTP` etc.) | Not implemented | P1 |
| `UserDevice` model for FCM tokens | Not in models.py | P0 |
| `/api/v1/` blueprint prefix | No versioned prefix | P0 |
| Marshmallow `ProfileCardSchema` | Not implemented | P0 |
| Marshmallow `ProfileFullSchema` | Not implemented | P0 |
| JWT token revocation via Redis | Not implemented | P1 |
| SocketIO JWT authentication path | Session-only currently | P1 |
| OpenAPI/Swagger documentation | Not implemented | P2 |

### Conflicting

| Conflict | Current | Target | Risk | Recommendation |
|----------|---------|--------|------|----------------|
| All routes return HTML | Every blueprint renders templates | API routes return JSON with JWT | LOW — additive change; no conflict with existing HTML routes | Add `app/api/` as new blueprint alongside existing blueprints |
| SocketIO uses Flask-Login session | `current_user.is_authenticated` in socket events | JWT token in SocketIO `auth` parameter | MEDIUM — requires socket event refactor | Add JWT auth path alongside session path; both work |

---

## DOCUMENT 7 — MOBILE-FIRST DESIGN SYSTEM

### Already Implemented

| Item | Evidence |
|------|----------|
| Bottom navigation exists | `base.html` — `#ij-bottom-nav` |
| PWA manifest | `static/manifest.json` |
| Service worker | `static/sw.js` |
| `apple-mobile-web-app-capable` meta tag | `base.html` head |
| `apple-touch-icon` meta tag | `base.html` head |
| `theme-color` meta tag | `base.html` |
| Viewport meta tag | `base.html` |
| `-webkit-font-smoothing: antialiased` | `style.css` |
| Custom scrollbar styling | `style.css` |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| PWA icons | Manifest references `/static/images/icon-192.png` | Icon file existence not confirmed; maskable purpose not set |
| Bottom nav height | Estimated 56px | Redesign requires 64px for 44px touch targets |
| Safe area inset support | Not confirmed | `env(safe-area-inset-bottom)` not in style.css |
| Card grid (2 columns mobile) | Home feed has card layout | No explicit `repeat(2, 1fr)` mobile grid in CSS |

### Missing

| Item | Specification | Priority |
|------|--------------|---------|
| Breakpoint token variables (`--screen-sm` etc.) | Not in style.css | P1 |
| Spacing scale (`--space-1` through `--space-16`) | Not in style.css | P1 |
| Safe area CSS classes (`.safe-top`, `.safe-bottom`) | Not in style.css | P1 |
| `@media (hover: none)` touch interaction overrides | Not in style.css | P1 |
| `-webkit-tap-highlight-color: transparent` global | Not in style.css | P1 |
| Bottom sheet component (`.ij-bottom-sheet`) | Not in style.css | P1 |
| Mobile search bar component | Not in style.css | P1 |
| Onboarding full-screen layout (`min-height: 100dvh`) | Not in style.css | P1 |
| Profile view sticky CTA bar (mobile) | Not in style.css | P1 |
| PWA offline page (`/offline.html`) | Does not exist | P1 |
| PWA icon files (192px + 512px maskable) | Not confirmed present | P1 |
| `screenshots` field in manifest.json | Not in manifest | P2 |
| FCM push notification integration | Not implemented | P1 |
| `UserDevice` model | Not in models.py | P0 |
| `firebase-admin` SDK | Not in requirements.txt | P1 |

### Conflicting

| Conflict | Current | Target | Recommendation |
|----------|---------|--------|----------------|
| Hover states throughout style.css | `:hover` on cards, buttons, links | `@media (hover: none)` removes hover on touch; `:active` replaces | Add media query block at end of style.css |
| Search filter sidebar `d-none d-lg-block` | Filter hidden on mobile | Filter accessible via bottom sheet on mobile | Implement bottom sheet; keep sidebar for desktop |

---

## DOCUMENT 8 — RECOMMENDED ARCHITECTURE

### Already Implemented

| Item | Evidence |
|------|----------|
| Flask monolith (correct for 0-10K users) | Confirmed — single process |
| Nginx reverse proxy | Confirmed in deployment |
| Gunicorn with gevent | `requirements.txt` — gunicorn + gevent |
| ProxyFix middleware | `wsgi.py` — `ProxyFix(x_for=1, x_proto=1, x_host=1)` |
| Redis for rate limiting + Celery broker | `config.py` — separate DB indices |
| Celery async task queue (9 tasks) | `app/tasks.py` |
| S3 for photo storage | `utils.py` — `upload_image_to_s3()` |
| SES for email | `utils.py` — `send_email()` |
| Sentry error monitoring | `app/__init__.py` — conditional init |
| Pool configuration on SQLAlchemy | `config.py` — `pool_size=10, max_overflow=20` |
| Session invalidation on password change | `session_version` column + `before_request` hook |
| Guna Milan in match ranking (±5 pts) | `calculate_match_score()` — confirmed |
| AdminAuditLog INSERT-only | `app/models.py` — confirmed |
| `plan_can_view_photos` property | `User.plan_can_view_photos` — confirmed |

### Partially Implemented

| Item | Current State | Gap |
|------|--------------|-----|
| `last_active_at` update | Not implemented at all | Needs column + `before_request` hook updating at hourly intervals |
| Match score caching | Calculated synchronously per request | No Redis cache; no `MatchScoreCache` table; no Celery refresh task |
| Subscription expiry check | No automated check | No Celery Beat task; subscriptions expire based on `expires_at` but no action fires |

### Missing

| Item | Specification | Priority |
|------|--------------|---------|
| `User.last_active_at` column | Not in model | P1 |
| `last_active_at` `before_request` update (hourly) | Not in `app/__init__.py` | P1 |
| `MatchScoreCache` table | Not in models | P2 |
| Celery Beat process | Not configured | P0 |
| Celery Beat schedule (`CELERYBEAT_SCHEDULE`) | Not in config.py | P0 |
| Daily match email task | Not in tasks.py | P0 |
| Subscription expiry Celery task | Not in tasks.py | P0 |
| Match score pre-computation Celery task | Not in tasks.py | P1 |
| OTP cleanup Celery task | Not in tasks.py | P2 |
| `UserDevice` model for FCM | Not in models | P0 |
| FCM push notification task | Not in tasks.py | P1 |
| `saved_searches` table | Not in models | P2 |
| ProfileView daily deduplication index | No unique index on (viewer_id, viewed_id, DATE(timestamp)) | P2 |
| `PartnerPreference.min_income_lpa` Integer | min_income is String | P1 |
| `PartnerPreference.max_income_lpa` Integer | Not in model | P1 |

---

## CROSS-DOCUMENT CONFLICT MATRIX

| ID | Conflict | Documents Involved | Impact | Resolution |
|----|----------|-------------------|--------|-----------|
| C1 | Email-first vs phone-first registration | MASTER_REDESIGN + IDEAL_USER_FLOW + API_FIRST | HIGH — entire auth flow changes | Implement phone OTP as primary path. Keep email registration as secondary. Not a breaking change to existing users. |
| C2 | 22 profile routes vs 1 AJAX editor | PROFILE_MANAGEMENT + UI_UX + WIREFRAMES | HIGH — primary user journey change | Implement new tabbed editor at `/profile`. Redirect all 22 old routes. |
| C3 | Bootstrap visual system in `my_profile.html` vs iJodidar design system | MASTER_REDESIGN + UI_UX | LOW — visual only | Replace Bootstrap card classes. No model or route changes needed. |
| C4 | Global sidebar vs contextual sidebar | MASTER_REDESIGN + NAVIGATION | MEDIUM — template restructure | Implement sidebar as template block override per section. |
| C5 | Session auth for SocketIO vs JWT auth | API_FIRST + MOBILE_DESIGN | HIGH — mobile app requirement | Add JWT auth path in `socket_events.py`. Session path remains for web. |
| C6 | Synchronous email in SocketIO handler | RECOMMENDED_ARCH + current code | HIGH — performance | Replace `send_email()` call in `socket_events.py` with `send_message_email_task.delay()`. |
| C7 | `date_of_birth` String vs `dob` Date | PROFILE_REDESIGN + RECOMMENDED_ARCH + current model | MEDIUM — data migration | All code should read/write `dob` Date. `date_of_birth` deprecated column. |
| C8 | `min_income` String vs `min_income_lpa` Integer | IDEAL_PROFILE + RECOMMENDED_ARCH + current model | MEDIUM — search filter broken | Add `min_income_lpa` + `max_income_lpa` Integer columns to PartnerPreference. |
| C9 | Income filter defined in search UI but not wired | MASTER_REDESIGN + search/routes.py | HIGH — feature broken | 2-hour fix: add `income_lpa` filter to search query |
| C10 | Admin blueprint with 14 redirect routes | All documents (deprecated) | LOW — cleanup | Remove `app/admin/routes.py` and `templates/admin/` directory |

---

## PHASE B SUMMARY SCORECARD

| Redesign Document | Fully Implemented | Partially Implemented | Missing Items | Conflicts |
|-------------------|-------------------|----------------------|---------------|-----------|
| Master Product Redesign | 11 items | 7 items | 14 items | 3 |
| Navigation Architecture | 6 items | 4 items | 9 items | 3 |
| Profile Management Redesign | 9 items | 3 items | 17 items | 2 |
| Complete UI/UX Redesign | 11 items | 5 items | 22 items | 2 |
| Screen-by-Screen Wireframes | 11 screens | 6 screens | 5 screens | 0 |
| API-First Architecture | 3 items | 2 items | 29 items | 2 |
| Mobile-First Design System | 9 items | 4 items | 16 items | 2 |
| Recommended Architecture | 14 items | 3 items | 14 items | 0 |
| **TOTALS** | **74** | **34** | **126** | **14** |

### Overall Alignment: 34% fully implemented, 16% partial, 50% missing

---

## CRITICAL PATH — What Must Be Done Before Mobile App Can Launch

The following 6 items are on the critical path. Every item below depends on all items above.

```
1. Install Flask-JWT-Extended + Marshmallow (P0, 2 hours)
      ↓
2. Implement /api/v1/ blueprint with JWT auth endpoints (P0, 1 week)
      ↓
3. Implement /api/v1/profiles/feed + /api/v1/profiles/@username (P0, 3 days)
      ↓
4. Implement /api/v1/interests + /api/v1/conversations (P0, 3 days)
      ↓
5. Add UserDevice model + /api/v1/devices + FCM task (P0, 2 days)
      ↓
6. SocketIO JWT authentication path (P1, 1 day)
```

Total: approximately 3 weeks for minimum viable mobile API surface.

---

CHECKPOINT_STATUS
Current Phase: B — Redesign Document Analysis
Current Section: REDESIGN_ALIGNMENT_REPORT.md Complete
Completed: REPOSITORY_DISCOVERY.md, DEPENDENCY_GRAPH.md, TECHNICAL_DEBT_REPORT.md, PROJECT_INVENTORY.md, REDESIGN_ALIGNMENT_REPORT.md
Remaining: Phase C (MATRIMONY_GAP_ANALYSIS), Phase C2 (FEATURE_RATIONALIZATION), Phase D (Migration Blueprint + 8 architecture docs)
Files Generated: 5
Progress Percent: 38%

Reply **CONTINUE** to proceed to Phase C — Matrimony Platform Gap Analysis.
