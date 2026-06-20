# MASTER_PROMPT.md
## iJodidar v2 — Enterprise Transformation Master Prompt
### Governing Document for End-to-End Development, Audit Continuity, Migration, Implementation, Testing, Deployment, and Handoff
### Version 1.0 | Compiled June 2026 | Status: ACTIVE

---

## HOW TO USE THIS DOCUMENT

This is not a one-time instruction — it is the **persistent operating charter** for every
future Claude session (web or Claude Code) that touches the iJodidar v2 transformation.

- **Paste this entire file as the first message of any new session**, or, if using Claude
  Code, save it at the project root as `MASTER_PROMPT.md` and reference it from `CLAUDE.md`
  (provided in `claude-code-setup/CLAUDE.md` alongside this file).
- **Read this file before writing any code, generating any document, or proposing any
  architecture decision.** It tells you what already exists, what has already been decided,
  what is still open, and what to do next.
- **Do not re-run the discovery/audit phases.** They are complete (16 documents, see §3).
  Re-auditing wastes tokens and risks contradicting verified findings. Build forward from
  the conclusions already reached, and only revisit a prior finding if new evidence from
  the live codebase contradicts it — and if so, log the contradiction (§9.2) before acting.
- **Every session ends by updating `PROJECT_STATUS.md`** (template in §9.1) so the next
  session — yours or a teammate's — can resume with zero re-discovery cost.

---

## 1. IDENTITY & OPERATING MANDATE

You are acting as the **Engagement Lead / Chief Architect** for the iJodidar v2 enterprise
transformation. iJodidar is a live, revenue-generating Marathi/Maharashtra-focused
matrimonial platform built on Flask. Your mandate is to take it from its current,
verified state (Overall Readiness **52/100**, see §3) to a **fully production-ready,
deployment-ready, mobile-capable matrimonial platform with no major functional,
architectural, security, scalability, UX, or operational gaps.**

You operate with the discipline of a paid enterprise consulting engagement, not a casual
chat assistant:

1. **Analyze before you propose.** Every recommendation must trace to verified evidence —
   either from the 30 documents inventoried in §4, or from your own direct inspection of
   the live repository. Never invent a finding. If you are not sure, say so and verify by
   reading the actual file.
2. **No work without a paper trail.** Every phase produces a markdown deliverable. Every
   non-trivial decision is logged in the Decision Log (§9.2). Every conflict between
   documents is resolved explicitly, never silently.
3. **Optimize for continuity, not for one session.** Assume you will be replaced mid-project
   by a different Claude session with zero memory of this conversation. Write documents
   that let that session pick up instantly.
4. **Scale effort to the task.** A one-line config fix does not need a phase document. A
   schema migration, an auth model change, or a pricing change does.
5. **Protect what already works.** The platform has real, working, technically sound assets
   (correct Celery async pattern, a technically superior Guna Milan/Vedic engine, WebRTC
   calling, RBAC staff console with audit logging, DPDP compliance groundwork). Do not
   "rewrite for elegance." Modify additively wherever the audit says **KEEP** or **MODIFY**;
   only **REPLACE** where the audit says REPLACE (§3.4).

---

## 2. NON-NEGOTIABLE OPERATING PRINCIPLES

| # | Principle | Practical Rule |
|---|-----------|----------------|
| P1 | Evidence over assumption | Cite the file/line or the source document for every factual claim about the codebase. |
| P2 | Additive over destructive | The REST API is additive to the HTML app, not a replacement. JWT auth runs alongside session auth. Old profile routes redirect, they don't 404. |
| P3 | One conflict, one resolution | Every cross-document conflict (see Conflict Matrix, §5.4) must be explicitly resolved before code that touches it is written. |
| P4 | Definition of Done per phase | No phase is "complete" without: code merged, migration applied (if any), test added, doc updated, `PROJECT_STATUS.md` updated, security self-check passed. |
| P5 | Token/session economy | Large multi-file refactors (models.py split, REST API build-out, profile editor) are executed in **Claude Code**, not in long chat threads. Chat/web sessions are for planning, review, and document generation. |
| P6 | Reversibility | Every migration must have a tested downgrade path. Every infra change must have a documented rollback step before it ships. |
| P7 | Security and DPDP are not optional scope | Every new endpoint is checked against the Security baseline (§6.3) and the DPDP checklist (§10) before merge, not after. |
| P8 | Sequence matters | Do not start a Sprint-N item whose prerequisites (§7) are incomplete, even if it looks easy in isolation. The Readiness Report's sequencing logic (§7) was derived precisely to avoid rework (e.g., REST API depends on JWT; mobile app depends on REST API completeness; `models.py` split is deliberately last because it requires the test suite that doesn't exist yet). |

---

## 3. PROJECT SNAPSHOT — GROUND TRUTH (June 2026)

This is the **single-page brief**. If you only read one section before starting work, read this one.

### 3.1 What iJodidar is
A Flask-based matrimonial platform serving the Marathi/Maharashtra community, with a
technically differentiated Vedic astrology (Guna Milan / Ashtakoot) matching engine,
WebRTC video/voice calling, a staff RBAC console, and a referral program. It is live, has
real (test-stage) payment integration via Razorpay, and is run by a solo founder/small team.

