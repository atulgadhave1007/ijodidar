# SECURITY_ARCHITECTURE.md
## iJodidar v2 — Security Architecture
## June 2026

---

## SECURITY POSTURE: 72 / 100 (Good Foundation, JWT Gap)

| Layer | Score | Status |
|-------|-------|--------|
| Authentication (web) | 88/100 | bcrypt, lockout, session invalidation, TOTP |
| Authorization | 82/100 | CSRF, IDOR checks, RBAC console |
| Data Security | 85/100 | S3 private, signed URLs, no PII in Sentry |
| Payment Security | 90/100 | HMAC verification, server-side order fetch |
| API Security | 10/100 | No JWT; no REST API exists yet |
| Mobile Security | 5/100 | No mobile app; no token management |
| Infrastructure | 75/100 | SSL, ProxyFix, IP restriction, rate limiting |
| DPDP Compliance | 88/100 | Export, deletion, consent, grievance officer |

---

## VERIFIED SECURITY CONTROLS (Phase A evidence)

### Authentication Controls
- **Password hashing:** werkzeug `generate_password_hash` (bcrypt, strength=12)
- **Session invalidation:** `User.session_version` incremented on `set_password()`; checked in `before_request`
- **Account lockout:** `failed_login_count` + `locked_until` — 10 failures = 30-minute lock (users), 5 failures = 60-minute lock (console)
- **Token expiry:** Email verify 24h, password reset 1h, phone OTP 10m — all enforced
- **OTP storage:** bcrypt hash in `User.phone_otp` (VARCHAR(255)); never plaintext
- **TOTP 2FA:** Console-only; Google Authenticator via pyotp; 30s drift window
- **Console IP restriction:** `CONSOLE_ALLOWED_IPS` env var; returns 404 (not 403) to avoid revealing console existence

### Request Security
- **CSRF:** Flask-WTF CSRFProtect on all forms; disabled in development only
- **Rate limiting:** Flask-Limiter with Redis storage; all critical endpoints have limits
- **Input validation:** WTForms validators on all forms; phone regex; email-validator library
- **IDOR prevention:** Image delete checks `image.user_id == current_user.id`; conversation access checks user membership; interest respond checks `receiver_id == current_user.id`

### Data Security
- **S3 ACL:** Photos uploaded with `ACL: 'private'`
- **Pre-signed URLs:** 1-hour expiry for own profile; 24-hour for chat
- **No PII in Sentry:** `send_default_pii=False` confirmed in `app/__init__.py`
- **Payment verification:** Razorpay HMAC signature verified before any plan activation; order fetched server-side to prevent amount tampering
- **SECRET_KEY validation:** Application refuses to start in production with default or short key

---

## SECURITY GAPS (from Phase A + B)

### Critical

| Gap | Evidence | Sprint | Fix |
|-----|----------|--------|-----|
| No JWT implementation | Flask-JWT-Extended absent | 2 | Install + implement |
| No token revocation | No Redis blocklist | 2 | Redis DB 4 JWT blocklist |
| Sync email in SocketIO blocks event loop | `send_email()` in `on_send_message()` | Pre-sprint | Replace with task |
| Rate limiter falls back to in-memory | `'memory://'` default in config | 1 | Verify Redis configured |

### Medium

| Gap | Evidence | Sprint | Fix |
|-----|----------|--------|-----|
| No password strength enforcement | 8-char minimum only | 3 | Add zxcvbn or basic strength rules |
| `db.session.commit()` in model property | `interests_remaining()` | 1 | Remove to service layer |
| Bootstrap CDN dependency | `base.html` loads from jsdelivr | 4 | Serve locally |
| No rate limit on refresh token endpoint | Not confirmed | 2 | Add `@limiter.limit` |

### Low

| Gap | Evidence | Sprint | Fix |
|-----|----------|--------|-----|
| Family member data without consent flag | No `consent_given` on FamilyDetails | 2 | Add Boolean column |
| OTP resend: no exponential backoff | Only fixed rate limit | 3 | Add backoff after 3 resends |

---

## v2 SECURITY ADDITIONS

### JWT Token Architecture

```
Access Token:
  Expiry: 1 hour
  Claims: sub (user_id), plan, phone_verified, email_verified
  Storage: client secure storage (never localStorage)

Refresh Token:
  Expiry: 30 days
  Storage: client secure storage
  Revocation: Redis DB 4 (blocklist on logout/password change)

Revocation events:
  - User logout → add refresh token to Redis blocklist
  - Password change → invalidate session_version AND add all tokens to blocklist
  - Admin suspend → immediate Redis blocklist entry
```

### API Security Controls

```
All /api/v1/ endpoints:
  - JWT Bearer token required (except auth/send-otp, auth/verify-otp, auth/login)
  - Flask-CORS with explicit origin whitelist
  - Rate limiting per user_id (not per IP) for authenticated endpoints
  - Request body size limit: 5MB (existing MAX_CONTENT_LENGTH)

SocketIO JWT:
  - auth parameter: { token: access_token }
  - Verified on connect; user joined to personal room
  - Existing session path unchanged for web
```

---

## DPDP COMPLIANCE CONTROLS

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| Consent at registration | `User.consented_at` DateTime | ✅ |
| Age 18+ enforcement | WTForms validator + server check | ✅ |
| Right to portability (data export) | `/account/export` JSON, 3/day | ✅ |
| Right to erasure (deletion) | `/account/delete` — PII anonymised, S3 deleted | ✅ |
| Grievance officer | Footer on all pages → grievance@ijodidar.com | ✅ |
| Privacy Policy | `/privacy-policy` | ✅ |
| Terms of Service | `/terms` | ✅ |
| Third-party data consent (family) | Missing `FamilyDetails.consent_given` | ⚠️ Sprint 2 |
| Data retention policy | Not defined in code | ⚠️ Document required |

---

*SECURITY_ARCHITECTURE.md | iJodidar v2 | June 2026*
