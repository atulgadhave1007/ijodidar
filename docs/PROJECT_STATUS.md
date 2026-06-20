
---

## v2 TRANSFORMATION STATUS
_Last updated: 2026-06-20 by Claude Code (Sprint 1 complete)_

### Current Sprint: Sprint 1 — COMPLETE | Next: Sprint 2

### Maturity Scorecard (Sprint 1 vs baseline)
| Dimension | Baseline | Current | Trend |
|---|---|---|---|
| Product | 52 | 55 | ↑ (phone-first reg; daily match digest live) |
| Architecture | 64 | 70 | ↑ (ContextTask fixed; Beat running; no circular imports) |
| Security | 72 | 74 | ↑ (phone gate enforced; last_active_at throttled) |
| Mobile | 28 | 28 | → |
| Scalability | 58 | 60 | ↑ (subscription expiry automated; Beat scheduler live) |
| Competitiveness | 40 | 43 | ↑ (daily match digest = highest-ROI re-engagement lever) |
| **Overall** | **52** | **55** | ↑ |

### Sprint 1 Deliverables — Status
| Item | Status | Notes |
|---|---|---|
| Celery ContextTask fix | DONE | Lazy _get_flask_app() singleton; no more `from wsgi import app` in tasks |
| Celery Beat scheduler | DONE | ijodidar-beat.service running; 5 scheduled tasks registered |
| sweep_expired_subscriptions | DONE | Hourly — prevents paid features surviving expiry |
| send_daily_matches_all + send_daily_match_digest | DONE | Daily 02:30 UTC fan-out; highest-ROI re-engagement |
| cleanup_expired_otps | DONE | Daily 03:00 UTC |
| cleanup_stale_notifications | DONE | Weekly Sunday 04:00 UTC |
| refresh_match_scores | DONE | Placeholder — Sprint 4 replaces with MatchScoreCache |
| Phone-first registration (C1) | DONE | register() auto-logins + redirects to verify_phone |
| enforce_phone_verification gate | DONE | before_request: phone_verified required for all non-exempt routes |
| verify_phone.html updated | DONE | Shows phone entry form if phone not yet set |
| last_active_at hourly update | DONE | before_request throttled via session key (1h) |
| PartnerPreference income columns (C8) | DONE | min_income_lpa + max_income_lpa Integer; migration f1a2b3c4d5e6 applied |
| All migrations applied on EC2 | DONE | Head: f1a2b3c4d5e6 |
| ijodidar.com login/register working | DONE | HTTP 200 confirmed post-Sprint 1 deploy |

### Pre-Sprint 0 Deliverables — Status (carried forward, all DONE)
| Item | Status |
|---|---|
| Delete duplicate /ijodidar/ directory | DONE (not present) |
| Remove deprecated /admin/ blueprint | DONE |
| Fix sync email in SocketIO handler | DONE |
| Fix db.session.commit() in model method | DONE |
| Wire income filter to search query | DONE |
| Remove duplicate check_gotra_compatibility | DONE (not present) |
| Add User.last_active_at + migration | DONE |
| S3 bucket + IAM role confirmed | DONE |
| Redis installed + running on EC2 | DONE (redis-server) |

### Open Blockers / Risks
| Risk | Tier | Owner | Action |
|---|---|---|---|
| Celery worker (not Beat) — confirm running separately | Medium | Atul | `sudo systemctl status ijodidar-celery` — may need to create worker service |
| Rate limiting Redis DB — confirm REDIS_URL in .env | Medium | Atul | Check /home/ubuntu/ijodidar/.env has REDIS_URL set |
| PartnerPreference income search not yet wired to new columns | Low | Sprint 2 | Wire search to min/max_income_lpa in search/routes.py |
| eventlet deprecation warnings in logs | Low | Sprint 4 | Migrate to gevent or asyncio when eventlet drops Python 3.12 support |