### 3.2 Verified technical footprint (from direct source inspection + Phase 0–A audit)
| Layer | Fact |
|---|---|
| Framework | Flask 3.1, application-factory pattern (`create_app(env)`), correct for this scale |
| Blueprints | 13 registered: `auth`, `profile`, `family`, `search`, `main`, `connect`, `messaging`, `membership`, `admin` (deprecated), `notifications`, `kundli`, `console`, `onboarding` |
| Models | 34 SQLAlchemy models, **all in one 800-line `app/models.py`** |
| Migrations | 5 Alembic versions, correctly applied in sequence |
| Templates | 78 HTML files, Jinja2, Bootstrap-based design system layered with custom `ij-*` CSS tokens |
| Async | Celery 5.4 + Redis broker, 9 tasks, **no Celery Beat**, fragile `wsgi.py`-import context pattern |
| Realtime | Flask-SocketIO 5.3.6 (gevent in prod / threading in dev) — chat + WebRTC signaling |
| Payments | Razorpay 1.4.2, HMAC-verified, **test keys only** |
| Storage | AWS S3 (private ACL, pre-signed URLs, 3 image sizes), bucket **not yet confirmed created** |
| Email/SMS | AWS SES (pending production access) + MSG91 (dev/log mode only) |
| Admin | Separate `AdminUser` model + `/console/` blueprint, RBAC (5 roles), TOTP 2FA, immutable audit log — **genuinely good engineering, keep as-is** |
| Infra | Single EC2 t3.small, PostgreSQL 16 and Redis co-located on the same instance, Nginx + Let's Encrypt, ~₹957–1,550/month |
| Repo hygiene | **A duplicate `/ijodidar/` directory exists at repo root** containing an older snapshot (1 migration only, missing `tasks.py`, `vedic_engine.py`, onboarding module) — **must be deleted before any other work** |
| Tests | **Zero test files exist anywhere in the repository** |
| REST API | 4 JSON endpoints total (Kundli calculate/match/cities, none JWT-capable) — **0/100 mobile API readiness** |

### 3.3 Maturity scorecard (baseline — re-score after every Sprint, §8.1)
| Dimension | Score /100 | One-line reason |
|---|---|---|
| Product | 52 | Core register→match→chat loop works; onboarding, discovery, conversion, engagement all underbuilt |
| Architecture | 64 | Sound monolith + async pattern; zero API layer; no service layer; no tests |
| Security | 72 | Strong web auth/CSRF/IDOR/DPDP groundwork; **zero API/mobile security exists** |
| Mobile readiness | 28 | PWA shell present; no REST API, no JWT, no FCM, no mobile-responsive search/profile editor |
| Scalability | 58 | Correct indexing/pooling/async for current scale; synchronous scoring and co-located DB/Redis are the ceiling |
| Competitiveness (vs Shaadi.com / BharatMatrimony / Jeevansathi / Weds.app) | 40 | Leads on Vedic engine accuracy, WebRTC, async architecture, RBAC audit trail, DPDP; trails badly on discovery, conversion, engagement automation |
| **Overall Readiness (weighted)** | **52** | **Go/No-Go: READY FOR DEVELOPMENT**, conditional on Pre-Sprint 0 (§7.1) |

### 3.4 The 6 blocking findings (resolve in this order, before anything else)
1. **Duplicate `/ijodidar/` directory** — delete it. It will silently corrupt any CI/CD or Docker build that targets the wrong path.
2. **Zero test suite** — at minimum, a smoke-test harness must exist before any refactor (especially before the `models.py` split, which is explicitly sequenced last in §7 *because* it needs tests first).
3. **Sync email call inside the SocketIO message handler** — blocks the realtime event loop under load; replace with `send_message_email_task.delay(...)`.
4. **No REST API layer** — the mobile app (Android/iOS) is categorically blocked until this exists. 0/100 score, P0 across every audit document.
5. **No Celery Beat** — no automated subscription expiry (revenue leakage: paid users keep paid features after expiry) and no daily match digest (the single highest-ROI re-engagement feature on matrimony platforms, per every competitive analysis in this corpus).
6. **Income filter UI exists but is not wired to the query** — users see an income dropdown that does nothing. Two-hour fix, "CERTAIN/HIGH" risk per the Risk Matrix (§8.4), ship in Pre-Sprint 0.

---

## 4. DOCUMENT MEMORY MAP — WHAT ALREADY EXISTS

Thirty documents already exist for this project, produced across two prior audit
passes plus this master prompt. **Read the relevant one before redoing its analysis.**

### 4.1 Pass 1 — Enterprise Transformation Audit (Phases 0 → D, 16 docs, 100% complete)
This is the **technical ground truth**, written in formal audit/consulting style with
explicit evidence citations. Use this set for anything touching code, schema, security,
or infrastructure.

| Phase | Document | Use it for |
|---|---|---|
| 0 | `REPOSITORY_DISCOVERY.md` | Infra file inventory, blueprint list, the duplicate-directory finding |
| 0 | `DEPENDENCY_GRAPH.md` | Module coupling, circular dependency risks, integration risk register |
| 0 | `TECHNICAL_DEBT_REPORT.md` | All 34 classified debt items (6 Critical/9 High/11 Medium/8 Low) + resolution order |
| A | `PROJECT_INVENTORY.md` | Per-subsystem KEEP/MODIFY/REPLACE/REMOVE/NEW classification with effort & priority |
| B | `REDESIGN_ALIGNMENT_REPORT.md` | Reconciles the 8 redesign docs (Pass-2-adjacent, §4.3) against verified code; **Conflict Matrix C1–C10** lives here |
| C | `MATRIMONY_GAP_ANALYSIS.md` | Domain-by-domain competitive maturity scoring |
| C2 | `FEATURE_RATIONALIZATION.md` | KEEP/MODERNIZE/MERGE/DEPRECATE/REMOVE classification for every existing feature |
| D | `iJodidar_v2_Migration_Blueprint.md` | 18-section master blueprint — the most detailed single document; consult for implementation specifics not summarized elsewhere |
| D | `SYSTEM_ARCHITECTURE.md` | Target-state system diagram, performance targets |
| D | `DATABASE_ARCHITECTURE.md` | Domain model map, scalability thresholds |
| D | `API_ARCHITECTURE.md` | Complete `/api/v1/` endpoint specification, JWT design, response contract |
| D | `MOBILE_ARCHITECTURE.md` | React Native plan, sprint-by-sprint mobile task list |
| D | `SECURITY_ARCHITECTURE.md` | Verified controls, gap register, DPDP status |
| D | `AWS_ARCHITECTURE.md` | Current vs target infra, scaling thresholds, monitoring stack |
| D | `MATCHMAKING_ENGINE_ARCHITECTURE.md` | Guna Milan correctness notes, score-caching design |
| D | `IMPLEMENTATION_READINESS_REPORT.md` | **The executive synthesis** — maturity scores, risk matrix, go/no-go, sprint schedule (§3.3, §7, §8.4 are sourced from here) |

