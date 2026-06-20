# iJodidar — Implementation Tracker
## All Phases | June 2026

---

## PHASE COMPLETION SUMMARY

| Phase | Focus | Status | Score Impact |
|-------|-------|--------|-------------|
| Phase 1–4 | Bug fixes, security, auth, DB indexes | ✅ Complete | 52→76 |
| Strategic Phase 1 | Celery, Sentry, onboarding, spotlight fix | ✅ Complete | 76→88 |
| Strategic Phase 2 | Wizard, photo blur, audit log, DOB Date, S3 | ✅ Complete | 88→93 |
| Strategic Phase 3 | TOTP, signals, referral, RM workflow, export | ✅ Complete | 93→97 |
| Kundli v1 | Manual Nakshatra entry, 8-koot Guna Milan | ✅ Complete | — |
| Kundli v2 | Nadi/Vashya/Graha Maitri corrections | ✅ Complete | — |
| Kundli v3 | Auto-calculation from DOB+Time+City | ✅ Complete | — |
| **TOTAL** | | **97 / 100** | |

---

## COMPLETED ITEMS — DETAILED

### Authentication & Security
- [x] Registration with age 18+, consent, DOB → Profile
- [x] Email verification with 24h token expiry
- [x] Login with account lockout (10 fails = 30 min)
- [x] Forgot password (async email via Celery)
- [x] Password reset with token expiry
- [x] Session invalidation on password change
- [x] Phone OTP with bcrypt hash storage
- [x] Aadhaar verification workflow (dev mode)
- [x] Console TOTP 2FA (Google Authenticator)
- [x] Console brute force: 5 fails = 60 min
- [x] Console IP restriction (CONSOLE_ALLOWED_IPS)
- [x] Console rate limiting (10/min)
- [x] Open redirect prevention in login
- [x] CSRF protection on all forms
- [x] SECRET_KEY validation at startup
- [x] HTTPS session cookies (production config)
- [x] S3 photos uploaded as private
- [x] Pre-signed URLs for photo access

### Profile & Onboarding
- [x] 5-step onboarding wizard (gender → basics → career → photo → prefs)
- [x] Before_request gate: redirects to onboarding if no gender/looking_for
- [x] 22-page profile editing (all sections)
- [x] Photo upload to S3 (3 sizes: 800px, 400px, 150px)
- [x] Photo blur for Free plan (home feed + search)
- [x] Profile completeness percentage
- [x] Marathi UI toggle (en/mr)

### Matchmaking
- [x] Home feed filtered by looking_for (opposite gender)
- [x] Partner preference filtering (religion, marital status, age)
- [x] Spotlight as position slots (top 3), not score inflation
- [x] N+1 query fix (joinedload on home feed)
- [x] Signal-boosted match scoring (7 signal types)
- [x] Guna Milan integrated into match ranking (±5 points)
- [x] Collaborative filtering: accept/decline signals improve next suggestions
- [x] "New matches" not shown repetitively (viewed profiles deprioritised)

### Connect & Messaging
- [x] Send interest with monthly limit
- [x] Monthly interest auto-reset
- [x] Email gate: must verify email before sending interest
- [x] Interest accept/decline with email notification (async)
- [x] Conversation created on accept
- [x] Phone gate: must verify phone before messaging
- [x] Real-time chat (SocketIO)
- [x] Message email notification (async via Celery)
- [x] Shortlist with signal recording
- [x] Block/unblock with signal recording
- [x] Report user with signal recording

### Kundli / Guna Milan
- [x] Auto-calculation from DOB + Time + City (no external API)
- [x] Jean Meeus Chapter 47 Moon algorithm (±0.3° accuracy)
- [x] Lahiri ayanamsa (standard Indian Vedic)
- [x] 100+ Indian cities built-in, Nominatim fallback
- [x] All 8 Ashta Koota factors calculated
- [x] Corrected Nadi assignments (15/27 were wrong — now correct)
- [x] Corrected Vashya method (zodiac groups, not varna)
- [x] Corrected Graha Maitri (neutral + enemy scoring)
- [x] Manglik (approximate via Chandra Lagna)
- [x] Gotra / Sapinda check
- [x] Guna Milan in match ranking (28+ = +5 pts, <18 = -3 pts)
- [x] Live preview (AJAX) before saving
- [x] Manual override for users with paper kundli
- [x] City autocomplete API

### Membership & Payments
- [x] 4 plans: Free / Silver / Gold / Platinum
- [x] Razorpay integration (test keys)
- [x] Payment webhook with dedicated webhook secret
- [x] Spotlight feature (position slots, admin verify for manual payment)
- [x] Assisted plan with RM workflow
- [x] RM contact log (call, email, WhatsApp, meeting, outcome)

