# API_ARCHITECTURE.md
## iJodidar v2 — REST API Architecture
## June 2026

---

## DESIGN DECISIONS

### Why additive (not replace)
The existing HTML web application is correct and must remain unchanged.
The REST API is an additional layer sharing models, business logic, and Celery tasks.
Web users use sessions. Mobile users use JWT tokens. Both work simultaneously.

### Blueprint structure
```
app/
  api/
    __init__.py       — blueprint registration, CORS, error handlers
    auth.py           — /api/v1/auth/*
    profiles.py       — /api/v1/profiles/*
    interests.py      — /api/v1/interests/*
    conversations.py  — /api/v1/conversations/*
    notifications.py  — /api/v1/notifications/*
    kundli.py         — /api/v1/kundli/*
    devices.py        — /api/v1/devices/*
    plans.py          — /api/v1/plans/*
    schemas.py        — all Marshmallow serializers
    errors.py         — error code constants + helpers
```

### Authentication
- **Web:** Flask-Login session cookie (unchanged)
- **API:** JWT Bearer token via Flask-JWT-Extended 4.6.0
- **Access token expiry:** 1 hour
- **Refresh token expiry:** 30 days
- **Storage:** Client stores in Keychain (iOS) or EncryptedSharedPreferences (Android)
- **Revocation:** Redis DB 4 — blocklist (on logout, password change)
- **SocketIO:** JWT token in `auth` parameter alongside existing session path

### Response contract (all endpoints)
```
Success:  { "success": true,  "data": {...},  "meta": {...optional...} }
Error:    { "success": false, "error": { "code": "ERROR_CODE", "message": "...", "field": "..." } }
List:     { "success": true,  "data": [...],  "meta": { "page": 1, "per_page": 20, "total": 142, "pages": 8 } }
```

---

## COMPLETE API ENDPOINT SPECIFICATION

### Authentication — `/api/v1/auth/`

| Method | Endpoint | Auth | Body | Returns |
|--------|----------|------|------|---------|
| POST | `/auth/send-otp` | None | `{phone, name?}` | `{otp_sent, is_new_user}` |
| POST | `/auth/verify-otp` | None | `{phone, otp}` | `{access_token, refresh_token, user}` |
| POST | `/auth/login` | None | `{email, password}` | `{access_token, refresh_token, user}` |
| POST | `/auth/refresh` | Refresh | — | `{access_token}` |
| POST | `/auth/logout` | Access | `{fcm_token?}` | `{success}` |
| POST | `/auth/forgot-password` | None | `{email}` | `{success}` |
| POST | `/auth/reset-password` | None | `{token, password}` | `{success}` |

### Profiles — `/api/v1/profiles/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| GET | `/profiles/me` | JWT | Full profile object |
| PATCH | `/profiles/me` | JWT | `{completeness, section_score}` |
| GET | `/profiles/me/completeness` | JWT | `{total, sections}` |
| GET | `/profiles/feed` | JWT | Paginated profile cards with scores |
| GET | `/profiles/feed?tab=new` | JWT | New profiles (last 7 days) |
| GET | `/profiles/feed?tab=mutual` | JWT | Mutual shortlist profiles |
| GET | `/profiles/feed?tab=near` | JWT | Same-city profiles |
| GET | `/profiles/@<username>` | JWT | Full profile + interest status |
| GET | `/profiles/viewers` | JWT | Who viewed my profile |
| POST | `/profiles/photos` | JWT | Upload photo (multipart) |
| DELETE | `/profiles/photos/<id>` | JWT | Delete photo |
| PATCH | `/profiles/photos/<id>/primary` | JWT | Set as primary |

### Interests — `/api/v1/interests/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| POST | `/interests` | JWT | `{interest_id, remaining}` |
| GET | `/interests/received` | JWT | Paginated received interests |
| GET | `/interests/sent` | JWT | Paginated sent interests |
| GET | `/interests/accepted` | JWT | Accepted connections |
| PATCH | `/interests/<id>` | JWT | `{action: accept/decline/withdraw, conversation_id?}` |