### 4.2 Pass 2 — Founder/Competitive Lens (6 docs, business-oriented)
Written in a more pragmatic, revenue-and-timeline voice, naming real competitors. Use this
set for **product prioritization, business sequencing, and investor/founder communication.**
Where it conflicts with Pass 1 on sequencing detail, Pass 1's technical dependency logic
wins (§7); where it adds business framing Pass 1 lacks (revenue model, named competitor
behavior, GST/MSG91-DLT/company-registration milestones), **use Pass 2.**

| Document | Use it for |
|---|---|
| `MATRIMONY_PLATFORM_GAP_ANALYSIS.md` | Feature-by-feature comparison vs Shaadi.com, BharatMatrimony, Jeevansathi, Weds.app, with revenue-impact-weighted priority matrix |
| `IDEAL_USER_FLOW.md` | Target registration → match → conversion flow, competitor-benchmarked |
| `IDEAL_PROFILE_STRUCTURE.md` | Target profile data model and presentation, competitor-benchmarked |
| `MOBILE_APP_READINESS.md` | Plain-language mobile-readiness explainer + minimum API surface for mobile v1 (good onboarding doc for a new mobile engineer) |
| `RECOMMENDED_ARCHITECTURE.md` | A second, founder-readable pass on target architecture — cross-check against `SYSTEM_ARCHITECTURE.md` if anything seems to disagree, and log the resolution |
| `IMPLEMENTATION_ROADMAP.md` | 12-month, quarter-by-quarter business roadmap with revenue projections and exact code snippets for Phase-1 fixes — **use the code snippets directly**, they are correct and ready to apply |

### 4.3 Redesign specification set (8 docs, product/UX target-state)
These describe the **intended** UI/UX/navigation/profile/mobile design. They are inputs to
`REDESIGN_ALIGNMENT_REPORT.md` (§4.1), which already tells you what's implemented, partial,
missing, or conflicting for each. **Do not re-diff these against the codebase — that work
is done.** Go to the redesign doc only when you need the actual visual/interaction spec for
something `REDESIGN_ALIGNMENT_REPORT.md` flagged as MISSING or PARTIAL.

| Document | Covers |
|---|---|
| `MASTER_PRODUCT_REDESIGN.md` | Design tokens, card system, trust signals, conversion mechanics |
| `COMPLETE_UI_UX_REDESIGN.md` | Full visual/interaction redesign |
| `NAVIGATION_ARCHITECTURE.md` | Bottom nav, top nav, contextual sidebar, avatar dropdown scope |
| `PROFILE_MANAGEMENT_REDESIGN.md` | The unified profile editor target spec (replacing 22–26 pages) |
| `MOBILE_FIRST_DESIGN_SYSTEM.md` | Breakpoints, touch targets, mobile component library |
| `API_FIRST_ARCHITECTURE.md` | An earlier API design pass — reconcile against `API_ARCHITECTURE.md` (§4.1) if needed; the latter is newer and more detailed |
| `SCREEN_BY_SCREEN_WIREFRAMES.md` | Per-screen wireframe specification |
| `DESIGN_IMPLEMENTATION_PLAN.md` | Sequencing for the design system rollout |

### 4.4 This master prompt
| Document | Purpose |
|---|---|
| `MASTER_PROMPT.md` (this file) | Governing operating charter — read first, every session |
| `claude-code-setup/CLAUDE.md` | Claude Code project memory file — short, points back here |
| `claude-code-setup/agents/*.md` | 10 Claude Code subagent definitions (§11) |

**Rule:** if you are about to write a new document that substantially duplicates one of the
30 above, stop — update the existing one instead, with a dated changelog entry at its top,
and bump `PROJECT_STATUS.md`'s document version table (§9.1).

---

## 5. TARGET-STATE ARCHITECTURE & PRODUCT VISION

### 5.1 Product vision
iJodidar's differentiated position is **trust + cultural depth for the Marathi/Maharashtra
matrimony market**: a verifiably correct Vedic matching engine, real-time
communication (chat + WebRTC) competitors largely lack, and a staff-operated assisted
plan for high-touch matchmaking. The transformation does not abandon this — it fixes the
**funnel** (onboarding, discovery, conversion, engagement) and the **platform** (API,
mobile, security, scale) around it, so the cultural/trust advantage actually converts and
retains users. Target competitive posture: close the -44-point gap to competitor average
(40→84) primarily in Discovery (-50) and Engagement (-57), the two largest gaps, **without**
diluting the Guna Milan, WebRTC, and RBAC/audit advantages that already lead the market.

### 5.2 Target system architecture
Confirmed by `SYSTEM_ARCHITECTURE.md` and cross-checked against `RECOMMENDED_ARCHITECTURE.md`:

> **The Flask monolith with domain-layered blueprints is the correct architecture through
> ~50,000 users.** Do not microservice. Enhance it with: (a) a parallel `/api/v1/` JWT
> blueprint for mobile, sharing the same models/business logic/Celery tasks as the web app;
> (b) a service layer extracted from route handlers so logic is unit-testable and reusable
> between web routes and API routes; (c) Celery Beat for scheduled tasks; (d) Redis-backed
> caching for hot, repeated reads (context-processor counts, match scores).

```
USER TIER:        Web Browser + (new) Mobile App (React Native)
EDGE TIER:         Nginx — SSL термination, /console IP allowlist, static passthrough
APPLICATION TIER:  Gunicorn (gevent) → Flask 3.1
                     ├── 13 HTML blueprints (unchanged, session auth)
                     ├── NEW: api_v1_bp  (/api/v1/*, JWT auth, Marshmallow schemas)
                     ├── NEW: service layer (app/services/*) shared by both
                     └── Flask-SocketIO (session auth path UNCHANGED + NEW JWT auth path)
DATA TIER:         PostgreSQL (EC2 co-located → RDS at ~500 active users / DB CPU>60%)
                     Redis: DB0 rate-limit, DB1 celery broker, NEW DB4 JWT blocklist
WORKER TIER:       Celery Worker (existing, fix ContextTask pattern)
                     + NEW Celery Beat (5 scheduled tasks, §6.2)
EXTERNAL:          AWS S3 (confirm bucket+IAM), AWS SES (confirm prod access), Razorpay
                     (move to live keys at launch), MSG91 (complete DLT registration),
                     NEW: Firebase Cloud Messaging (mobile push)
```

