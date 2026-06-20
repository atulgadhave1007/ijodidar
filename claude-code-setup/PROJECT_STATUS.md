# iJodidar — Project Status Tracker
## Auto-updated after each phase completion

---

## v2 TRANSFORMATION STATUS
_Last updated: June 2026 — initialized from the completed Enterprise Transformation Audit
(Phases 0–D, 16 documents) and the Founder/Competitive gap analysis (6 documents). See
`MASTER_PROMPT.md` for the full governing charter._

### Current Sprint: Pre-Sprint 0 (not yet started)

### Maturity Scorecard (baseline)
| Dimension | Baseline | Current | Trend |
|---|---|---|---|
| Product | 52 | 52 | — |
| Architecture | 64 | 64 | — |
| Security | 72 | 72 | — |
| Mobile | 28 | 28 | — |
| Scalability | 58 | 58 | — |
| Competitiveness | 40 | 40 | — |
| **Overall** | **52** | **52** | **—** |

### Sprint Deliverables — Status
| Item | Status | Notes |
|---|---|---|
| Delete `/ijodidar/` duplicate directory | NOT STARTED | Pre-Sprint 0, item 1 |
| Remove deprecated `/admin/` blueprint + templates | NOT STARTED | Pre-Sprint 0, item 2 |
| Fix sync email in SocketIO message handler | NOT STARTED | Pre-Sprint 0, item 3 |
| Fix `db.session.commit()` inside model property | NOT STARTED | Pre-Sprint 0, item 4 |
| Wire income filter into search query | NOT STARTED | Pre-Sprint 0, item 5 |
| Remove duplicate `check_gotra_compatibility` definition | NOT STARTED | Pre-Sprint 0, item 6 |
| Add `User.last_active_at` column + migration | NOT STARTED | Pre-Sprint 0, item 7 |
| Confirm S3 bucket + IAM role operational | NOT STARTED | External condition for Sprint 1 start |
| Confirm Redis-backed (not in-memory) rate limiting | NOT STARTED | External condition for Sprint 1 start |

### Open Blockers / Risks (top of Risk Register — see `MASTER_PROMPT.md` §13 for full list)
| Risk | Tier | Owner | Action |
|---|---|---|---|
| Income filter not wired | Blocking | Unassigned | Pre-Sprint 0 |
| Sync email in SocketIO handler | Blocking | Unassigned | Pre-Sprint 0 |
| No Celery Beat → no subscription expiry enforcement | Blocking | Unassigned | Sprint 1 |
| No REST API → mobile app blocked | Blocking | Unassigned | Sprint 2 |
| Email gate drops 40–60% of registrations | Blocking | Unassigned | Sprint 1 |

### Document Version Table
| Document | Last touched | By |
|---|---|---|
| `MASTER_PROMPT.md` | June 2026 | Initial compilation from all 30 source documents |
| `docs/decisions/DECISION_LOG.md` | June 2026 | Seeded with DEC-001–DEC-010 (Conflict Matrix C1–C10) |
| All 30 audit/redesign documents | June 2026 | Imported as-is into `docs/audits/` — see `MASTER_PROMPT.md` §4 |

### Next Session Should
1. Read `MASTER_PROMPT.md` in full if not already done this session.
2. Confirm the two external Pre-Sprint 0 conditions (S3/IAM, Redis-backed rate limiting).
3. Execute the 7 Pre-Sprint 0 cleanup items (`MASTER_PROMPT.md` §7.1), starting with deleting
   the `/ijodidar/` duplicate directory.
4. Stand up the minimal pytest smoke-test harness (owned by `qa-lead`) — this has no
   prerequisites and should happen in parallel with the cleanup items.
5. Update this section and write `docs/phases/PRE_SPRINT_0_HANDOFF.md` once the above is done.

---

## HISTORICAL BUILD LOG (Phases 1–16 — pre-transformation, do not edit below this line)

## PHASE STATUS