### Referral
- [x] Referral code generation per user
- [x] Referral cookie persists 7 days (not just URL param)
- [x] Dual-sided reward (referrer: 30-day Silver, referred: 15-day Silver)
- [x] Both rewards gated behind email AND phone verification
- [x] Fraud prevention: IP tracking, duplicate check

### Privacy & DPDP
- [x] Privacy Policy page (/privacy-policy)
- [x] Terms of Service (/terms)
- [x] Grievance officer in footer (all pages)
- [x] Data export (JSON, 3/day limit)
- [x] Account deletion (anonymises PII, deletes S3 photos)
- [x] Consent recorded at registration
- [x] Age 18+ enforced (form + server)

### Console (Staff)
- [x] Separate AdminUser model (not regular User accounts)
- [x] RBAC: 5 roles (ceo, manager, executive, rm, moderator)
- [x] Dashboard with KPIs
- [x] User management (activate, suspend, ID verify, note)
- [x] Report management (dismiss, suspend reported user)
- [x] Assisted plan management with RM workflow
- [x] Contact log interface
- [x] Staff management (add, deactivate)
- [x] Analytics (registrations, conversions, revenue)
- [x] Audit log (all actions with who/when/what/IP)
- [x] TOTP 2FA setup and verification
- [x] IP-restricted access

### Infrastructure
- [x] Celery + Redis async task queue
- [x] All emails sent async (no more blocking/hanging)
- [x] Sentry error monitoring
- [x] Redis rate limiting (shared across workers)
- [x] Systemd service for Celery worker
- [x] ProxyFix for Nginx
- [x] SQLite for local dev (no PostgreSQL needed)
- [x] PostgreSQL for production

---

## PENDING ITEMS

### 🔴 Business Blockers

| # | Item | Owner | Depends On |
|---|------|-------|-----------|
| 1 | GST registration | Atul | Nothing |
| 2 | Razorpay current account | Atul | GST |
| 3 | Razorpay live KYC | Atul | GST + account |
| 4 | MSG91 DLT registration | Atul | Udyam cert ✅ |
| 5 | MSG91 sender ID + template | Atul | DLT approved |

### 🟡 Technical (Week 2)

| # | Item | Effort |
|---|------|--------|
| 6 | GitHub Actions auto-deploy | 2h |
| 7 | UptimeRobot monitoring | 15 min |
| 8 | S3 bucket + IAM role setup | 30 min |
| 9 | AWS SES production access | 2h setup + 48h wait |
| 10 | Log rotation | 15 min |

### 🟢 Future Features (Month 2-3)

| # | Item | Effort |
|---|------|--------|
| 11 | CloudFront CDN for S3 | 2h |
| 12 | WhatsApp Business API | 1 week (Meta review) |
| 13 | Aadhaar KYC live (Surepass) | 3h code + account |
| 14 | Trademark filing (Class 45+42) | 20 min + ₹9,000 |
| 15 | Shop & Establishment registration | 1h |
| 16 | Full Lagna-based Manglik (birth time required) | 4h |
| 17 | Daily match digest email (APScheduler/Celery beat) | 4h |
| 18 | Android native app (TWA → Play Store) | See PLAYSTORE_TWA_GUIDE.md |
| 19 | Income range filter in search | 2h (income_lpa column ready) |
| 20 | Family member consent checkbox | 2h |
| 21 | Background check integration (AuthBridge) | 1 week |
| 22 | Pvt Ltd company registration | At milestone |

---

## NEXT IMMEDIATE ACTIONS (This Week)

```
1. [ ] Push v25 code to GitHub
       git add . && git commit -m "v25 auto-kundli complete" && git push

2. [ ] Deploy to EC2
       ssh ubuntu@13.205.222.218
       cd ~/ijodidar && git pull && flask db upgrade
       sudo systemctl restart ijodidar ijodidar-celery

3. [ ] Install Celery worker service
       sudo cp celery.service /etc/systemd/system/ijodidar-celery.service
       sudo systemctl enable ijodidar-celery && sudo systemctl start ijodidar-celery

4. [ ] Configure Sentry
       Create account at sentry.io → New Project → Python/Flask → copy DSN
       echo "SENTRY_DSN=https://xxx" >> ~/ijodidar/.env
       sudo systemctl restart ijodidar

5. [ ] Start MSG91 DLT registration
       Go to msg91.com → DLT → register (Udyam cert ready)

6. [ ] Invite 5 beta users
       Share ijodidar.com with family/network
       Manually verify their email until SES is live
```