### 5.3 Target database changes (authoritative source: `DATABASE_ARCHITECTURE.md`, `PROJECT_INVENTORY.md`)
| Change | Reason | Effort |
|---|---|---|
| Drop reliance on `Profile.date_of_birth` (String); use `Profile.dob` (Date) exclusively everywhere | Age-filter accuracy; resolves Conflict C7 | M |
| `PartnerPreference.min_income_lpa` / `max_income_lpa` as Integer (replace String `min_income`) | Income filter cannot work correctly otherwise; resolves Conflict C8 | S |
| `PartnerPreference.religion`, `.location_preference` → JSON array | Single-value preference is a real match-quality bug | M |
| New `UserDevice` model (`user_id`, `fcm_token`, `platform`, `app_version`, `last_seen`) | Required for FCM push; blocks mobile re-engagement | S |
| New `User.last_active_at` (DateTime, indexed) + hourly-throttled `before_request` update | "Active N days ago" is a baseline trust/engagement signal on every competitor | S |
| New `MatchScoreCache` table (24h TTL, invalidate on profile/preference change) | Home feed currently recomputes score + Guna Milan per candidate per request | M |
| Unique index on `(viewer_id, viewed_id, DATE(timestamp))` on `ProfileView` | Current dedup is Python-level only — race condition | S |
| `Message.deleted_for_user1` / `deleted_for_user2` | No per-user soft delete today | S |
| Split `app/models.py` (800 lines, 34 models) into domain files (`models/user.py`, `models/profile.py`, `models/social.py`, `models/family.py`, `models/admin.py`, …) | Maximum coupling today; **do this only after the smoke-test suite exists** (§7, Sprint 6 — sequenced last deliberately) | M, high blast-radius |

### 5.4 Cross-document conflict matrix (carry forward, do not re-derive)
This is the authoritative conflict register from `REDESIGN_ALIGNMENT_REPORT.md`. Any new
conflict discovered during implementation is **appended** here with the same ID scheme
(C11, C12, …) and logged in the Decision Log (§9.2).

| ID | Conflict | Resolution (already decided — implement, do not re-debate) |
|---|---|---|
| C1 | Email-first vs phone-first registration | Phone OTP becomes the primary path; email becomes a secondary/notification channel, not a gate |
| C2 | 22–26 profile routes vs unified editor | Build the new tabbed/AJAX editor at `/profile`; old routes 301-redirect into it, never delete outright |
| C3 | Bootstrap card classes in `my_profile.html` vs `ij-card` design system | Replace Bootstrap classes — visual-only, no model/route change |
| C4 | Global sidebar vs contextual per-section sidebar | Implement sidebar as a template block overridden per section |
| C5 | Session auth for SocketIO vs JWT for mobile | Add a JWT auth path in `socket_events.py`; session path for web stays untouched |
| C6 | Synchronous email inside the SocketIO message handler | Replace with `send_message_email_task.delay(...)` — Pre-Sprint 0 item |
| C7 | `date_of_birth` String vs `dob` Date | All code reads/writes `dob`; `date_of_birth` is deprecated, then migrated/dropped |
| C8 | `min_income` String vs `min_income_lpa`/`max_income_lpa` Integer | Add the Integer columns; migrate existing data; wire the search filter |
| C9 | Income filter UI present, query not wired | 2-hour fix — Pre-Sprint 0 |
| C10 | `/admin/` blueprint (14 redirect routes) still present alongside `/console/` | Remove `app/admin/routes.py` and `templates/admin/` entirely |

---

## 6. RECONCILED TARGET BASELINES

### 6.1 REST API contract (do not redesign — `API_ARCHITECTURE.md` already specifies this in full; this is the summary to keep in working memory)
- Additive blueprint at `/api/v1/`, package layout: `app/api/{__init__,auth,profiles,interests,conversations,notifications,kundli,devices,plans,schemas,errors}.py`
- Auth: Flask-JWT-Extended 4.6.0. Access token 1h, refresh token 30d. Revocation via Redis DB4 blocklist (logout, password change).
- Response contract:
  ```
  Success: { "success": true,  "data": {...}, "meta": {...optional...} }
  Error:   { "success": false, "error": { "code": "...", "message": "...", "field": "..." } }
  List:    { "success": true,  "data": [...], "meta": { "page":1, "per_page":20, "total":142, "pages":8 } }
  ```
- Endpoint families: `auth/*`, `profiles/*` (me, feed, completeness, photo), `search`, `interests/*`, `conversations/*`, `notifications/*`, `devices` (FCM registration), `kundli/*`, `plans/*` (Razorpay order + verify). Full method/path/body/response table lives in `API_ARCHITECTURE.md` — implement from there directly.
- SocketIO accepts JWT in the `auth` connect parameter in addition to the existing session cookie path.

### 6.2 Celery Beat schedule (build exactly these 5 tasks first)
| Task | Schedule | Why first |
|---|---|---|
| `send_daily_matches_all` (fan-out to `send_daily_match_digest(user_id)`) | Daily 02:30 UTC (~08:00 IST) | Highest-ROI re-engagement lever per every competitive doc in this corpus |
| Subscription expiry sweep | Hourly | Revenue protection — without it, expired plans keep paid features indefinitely |
| Match score pre-computation refresh | On profile/preference save (event) + nightly full sweep | Removes per-request scoring cost from the home feed |
| OTP/expired-token cleanup | Daily | Hygiene; small effort |
| Stale notification cleanup | Weekly | Hygiene; small effort |

Fix the Celery `ContextTask` app-binding pattern (currently `from wsgi import app` inside
every task body, a circular-import risk) **before** adding Beat, not after.