| Phase | Name | Status |
|-------|------|--------|
| 1  | Project structure, models, config | ✅ DONE |
| 2  | Auth, profile edit pages, S3 upload | ✅ DONE |
| 3  | Connect/Interest, Messaging, Membership, Admin, Family, Search | ✅ DONE |
| 4  | Advanced search, Partner prefs, Landing page, Photo privacy, Block/Report, Profile hide | ✅ DONE |
| 5  | Match algorithm, Email triggers, Real-time chat (SocketIO), Notification bell | ✅ DONE |
| 6  | Razorpay payments, Phone OTP, Trust badges, Image thumbnails | ✅ DONE |
| 7  | PWA manifest, Mobile bottom nav, SEO/sitemap, Success stories, auth/forms fix | ✅ DONE |
| 8  | Refer & Earn, Spotlight profiles, Admin analytics, Manglik compatibility | ✅ DONE |
| 9  | Error pages, seed admin user, check_migrations.py, final README, LOCAL_DEV_GUIDE | ✅ DONE |
| 10 | UI Redesign Phase 1 — base.html, home, login, register, inbox | ✅ DONE |
| 11 | UI Redesign Phase 2 — landing, search, interests, profile settings, plans, edit pages | ✅ DONE |
| 12 | Maharashtra competitor features — sub-castes, Gotra, Kundli/Guna Milan, ID verify, Hobbies, NRI | ✅ DONE |
| 13 | WebRTC voice/video calling, Marathi UI toggle, Play Store TWA guide | ✅ DONE |
| 14 | Full Marathi UI, Aadhaar ID verification, WhatsApp Business API, Assisted Plan | ✅ DONE |
| 15 | Git + CI/CD + Full EC2 Deployment Guide + Windows Dev Guide | ✅ DONE |
| **16** | **Staff Business Console — AdminUser model, role-based access, CEO/VP/RM/Executive, is_staff flag, /console/ portal** | ✅ DONE |

---

## PHASE 16 — WHAT WAS BUILT

### Problem Solved
Admin staff were registered as regular users — they appeared in search results, were counted in user stats, and could be matched with real users. Completely wrong.

### Solution Architecture
| Component | Details |
|-----------|---------|
| `AdminUser` model | Completely separate DB table from `User`. Staff are NOT matchmaking users. Has role + permissions + last_login |
| `User.is_staff` flag | Any legacy User who was acting as admin gets flagged — excluded from all feeds, stats, search |
| `/console/` blueprint | Separate URL space. Own login. Own dark-theme UI. Never uses Flask-Login sessions (uses console session key) |
| Role-based permissions | CEO > VP > Business Owner > Relationship Manager > Executive. Each role has a specific permission set |
| Staff excluded from stats | ALL admin/analytics queries filter `User.is_staff == False` |
| Staff excluded from search | Search and home feed filter `User.is_staff == False` |

### Role Permission Matrix
| Permission | CEO | VP | Biz Owner | RM | Executive |
|------------|-----|----|-----------|----|-----------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Analytics | ✅ | ✅ | ✅ | ❌ | ❌ |
| Revenue | ✅ | ❌ | ✅ | ❌ | ❌ |
| User Management | ✅ | ✅ | ❌ | ❌ | ✅ |
| Plans | ✅ | ❌ | ✅ | ❌ | ❌ |
| Reports | ✅ | ✅ | ✅ | ❌ | ✅ |
| Assisted Plans | ✅ | ✅ | ❌ | ✅ | ❌ |
| Staff Management | ✅ | ❌ | ❌ | ❌ | ❌ |

### Console Pages Built (9 templates)
| Page | URL | Description |
|------|-----|-------------|
| Login | /console/login | Dark professional login — separate from user login |
| Dashboard | /console/ | KPI cards, sparkline, gender split, plan dist, quick actions, live refresh |
| Analytics | /console/analytics | Registration chart, revenue chart, plan doughnut, interest funnel |
| Users | /console/users | Paginated, filterable, searchable — staff never shown |
| User Detail | /console/users/<id> | Full profile, suspend/activate, grant badges, send notes |
| Reports | /console/reports | Moderation queue with status tabs |
| Assisted | /console/assisted | RM-focused — RMs only see their own assignments |
| Staff | /console/staff | CEO-only — add/deactivate staff, role reference table |