### Conversations — `/api/v1/conversations/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| GET | `/conversations` | JWT | Inbox with last messages |
| GET | `/conversations/<id>/messages` | JWT | Paginated messages (before cursor) |
| POST | `/conversations/<id>/messages` | JWT | Sent message object |
| PATCH | `/conversations/<id>/read` | JWT | `{success}` |

### Notifications — `/api/v1/notifications/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| GET | `/notifications` | JWT | Paginated notifications |
| GET | `/notifications/unread-count` | JWT | `{count}` |
| PATCH | `/notifications/read` | JWT | `{success}` |

### Devices — `/api/v1/devices/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| POST | `/devices` | JWT | `{success}` |
| DELETE | `/devices/<fcm_token>` | JWT | `{success}` |

### Kundli — `/api/v1/kundli/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| POST | `/kundli` | JWT | Calculated + saved chart |
| GET | `/kundli/me` | JWT | Current user's chart |
| GET | `/kundli/match/<user_id>` | JWT | Guna Milan report |
| GET | `/kundli/cities?q=<query>` | JWT | City autocomplete |

### Plans — `/api/v1/plans/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| GET | `/plans` | JWT | All plans with features |
| POST | `/plans/<id>/order` | JWT | Razorpay order object |
| POST | `/plans/verify-payment` | JWT | `{success, plan_name}` |

### Search — `/api/v1/search/`

| Method | Endpoint | Auth | Returns |
|--------|----------|------|---------|
| GET | `/search?religion=Hindu&min_age=24&city=Pune` | JWT | Paginated search results |

---

## MARSHMALLOW SCHEMAS

### ProfileCardSchema (feed + search)
Fields: id, username, first_name, age, city, religion, caste, occupation, income_range, photo_url, thumb_url, match_score, trust_score, trust_label, trust_tier, is_spotlight, last_active_at, plan_name

### ProfileFullSchema (profile view)
Extends ProfileCardSchema plus: last_name, height, weight, bio, sub_caste, gotra, marital_status, mother_tongue, diet, smoking, drinking, family_type, is_nri, nri_country, nakshatra, rashi, manglik, hobbies_list, photos, educations, professional, completeness_pct

### InterestSchema
Fields: id, sender (ProfileCardSchema), receiver (ProfileCardSchema), status, message, sent_at, updated_at

### ConversationSchema
Fields: id, other_user (ProfileCardSchema), last_message_body, last_message_at, unread_count, created_at

### MessageSchema
Fields: id, body, sender_id, is_mine (computed), sent_at, is_read

### NotificationSchema
Fields: id, type, message, link, is_read, created_at

---

## ERROR CODE REGISTRY

| Code | HTTP | When |
|------|------|------|
| `INVALID_OTP` | 400 | OTP mismatch |
| `OTP_EXPIRED` | 400 | OTP past 10-minute window |
| `ACCOUNT_LOCKED` | 429 | Brute force lockout active |
| `NOT_AUTHENTICATED` | 401 | No valid session or token |
| `TOKEN_EXPIRED` | 401 | JWT access token past 1h |
| `REFRESH_REQUIRED` | 401 | Use refresh token to get new access token |
| `EMAIL_NOT_VERIFIED` | 403 | Email must be verified |
| `PHONE_NOT_VERIFIED` | 403 | Phone must be verified for messaging |
| `PLAN_REQUIRED` | 403 | Feature requires paid plan |
| `INTEREST_LIMIT` | 429 | Monthly interest quota exhausted |
| `ALREADY_EXISTS` | 409 | Interest already sent; conversation already exists |
| `NOT_FOUND` | 404 | Resource not found |
| `FORBIDDEN` | 403 | Not owner of resource |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `PAYMENT_FAILED` | 400 | Razorpay signature invalid |

---

## RATE LIMITS (API-specific)

| Endpoint | Limit | Shared With Web? |
|----------|-------|-----------------|
| `POST /auth/send-otp` | 5 per hour per phone | No |
| `POST /auth/verify-otp` | 10 per 30 min per phone | No |
| `POST /auth/login` | 20 per minute per IP | No |
| `GET /profiles/feed` | 60 per minute per user | No |
| `POST /interests` | 20 per minute per user | No |
| `POST /conversations/<id>/messages` | 30 per minute per user | No |

---

*API_ARCHITECTURE.md | iJodidar v2 | June 2026*