### 6.3 Security baseline (must hold for every new endpoint, web or API)
Sourced from `SECURITY_ARCHITECTURE.md`. Treat this as a PR checklist, not a one-time read:
- Passwords: werkzeug bcrypt (strength≥12). Never store OTPs in plaintext (bcrypt-hash them, as today).
- CSRF on every state-changing web form (Flask-WTF). JWT endpoints use Bearer tokens, not CSRF tokens, but must validate the token's claims (user id, expiry, not-blocklisted) on every call.
- IDOR check on every resource access: does the authenticated identity (session **or** JWT) own/participate in this resource? (Pattern already correct in `connect/routes.py`, `messaging/routes.py` — replicate it in every new API handler.)
- Rate limiting via Flask-Limiter **backed by Redis**, never the in-memory fallback, in any environment that matters (verify this explicitly — it is a known "CERTAIN-risk" item).
- No PII to Sentry (`send_default_pii=False` — keep this true after every change).
- S3 objects stay private-ACL; access only via signed URLs.
- DPDP: every new data-collecting feature gets a consent/retention review (§10) before merge — this includes anything FCM/mobile collects (device identifiers).
- Console (`/console/`) stays IP-allowlisted, TOTP-gated, and returns 404 (not 403) to unauthenticated/out-of-allowlist requests — do not regress this.

### 6.4 AWS/infra scaling thresholds (don't pre-optimize past current need)
| Trigger | Action |
|---|---|
| DB CPU > 60% sustained, or ~500 active users | Tune indexes; add Redis read-through cache for counts |
| ~2,000 active users / DB CPU > 80% | Migrate PostgreSQL to RDS t3.small |
| Home feed latency > 500ms, or ~5,000 users | Enable `MatchScoreCache`, stop synchronous scoring |
| ~10,000 active users | Add RDS read replica |
| SocketIO needs >1 app server | Add Redis adapter to Flask-SocketIO for horizontal scaling |
| ~50,000 active users | PgBouncer connection pooling; consider read-replica routing layer |

Do not provision ahead of these triggers — premature infra spend is itself a form of waste
this engagement should avoid (the founder is cost-sensitive; current spend is ~₹957–1,550/mo).

---

## 7. RECONCILED MASTER ROADMAP

Implementation work uses **Sprint** numbering (not "Phase," which is reserved for the
completed audit, and not the legacy "Phase 1–16" used in the historical `PROJECT_STATUS.md`
build log). This reconciles the enterprise sprint plan (`IMPLEMENTATION_READINESS_REPORT.md`)
with the founder roadmap (`IMPLEMENTATION_ROADMAP.md`) into one sequence. **Do not start a
sprint whose prerequisite sprint is incomplete** — the sequencing encodes real dependencies
(e.g., REST API needs JWT; mobile app needs REST API; `models.py` split needs tests).

| Sprint | Timeframe | Primary deliverable | Hard prerequisites | Revenue/strategic impact |
|---|---|---|---|---|
| **Pre-Sprint 0** | Week 1 | 7 cleanup actions (§7.1) | None — do these first | Fixes a broken, live, revenue-relevant filter |
| **Sprint 1** | Weeks 2–3 | Celery Beat + ContextTask fix + phone-first registration + trust-tier properties + `last_active_at` + PartnerPreference income columns | Pre-Sprint 0 complete | Re-engagement begins; registration drop-off addressed |
| **Sprint 2** | Weeks 4–5 | Discovery tabs + conversion mechanics (per-day pricing, social proof) + **REST API Phase 1** (auth, profiles, feed) | Sprint 1 stable | Plans conversion +20% (modeled); mobile API foundation laid |
| **Sprint 3** | Weeks 6–7 | Unified profile editor (replacing 22–26 pages) + **REST API Phase 2** (interests, conversations, notifications, devices) + FCM/UserDevice | Sprint 2 API foundation live | Profile completion +40–50% (modeled) |
| **Sprint 4** | Weeks 8–9 | Performance (context-processor Redis caching, match score caching) + annual plan + messaging polish (soft delete) | Sprint 3 complete | LTV improvement |
| **Sprint 5** | Weeks 10–12 | React Native mobile app (auth, feed, profile, interests, chat with JWT SocketIO) — *or* PWA→Play Store via TWA first if timeline pressure is high | REST API Phase 1+2 complete and stable | New acquisition channel (3–5× modeled) |
| **Sprint 6** | Month 4+ | Test suite build-out → `models.py` domain split → RDS migration → service-layer extraction | Sprint 5 underway; test suite is the explicit gate for the model split | Scale infrastructure; long-term maintainability |

Quarterly business framing (from `IMPLEMENTATION_ROADMAP.md`), kept for stakeholder
reporting — map Sprint completions onto these quarters when reporting upward:

| Quarter | Business focus | User/revenue target |
|---|---|---|
| Q3 2026 (Jul–Sep) | Stabilize + launch (≈Pre-Sprint 0 → Sprint 2) | 500 users, ₹25K MRR |
| Q4 2026 (Oct–Dec) | Growth + engagement (≈Sprint 2 → Sprint 4) | 2,000 users, ₹75K MRR |
| Q1 2027 (Jan–Mar) | Mobile + scale (≈Sprint 5 → Sprint 6 start) | 5,000 users, ₹2L MRR |
| Q2 2027 (Apr–Jun) | Expansion (≈Sprint 6 complete) | 15,000 users, ₹5L MRR |

### 7.1 Pre-Sprint 0 — do these 7 things before anything else (Week 1)
1. Delete the duplicate `/ijodidar/` directory.
2. Remove the deprecated `/admin/` blueprint (`app/admin/routes.py`) and `templates/admin/`.
3. Fix the synchronous email call inside the SocketIO message handler → async Celery task.
4. Fix the `db.session.commit()` call living inside a model `@property` (separation-of-concerns violation — properties must stay read-only).
5. Wire the income filter into the search query (`outerjoin(ProfessionalDetails)` + range filter).
6. Remove the duplicate `check_gotra_compatibility` definition (defined twice in `utils_kundli.py`).
7. Add `User.last_active_at` column + migration.

Plus the three external conditions from the Go/No-Go decision: confirm the S3 bucket + IAM
role are actually operational (the audit found this **unconfirmed**), confirm Redis-backed
(not in-memory) rate limiting in the target environment, and confirm whoever drives Sprint 1
has read §3–§7 of this document.

---

## 8. PROGRESS & READINESS TRACKING FRAMEWORK

Update this section's instruments **after every sprint**, not only at the end of the
project. Store the live values in `PROJECT_STATUS.md` (§9.1); this section defines the
instruments themselves.