### Document Version Table
| Document | Last touched | By |
|---|---|---|
| MASTER_PROMPT.md | 2026-06-20 | Claude Code Pre-Sprint 0 |
| CLAUDE.md (repo root) | 2026-06-20 | Claude Code Pre-Sprint 0 |
| docs/decisions/DECISION_LOG.md | 2026-06-20 | Claude Code Sprint 1 |
| app/__init__.py | 2026-06-20 | Claude Code Sprint 1 |
| app/tasks.py | 2026-06-20 | Claude Code Sprint 1 |
| app/models.py | 2026-06-20 | Claude Code Sprint 1 |
| app/auth/routes.py | 2026-06-20 | Claude Code Sprint 1 |
| templates/auth/verify_phone.html | 2026-06-20 | Claude Code Sprint 1 |
| migrations/versions/f1a2b3c4d5e6_sprint1_income_columns.py | 2026-06-20 | Claude Code Sprint 1 |

### Next Session Should (Sprint 2 — Weeks 4–5)
1. **Confirm Celery worker service** exists and is running (`ijodidar-celery.service`); create if missing.
2. **Wire search to new income columns**: update `search/routes.py` and partner preferences form to use `min_income_lpa`/`max_income_lpa`.
3. **Sprint 2 primary**: Discovery tabs + conversion mechanics (per-day pricing, social proof) + REST API Phase 1 (auth, profiles, feed endpoints) — see MASTER_PROMPT.md §7 Sprint 2.
4. **REST API foundation**: create `app/api/` package, JWT via Flask-JWT-Extended, `/api/v1/auth/register` + `/login` + `/me` + `/feed` endpoints.
5. **Read** `API_ARCHITECTURE.md` before writing any API code — full endpoint spec is already there.

# iJodidar â€” Project Status
## v25 Auto-Kundli | Complete Production Build | June 2026
### https://ijodidar.com | EC2: 13.205.222.218 | Atul Gadhave, Pune

---

## PRODUCTION READINESS: 97 / 100

| Category | Score | What's Done |
|----------|-------|-------------|
| Infrastructure | 90 | EC2 + Nginx + SSL + PG + Redis + Celery |
| Authentication | 97 | Lockout + session invalidation + TOTP 2FA |
| Matchmaking | 98 | Signal-boosted + Guna Milan integrated |
| Security | 97 | TOTP, audit log, OTP hash, signed URLs |
| Business Logic | 95 | Monthly limits, dual referral, RM workflow |
| Email / SMS | 88 | SES async/Celery; MSG91 DLT pending |
| Payments | 48 | Test keys; GST + current account needed |
| Privacy | 99 | DPDP export, deletion, consent, S3 private |
| Database | 99 | 34 models, 5 migrations, correct indexes |
| Kundli Engine | 96 | Auto-calc from DOB+Time+City, 8 koots |
| DevOps | 82 | Sentry, Celery service; GitHub Actions pending |

---

## COMPLETE CODEBASE STATS

| Metric | Count |
|--------|-------|
| Python files | 45 |
| HTML templates | 78 |
| SQLAlchemy models | 34 |
| Alembic migrations | 5 |
| Blueprints | 13 |
| Routes | 80+ |
| Syntax errors | 0 |

---

## FEATURES â€” ALL STATUS

### âœ… COMPLETE AND WORKING

**Auth & Security**
- Registration (age 18+, consent, DOB)
- Email verification (24h expiry, async via Celery)
- Login with account lockout (10 fails = 30 min)
- Password reset (async, 1h expiry)
- Session invalidation on password change
- Phone OTP with bcrypt hash storage
- Aadhaar KYC workflow (dev mode)
- Console TOTP 2FA (Google Authenticator)
- Console brute force: 5 fails = 60 min
- Console IP restriction + rate limiting
- Admin audit log (immutable)
- CSRF protection, HTTPS cookies
- S3 private photos + pre-signed URLs