### seed.py
Added `seed_console_ceo()` — set `CONSOLE_CEO_EMAIL` + `CONSOLE_CEO_PASSWORD` env vars.


---

## 🏁 ALL 15 PHASES COMPLETE — FULLY DEPLOYMENT-READY

---

## PHASE 15 — WHAT WAS BUILT

| Item | Details |
|------|---------|
| .gitignore | Complete — secrets, venv, instance/, __pycache__, logs, uploads excluded |
| requirements.txt | Production (Linux): gunicorn + gevent + psycopg2 |
| requirements-windows.txt | Dev (Windows): no gunicorn/gevent, uses SQLite |
| .github/workflows/deploy.yml | GitHub Actions: syntax check → SSH into EC2 → git pull → pip install → flask db upgrade → restart |
| DEPLOYMENT_GUIDE.md | 596-line complete guide: EC2, RDS, S3, Nginx, SSL, Cloudflare, GitHub Actions, troubleshooting |
| LOCAL_DEV_GUIDE_WINDOWS.md | 295-line Windows-specific dev guide with every error fixed |

## DEPLOYMENT PLAN (Your Plan)
1. `git push` to GitHub → GitHub Actions auto-deploys to EC2
2. Set all keys in `/home/ubuntu/ijodidar/.env` on EC2 once
3. Every future `git push` = automatic deployment in ~60 seconds


---

## 🎉 ALL 14 PHASES COMPLETE — PROJECT IS PRODUCTION-READY

---

## FINAL CODEBASE SUMMARY
- **33 Python files** — all syntax clean, 0 errors
- **56 HTML templates** — all complete
- **29 DB models** — AssistedRequest added in Phase 14
- **11 Blueprints** — auth, profile, family, search, connect, messaging, membership, admin, main, notifications, kundli
- **3 Utility files** — utils.py, utils_kundli.py, translations/mr/messages.py
- **Guides** — LOCAL_DEV_GUIDE.md, PLAYSTORE_TWA_GUIDE.md, email_otp_setup_guide.md, README.md

---

## PHASE 14 — WHAT WAS BUILT

| Item | Status | Details |
|------|--------|---------|
| 14.1 Full Marathi UI | ✅ | translations/mr/messages.py — 100+ UI strings. Loaded dynamically at startup. `t()` filter applies across all templates. Save/Cancel/Search/Filters/Plans/Sections all translated |
| 14.1 Translation system | ✅ | No Babel dependency — custom dict system. File-based for easy expansion. Session + DB persistent |
| 14.2 Aadhaar OTP route | ✅ | `GET/POST /verify-id` — 2-step: enter Aadhaar → OTP sent → verify → badge granted |
| 14.2 send_aadhaar_otp() | ✅ | utils.py — dev mode: any 12-digit number + 6-digit OTP works (console log). Prod: Surepass API |
| 14.2 verify_aadhaar_otp() | ✅ | utils.py — verifies OTP, grants id_verified badge, sends in-app notification |
| 14.2 verify_id.html | ✅ | 156-line beautiful 2-step UI with privacy note, dev mode hint, OTP entry |
| 14.2 config.py | ✅ | KYC_API_KEY, KYC_PROVIDER keys added |
| 14.3 send_whatsapp() | ✅ | utils.py — Meta Business API. Dev mode: console log. Prod: template messages |
| 14.3 WhatsApp — interest received | ✅ | Fires in connect/routes.py on send_interest |
| 14.3 WhatsApp — interest accepted | ✅ | Fires in connect/routes.py on respond_interest |
| 14.3 WhatsApp — new message | ✅ | Fires in messaging/routes.py |
| 14.3 config.py | ✅ | WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID keys added |
| 14.4 AssistedRequest model | ✅ | user_id, manager, notes, status, curated_profiles, created_at |
| 14.4 /plans/assisted route | ✅ | Signup page, notifies admin on request, creates AssistedRequest record |
| 14.4 assisted.html | ✅ | 129-line beautiful plan page — features, Assisted vs Platinum comparison table |
| 14.4 admin/assisted.html | ✅ | 152-line admin view — stats strip, modal to assign manager, update status, add notes |
| 14.4 /admin/assisted routes | ✅ | List + update_assisted routes with notification on activation |
| 14.4 plans.html | ✅ | Purple Assisted Plan banner added above trust row |
| 14.4 profile.html | ✅ | ID Verification row added to Privacy section |
| 14.4 admin/dashboard.html | ✅ | Assisted Plans link added |