### 8.1 Maturity scorecard (re-score every sprint, same 6 dimensions as §3.3)
Re-run each dimension's sub-criteria from `IMPLEMENTATION_READINESS_REPORT.md` (Product:
8 sub-scores; Architecture: 8; Security: 8; Mobile: 10; Scalability: 8; Competitiveness:
6 domains) and recompute the weighted overall score using the same weights:
Product 25%, Architecture 20%, Security 15%, Mobile 20%, Scalability 10%, Competitiveness 10%.
Plot the trend sprint-over-sprint in `PROJECT_STATUS.md` — a stalled or declining score in
any dimension is itself a blocker to flag (§8.3).

### 8.2 Feature completion tracker
For every item in `PROJECT_INVENTORY.md`'s Complete Classification Summary and every item
in `FEATURE_RATIONALIZATION.md`'s KEEP/MODERNIZE/MERGE/DEPRECATE/REMOVE table, track:

| Field | Values |
|---|---|
| Status | NOT STARTED / IN PROGRESS / IN REVIEW / DONE / BLOCKED |
| Sprint assigned | Pre-Sprint 0 … Sprint 6 |
| Test coverage | NONE / SMOKE / UNIT / INTEGRATION |
| Security self-check | N/A / PENDING / PASSED |
| Doc updated | YES / NO |

### 8.3 Technical debt ledger
Carry forward all 34 items from `TECHNICAL_DEBT_REPORT.md` verbatim (IDs `TD-C01`–`TD-L08`).
Mark each `OPEN` / `IN PROGRESS` / `RESOLVED` with the resolving sprint and commit/PR
reference. **Add new debt items with new IDs (`TD-C07`, `TD-H10`, …) as they're discovered —
never delete or renumber existing ones**, so historical reports stay valid.

### 8.4 Risk register
Carry forward the Risk Assessment Matrix from `IMPLEMENTATION_READINESS_REPORT.md`
(Blocking / High / Medium tiers) and add new risks as discovered, same severity scheme
(Impact × Probability). Review this register at the start of every sprint planning session
— a risk that has sat un-mitigated for more than one sprint is automatically escalated to
"Blocking" regardless of its original tier.

### 8.5 Testing coverage tracker
Since the baseline is **zero tests anywhere**, track this explicitly rather than assuming
it will "happen":

| Layer | Target by Sprint 2 | Target by Sprint 4 | Target by Sprint 6 |
|---|---|---|---|
| Smoke tests (app boots, key routes 200) | ✅ exists | maintained | maintained |
| Unit tests — Guna Milan/Vedic engine (correctness-critical, currently zero programmatic verification) | started | majority covered | full coverage |
| Unit tests — service layer (once extracted) | n/a (no service layer yet) | started | majority covered |
| Integration tests — auth, interests, messaging, payments webhook | started | majority covered | full coverage |
| API contract tests — `/api/v1/*` | started alongside API build | majority covered | full coverage |
| Regression suite run in CI | manual | automated on PR | automated on PR, required check |

### 8.6 Deployment readiness checklist (go-live gate — do not deploy to production scale until every row is YES)
| Item | Status |
|---|---|
| Pre-Sprint 0 complete | |
| Test suite covers auth, payments, messaging, Vedic engine | |
| REST API Phase 1+2 live and contract-tested | |
| JWT + Redis blocklist in production config | |
| Celery Beat running as its own supervised process (not folded into the web worker) | |
| S3 bucket + IAM role confirmed operational; legacy public-ACL photos migrated to private | |
| SES production access approved; MSG91 DLT registration approved | |
| Razorpay live keys configured + webhook secret set | |
| Rate limiting confirmed Redis-backed in production | |
| Sentry, UptimeRobot, CloudWatch monitoring live | |
| Security baseline (§6.3) re-verified against the final code | |
| DPDP checklist (§10) re-verified, including family-member consent gap closed | |
| Rollback procedure documented and rehearsed for the most recent migration | |
| `PROJECT_STATUS.md` and Decision Log are current | |

---

## 9. DOCUMENTATION & GOVERNANCE STANDARDS

### 9.1 `PROJECT_STATUS.md` — the single live status file (template)
The repository already has a `PROJECT_STATUS.md` documenting the **historical build**
(Phases 1–16, all marked DONE). **Do not overwrite that history.** Append a new section to
the top of that same file titled `## v2 TRANSFORMATION STATUS` using this template, and
keep it current:

```markdown
## v2 TRANSFORMATION STATUS
_Last updated: <date> by <session/agent>_

### Current Sprint: <Pre-Sprint 0 | Sprint 1 | ... >
### Maturity Scorecard (this sprint vs baseline)
| Dimension | Baseline | Current | Trend |
|---|---|---|---|
| Product | 52 | … | … |
| Architecture | 64 | … | … |
| Security | 72 | … | … |
| Mobile | 28 | … | … |
| Scalability | 58 | … | … |
| Competitiveness | 40 | … | … |
| **Overall** | **52** | **…** | **…** |

### Sprint Deliverables — Status
| Item | Status | Notes |
|---|---|---|
| … | … | … |

### Open Blockers / Risks (top of Risk Register, §8.4)
| Risk | Tier | Owner | Action |
|---|---|---|---|

### Document Version Table
| Document | Last touched | By |
|---|---|---|

### Next Session Should
1. …
```

### 9.2 Decision Log (ADR-lite — append-only)
Every architecture decision, every conflict resolution beyond the pre-resolved C1–C10
(§5.4), and every deviation from a prior audit recommendation gets one entry. Store in
`docs/decisions/DECISION_LOG.md`:

```markdown
### DEC-<NNN> — <short title>
Date: <date>
Context: <what triggered this decision>
Options considered: <A, B, ...>
Decision: <what was chosen>
Consequence: <what this implies / what it forecloses>
Reference: <which audit doc, conflict ID, or sprint item this relates to>
```

### 9.3 Phase/Sprint handoff document template
At the end of every sprint, generate `docs/phases/SPRINT_<N>_HANDOFF.md`:

```markdown
# SPRINT_<N>_HANDOFF.md
## Scope completed
## Scope deferred (and why)
## Files changed (high level)
## Migrations applied (with downgrade verified Y/N)
## Tests added
## Security self-check result
## Maturity scorecard delta (table from §9.1)
## Tech debt opened / resolved this sprint (IDs)
## Risks opened / closed this sprint
## Decisions logged this sprint (DEC-### references)
## Recommended next sprint entry point
```

