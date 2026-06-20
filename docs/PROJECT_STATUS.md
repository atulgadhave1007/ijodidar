
---

## v2 TRANSFORMATION STATUS
_Last updated: 2026-06-20 by Claude Code (Pre-Sprint 0 session)_

### Current Sprint: Pre-Sprint 0 — COMPLETE

### Maturity Scorecard (this sprint vs baseline)
| Dimension | Baseline | Current | Trend |
|---|---|---|---|
| Product | 52 | 52 | → (no product changes yet) |
| Architecture | 64 | 65 | ↑ (admin blueprint removed; async email fixed) |
| Security | 72 | 72 | → |
| Mobile | 28 | 28 | → |
| Scalability | 58 | 58 | → |
| Competitiveness | 40 | 40 | → |
| **Overall** | **52** | **52** | → (Pre-Sprint 0 is housekeeping; scores move in Sprint 1+) |

### Sprint Deliverables — Status
| Item | Status | Notes |
|---|---|---|
| 1. Delete duplicate /ijodidar/ directory | DONE | Not present in this working copy; verify on EC2 (DEC-001) |
| 2. Remove deprecated /admin/ blueprint | DONE | app/admin/ deleted; templates/admin/ deleted; __init__.py registration removed |
| 3. Fix sync email in SocketIO handler | DONE | socket_events.py: send_email() → send_message_email_task.delay() |
| 4. Fix db.session.commit() in model method | DONE | UserSubscription.interests_remaining(): commit removed; caller responsibility |
| 5. Wire income filter to search query | DONE | search/routes.py: ProfessionalDetails.income_lpa range filter added |
| 6. Remove duplicate check_gotra_compatibility | DONE | Not present; only one definition exists (DEC-002) |
| 7. Add User.last_active_at + migration | DONE | Column added to models.py; migration a1b2c3d4e5f6 created |
| CLAUDE.md at repo root | DONE | Copied from claude-code-setup/CLAUDE.md |
| docs/decisions/DECISION_LOG.md created | DONE | 3 entries logged |
| docs/phases/ and docs/decisions/ created | DONE | Governance structure in place |

### Open Blockers / Risks (top of Risk Register, §8.4)
| Risk | Tier | Owner | Action |
|---|---|---|---|
| S3 bucket + IAM role not confirmed operational | Medium | Atul | Confirm before Sprint 1 deploy |
| Rate limiting Redis-backed (not in-memory) — unconfirmed | Medium | Atul | Verify limiter storage_uri in config.py |
| Duplicate /ijodidar/ may exist on EC2 repo | Medium | Atul | Check on EC2 before next deployment |
| Migration a1b2c3d4e5f6 not yet applied to DB | Blocking (for last_active_at) | Dev | Run: flask db upgrade |

### External Go/No-Go conditions (from §7.1)
| Condition | Status |
|---|---|
| S3 bucket + IAM role operational | ❓ Unconfirmed — verify manually |
| Redis-backed rate limiting confirmed | ❓ Unconfirmed — check config.py RATELIMIT_STORAGE_URI |
| Sprint 1 lead has read MASTER_PROMPT.md §3–§7 | ✅ Current session lead confirmed |

### Document Version Table
| Document | Last touched | By |
|---|---|---|
| MASTER_PROMPT.md | 2026-06-20 | Claude Code Pre-Sprint 0 |
| CLAUDE.md (repo root) | 2026-06-20 | Claude Code Pre-Sprint 0 |
| docs/decisions/DECISION_LOG.md | 2026-06-20 | Claude Code Pre-Sprint 0 |
| app/__init__.py | 2026-06-20 | Claude Code Pre-Sprint 0 |
| app/messaging/socket_events.py | 2026-06-20 | Claude Code Pre-Sprint 0 |
| app/models.py | 2026-06-20 | Claude Code Pre-Sprint 0 |
| app/search/routes.py | 2026-06-20 | Claude Code Pre-Sprint 0 |
| migrations/versions/a1b2c3d4e5f6_add_user_last_active_at.py | 2026-06-20 | Claude Code Pre-Sprint 0 |

### Next Session Should
1. **Apply the migration on the target database**: `flask db upgrade` (adds `users.last_active_at` column).
2. **Verify on EC2**: check whether `/ijodidar/` duplicate directory exists there (`ls ~/ijodidar/` or equivalent) — delete it if found.
3. **Confirm Redis-backed rate limiting**: check `config.py` for `RATELIMIT_STORAGE_URI`; must point to Redis, not in-memory.
4. **Confirm S3 bucket + IAM role**: verify `AWS_S3_BUCKET` env var resolves to a real, accessible bucket.
5. **Start Sprint 1**: Celery Beat + ContextTask fix + phone-first registration + trust-tier properties + PartnerPreference income columns (§7, Sprint 1).

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