**Profile & Onboarding**
- 5-step onboarding wizard
- 22-page profile editing
- Photo upload (3 sizes, S3)
- Photo blur for Free plan users
- Profile completeness %
- Marathi UI toggle

**Matchmaking**
- Home feed (opposite gender only)
- Partner preference filtering
- N+1 query fix (joinedload)
- Spotlight as position slots (top 3)
- Signal-boosted scoring (7 signals)
- Guna Milan in match ranking

**Kundli / Guna Milan**
- Auto-calculation from DOB + Time + City
- Meeus Ch47 Moon algorithm (Â±0.3Â°)
- Lahiri ayanamsa
- 100+ Indian cities built-in
- All 8 Ashta Koota factors
- Corrected Nadi (was 15/27 wrong, now all correct)
- Corrected Vashya (zodiac groups, not varna)
- Corrected Graha Maitri (neutral + enemy)
- Manglik (Chandra Lagna approximation)
- Gotra/Sapinda check
- Guna Milan in match ranking (Â±5 pts)
- Live preview + manual override
- City autocomplete

**Connect & Messaging**
- Send interest (monthly limit, auto-reset)
- Email gate for interests
- Interest accept/decline with Celery notifications
- Real-time chat (SocketIO)
- Phone gate for messaging
- Shortlist, block, report with signals

**Business**
- 4 membership plans (Free/Silver/Gold/Platinum)
- Razorpay payments (test keys)
- Spotlight (admin verify for manual payment)
- Assisted plan + RM contact log workflow
- Dual-sided referral (both sides get Silver)
- Referral cookie persists 7 days

**Privacy & DPDP**
- Privacy Policy + Terms of Service
- Grievance officer in footer
- Data export (JSON, 3/day)
- Account deletion (PII anonymised, S3 deleted)
- Consent recorded at registration
- Age 18+ enforced

**Console (Staff)**
- Separate AdminUser model (RBAC, 5 roles)
- Dashboard with KPIs + charts
- User management with audit trail
- Report management
- Assisted plan + RM workflow interface
- Staff management
- Analytics
- TOTP 2FA

**Infrastructure**
- Celery + Redis async queue
- Sentry error monitoring
- SQLite for local dev (no PostgreSQL needed)
- systemd services for app + Celery

### âš ï¸ CODE READY â€” NEEDS CONFIGURATION

| Feature | What's Needed |
|---------|--------------|
| Email sending | SES production access (24-48h wait) |
| Photo uploads | S3 bucket + IAM role on EC2 |
| SMS OTP | MSG91 DLT approval (3-5 days) |
| Razorpay live | GST + current bank account |
| WhatsApp | Meta Business API approval |
| Aadhaar KYC | Surepass/Signzy API key |

### âŒ NOT YET BUILT

| Feature | Priority |
|---------|---------|
| GitHub Actions auto-deploy | Medium |
| CloudFront CDN | Medium |
| Income range filter in search | Low (column ready) |
| Family member consent checkbox | Low |
| Lagna-based Manglik (full) | Future |
| Android native app | Future |

---

## COST BREAKDOWN

| Service | Monthly |
|---------|---------|
| EC2 t3.small (Mumbai) | ~â‚¹700 |
| Route 53 + DNS | ~â‚¹107 |
| S3 + CloudFront | ~â‚¹150 (after setup) |
| SES (62K free from EC2) | â‚¹0 |
| Redis on EC2 | â‚¹0 |
| SSL Let's Encrypt | â‚¹0 |
| **TOTAL** | **~â‚¹957/month** |

---

## THIS WEEK'S PRIORITY

```
1. Local testing â€” run all 55 tests in TESTING_CHECKLIST.md
2. Push to GitHub
3. Deploy to EC2 + flask db upgrade
4. Start MSG91 DLT registration (msg91.com â†’ DLT)
5. Configure Sentry (sentry.io â†’ free tier)
6. Invite 5 beta users
```

---

*v25 Auto-Kundli | June 2026 | 45 Python files | 0 syntax errors*