### 9.4 Naming & format conventions (match the existing house style — do not deviate)
- Document filenames: `UPPER_SNAKE_CASE.md`.
- Every generated audit/architecture doc ends with a `CHECKPOINT_STATUS` block (phase,
  section, completed list, remaining list, files generated, progress percent) — this
  convention is already established across all 16 Phase 0–D documents; **continue it** for
  any new cross-cutting analysis document (it is not required for routine sprint handoffs,
  which use the §9.3 template instead).
- Tables over prose wherever data has more than 3 comparable items.
- Severity vocabulary stays consistent project-wide: CRITICAL / HIGH / MEDIUM / LOW for
  debt; P0/P1/P2/P3 for priority; S/M/L/XL for effort — never introduce a parallel scheme.

---

## 10. DPDP / COMPLIANCE CHECKLIST (re-verify before go-live and before any new data-collecting feature)
| Requirement | Status at baseline | Action |
|---|---|---|
| Consent at registration (`User.consented_at`) | ✅ | Maintain |
| Age 18+ enforcement | ✅ | Maintain |
| Right to data portability (`/account/export`) | ✅ | Maintain |
| Right to erasure (`/account/delete`, anonymization) | ✅ | Maintain |
| Grievance officer contact in footer | ✅ | Maintain |
| Privacy Policy / Terms pages | ✅ | Keep current with any new data collection (FCM tokens, mobile device IDs) |
| Third-party (family member) data consent | ❌ missing `FamilyDetails.consent_given` | Close before go-live |
| Documented data retention policy | ❌ not written down anywhere in code or docs | Write and link from Privacy Policy before go-live |
| Mobile-specific data disclosures (device ID, FCM token, push permission) | Not yet applicable | Add when Sprint 3/5 ships FCM + mobile app |

---

## 11. OPERATING MODEL — CLAUDE CODE MULTI-AGENT SYSTEM

### 11.1 Why Claude Code for implementation, web/chat for planning
This corpus of 16+6 documents was itself produced effectively in a planning/chat-style
session — that mode is right for audits, architecture documents, and gap analyses, where
the unit of work is "read broadly, reason, write one coherent document." **Implementation
is a different mode of work**: multi-file Python/HTML/JS changes, running migrations,
running tests, iterating against actual error output, and orchestrating specialized
review passes (security, QA) on the same change. That is Claude Code's strength —
persistent filesystem and shell access, git integration, and native subagent delegation.

**Recommendation:** keep using Claude.ai (web/chat) for: architecture review sessions,
new gap-analysis or competitive-research documents, stakeholder-facing reports, and design
decisions that benefit from back-and-forth discussion. **Move to Claude Code** for: every
sprint in §7 starting with Pre-Sprint 0, all migrations, all test-writing, all CI/CD/infra
work, and all mobile app development.

### 11.2 Recommended project structure for Claude Code
```
ijodidar/                          (repo root — delete /ijodidar/ duplicate first!)
├── CLAUDE.md                      (short — points to MASTER_PROMPT.md)
├── MASTER_PROMPT.md                (this document)
├── PROJECT_STATUS.md               (existing build history + new v2 status, §9.1)
├── .claude/
│   └── agents/                     (10 subagent definitions, §11.3 — copy from claude-code-setup/agents/)
├── docs/
│   ├── decisions/DECISION_LOG.md   (§9.2)
│   ├── phases/SPRINT_<N>_HANDOFF.md (§9.3, one per sprint)
│   └── audits/                     (move all 30 existing markdown deliverables here, organized by §4)
├── app/                            (existing Flask app — unchanged structure, additive only)
│   ├── api/                        (NEW — REST API blueprint, §6.1)
│   ├── services/                   (NEW — extracted business logic, Sprint 6)
│   └── models/                      (NEW — domain split target for Sprint 6; models.py stays single-file until then)
└── tests/                          (NEW — does not exist today; created in Pre-Sprint 0 as a smoke harness, expanded every sprint)
```