---

## COMPLETE FEATURE LIST (All 14 Phases)

| Category | Features |
|----------|---------|
| Auth | Register, Login, Email verify, Phone OTP, Forgot/Reset password, Aadhaar ID verification (self-service) |
| Profile | 23 edit pages, Religion/Marathi sub-caste/Gotra, Kundli/Nakshatra, Hobbies (30), NRI, Photos, Partner prefs, Privacy, Language (EN/मराठी) |
| Matchmaking | Interest flow, Shortlist, Block/Report, 10-factor match score, Guna Milan (0-36 Ashtakoot) |
| Communication | Real-time chat (SocketIO), WebRTC video/voice calls (Gold+), WhatsApp Business notifications |
| Search | 13 filters incl. Marathi sub-caste + NRI |
| Membership | Free/Silver/Gold/Platinum/Assisted, Razorpay, Spotlight ₹199/week |
| Trust | Email ✅, Phone 🛡️, Aadhaar ID 🆔, NRI 🌐, Manglik, Gotra Sapinda check |
| Refer & Earn | IJD-XXXXXX code, Auto-reward Silver |
| Notifications | Bell dropdown + WhatsApp on all key events |
| Family Tree | 10 categories, 42+ relation types |
| Kundli | Guna Milan 8-koot, Gotra compat, Nadi Dosha warning |
| Admin | Dashboard, Users + ID verify, Plans, Reports, Stories, Analytics, Assisted Plan management |
| SEO & PWA | PWA, robots.txt, Sitemap, OG tags, Mobile bottom nav |
| Multilingual | Marathi UI — 100+ strings, session + DB persistent |
| Assisted Plan | ₹2,999/month relationship manager tier — request flow + admin management |

---

## ENV VARS — COMPLETE REFERENCE

```env
# Required
SECRET_KEY=...
FLASK_ENV=development|production
ADMIN_EMAILS=you@email.com

# Database
DATABASE_URL=postgresql://...   # blank = SQLite for dev

# AWS S3 + SES
AWS_REGION=ap-south-1
AWS_S3_BUCKET=ijodidar-images
MAIL_FROM=noreply@ijodidar.in

# Razorpay
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...

# MSG91 (Phone OTP)
MSG91_AUTH_KEY=...
MSG91_SENDER_ID=IJODDR
MSG91_TEMPLATE_ID=...

# Aadhaar KYC (Phase 14.2)
KYC_API_KEY=...        # blank = dev mode (any OTP passes)
KYC_PROVIDER=surepass

# WhatsApp Business (Phase 14.3)
WHATSAPP_TOKEN=...     # blank = dev mode (console log)
WHATSAPP_PHONE_NUMBER_ID=...

# Admin user via seed.py
ADMIN_EMAIL=you@email.com
ADMIN_PASSWORD=YourStrongPassword
```

---

## MONTHLY COST AT 10K USERS
| Service | Cost |
|---------|------|
| EC2 t3.small | ~₹700/mo |
| RDS t3.micro PostgreSQL | ~₹700/mo |
| AWS S3 (15GB + transfer) | ~₹150/mo |
| Cloudflare | ₹0 |
| MSG91 SMS (est. 2K OTPs) | ~₹400 one-time |
| Surepass KYC (est. 500 verif.) | ~₹5,000 one-time |
| WhatsApp (1K conv free/mo) | ₹0 initially |
| **Total recurring** | **~₹1,550/mo** |