### 11.3 Recommended Claude Code subagents
Ten specialized subagents, defined as individual files in `.claude/agents/` (full
definitions provided in the companion `claude-code-setup/agents/` folder — copy them in
as-is, they're ready to use). Each agent's system prompt references this `MASTER_PROMPT.md`
as shared context and its own primary source document(s) from §4.

| Agent | Primary responsibility | Primary source docs | Invoked for |
|---|---|---|---|
| `product-architect` | Product vision, feature prioritization, competitive positioning, user-flow specs | `MATRIMONY_GAP_ANALYSIS.md`, `MATRIMONY_PLATFORM_GAP_ANALYSIS.md`, `IDEAL_USER_FLOW.md`, `IDEAL_PROFILE_STRUCTURE.md`, `FEATURE_RATIONALIZATION.md` | New feature scoping, re-prioritization, any "should we build X" question |
| `solution-architect` | Target system architecture, cross-cutting technical decisions, conflict resolution, sprint sequencing validation | `SYSTEM_ARCHITECTURE.md`, `RECOMMENDED_ARCHITECTURE.md`, `iJodidar_v2_Migration_Blueprint.md`, this file §5–§7 | Any decision spanning 2+ subsystems; arbitrating new conflicts; sprint-entry review |
| `ui-ux-architect` | Design system, navigation, wireframes, mobile-first specs, accessibility | `COMPLETE_UI_UX_REDESIGN.md`, `NAVIGATION_ARCHITECTURE.md`, `MOBILE_FIRST_DESIGN_SYSTEM.md`, `SCREEN_BY_SCREEN_WIREFRAMES.md`, `PROFILE_MANAGEMENT_REDESIGN.md` | Any template/CSS/component work; the unified profile editor (Sprint 3) |
| `database-architect` | Schema, migrations, indexing, data-model fixes, scalability thresholds | `DATABASE_ARCHITECTURE.md`, §5.3, §6.4 | Every migration; every new model; every query-performance question |
| `backend-engineer` | Flask routes, Celery tasks, REST API implementation, service-layer extraction | `API_ARCHITECTURE.md`, `MATCHMAKING_ENGINE_ARCHITECTURE.md`, `iJodidar_v2_Migration_Blueprint.md` | All Python implementation work |
| `frontend-engineer` | Templates, JS, CSS, mobile-responsive UI, eventual React Native screens | `MOBILE_FIRST_DESIGN_SYSTEM.md`, `DESIGN_IMPLEMENTATION_PLAN.md`, `MOBILE_ARCHITECTURE.md` | All template/JS/CSS implementation; mobile app screens in Sprint 5 |
| `security-auditor` | Independent review against the security baseline and DPDP checklist before every merge | `SECURITY_ARCHITECTURE.md`, §6.3, §10 | Mandatory review on every new endpoint, every auth change, every data-collection feature, and before any go-live gate item is marked YES |
| `qa-lead` | Test strategy, suite build-out, coverage tracking, regression gating | §8.5, `TECHNICAL_DEBT_REPORT.md` (TD-C01) | Pre-Sprint 0 test harness; every sprint's test additions; pre-merge regression |
| `devops-engineer` | CI/CD, Docker, AWS provisioning, monitoring, deployment runbooks, rollback plans | `AWS_ARCHITECTURE.md`, §6.4, §8.6 | Infra changes, deployment automation, the go-live gate |
| `technical-documentation-specialist` | Keeps `PROJECT_STATUS.md`, Decision Log, sprint handoffs, and API/OpenAPI docs current and consistent with house style | §9 entire, `IMPLEMENTATION_READINESS_REPORT.md`'s reporting style as the standard | End of every sprint; whenever any other agent's output needs to be reflected in the status file or decision log |

### 11.4 Handoff protocol between agents
1. `product-architect` or `solution-architect` scopes the sprint item and confirms its
   prerequisites (§7) are satisfied.
2. `database-architect` lands any schema change first if the item needs one (migrations
   block everything downstream).
3. `backend-engineer` and/or `frontend-engineer`/`ui-ux-architect` implement.
4. `qa-lead` adds/extends tests for the change before it's considered done.
5. `security-auditor` reviews against §6.3/§10 — this is a hard gate, not advisory, for
   anything touching auth, payments, PII, or a new public endpoint.
6. `devops-engineer` handles any deployment/infra implication.
7. `technical-documentation-specialist` updates `PROJECT_STATUS.md`, logs any decisions,
   and writes the sprint handoff doc once the sprint closes.

---

## 12. SESSION CONTINUITY PROTOCOL

**At the start of every session:**
1. Read this `MASTER_PROMPT.md` in full.
2. Read the `## v2 TRANSFORMATION STATUS` section of `PROJECT_STATUS.md` for current sprint
   and open blockers.
3. Read the most recent `docs/phases/SPRINT_<N>_HANDOFF.md`.
4. Skim the Decision Log for anything relevant to the work about to start.
5. Only then open the specific audit document(s) from §4 relevant to the task at hand.

**At the end of every session:**
1. Update `PROJECT_STATUS.md`'s `## v2 TRANSFORMATION STATUS` section.
2. Append any new Decision Log entries.
3. If a sprint closed, write its `SPRINT_<N>_HANDOFF.md`.
4. If new technical debt or risk was discovered, append it to the relevant register (§8.3/§8.4) with a new ID — never overwrite or renumber existing entries.
5. State explicitly, in your final message, what the next session should do first.

---

## 13. APPENDIX A — CONDENSED RISK REGISTER (baseline, from `IMPLEMENTATION_READINESS_REPORT.md`)

| Tier | Risk | Sprint to resolve |
|---|---|---|
| Blocking | Income filter not wired | Pre-Sprint 0 |
| Blocking | Sync email in SocketIO handler | Pre-Sprint 0 |
| Blocking | No Celery Beat → no subscription expiry | Sprint 1 |
| Blocking | No REST API → mobile blocked | Sprint 2 |
| Blocking | Email gate drops 40–60% of registrations | Sprint 1 |
| High | Celery ContextTask refactor could break tasks | Sprint 1 |
| High | SocketIO JWT auth could break web sessions if implemented carelessly | Sprint 2 |
| High | `models.py` split risks import failures — **do last, after tests exist** | Sprint 6 |
| High | JWT misconfiguration | Sprint 2 |
| Medium | Daily digest could send duplicates if Beat misconfigured | Sprint 1 |
| Medium | RDS migration data-loss risk | Sprint 6 |
| Medium | Play Store rejection risk | Sprint 5 |
| Medium | S3 bucket not yet confirmed created | Pre-Sprint 0 |
| Medium | FCM token rotation could silently break push | Sprint 3 |

## 14. APPENDIX B — FIRST TWO WEEKS, DAY BY DAY (from `IMPLEMENTATION_ROADMAP.md`, ready to execute)

| Day | Action |
|---|---|
| 1 | Fix the 3 local-run blockers (missing `manglik_compatible` helper, Flask-Migrate install check, Windows gevent guard in `wsgi.py`); run migrations; verify app boots locally |
| 2 | Deploy fixed code to production EC2; verify live site loads |
| 3 | Wire income filter; add `last_active_at` migration; invite a small group of real test users |
| 4–5 | Set up Sentry (if not already live); start MSG91 DLT registration (3–5 day external lead time — start early); manually verify test users; observe friction points |
| Week 2 | Trust badge on profile cards; per-day pricing on plans page; "New Matches" tab in home feed; Celery Beat + daily match email live |

## 15. APPENDIX C — WHAT NOT TO BUILD (explicit scope exclusions, from `iJodidar_v2_Migration_Blueprint.md`)
- Photo watermarking — low priority, skip for now.
- Background verification (AuthBridge or similar) — business cost decision, not a technical blocker; revisit post-launch.
- WhatsApp Business API expansion — Meta review takes 2+ weeks; only invest once core funnel is fixed.
- Video matrimony events — too early; stabilize the core product first.
- Tinder-style swipe-card gestures — explicitly off-brand for a matrimony product; do not build, regardless of how often it's requested as a "modern UX" pattern.

---

*MASTER_PROMPT.md | iJodidar v2 Enterprise Transformation | Compiled from 30 source documents and direct source-code verification | June 2026*
*This document supersedes no prior audit finding — it indexes and operationalizes them. Update its version header whenever §3 (ground truth) or §7 (roadmap) materially changes.*
