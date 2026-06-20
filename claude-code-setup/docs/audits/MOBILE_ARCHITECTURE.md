# MOBILE_ARCHITECTURE.md
## iJodidar v2 — Mobile Architecture
## June 2026

---

## MOBILE STRATEGY

**Phase 1 (Sprint 5):** React Native app (Expo managed workflow)
**Interim:** PWA via TWA (Trusted Web Activity) → Play Store faster path

Both require the REST API (Sprint 2-3) to be complete first.

---

## TECHNOLOGY DECISIONS

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | React Native (Expo) | One codebase for Android + iOS; large ecosystem; Razorpay SDK available |
| Auth | Phone OTP → JWT | Industry standard for Indian mobile; matches web phone-first flow |
| Real-time | SocketIO with JWT auth | Reuses existing SocketIO server; JWT auth path added in Sprint 2 |
| Push | Firebase FCM | Google standard; free tier sufficient for 10K devices |
| Storage | Secure storage | Keychain (iOS), EncryptedSharedPreferences (Android) for JWT tokens |
| State | React Context + useState | No Redux needed at this scale |
| Navigation | React Navigation 6 | Industry standard; drawer + bottom tab |
| HTTP | Axios with interceptors | Auto-refresh JWT tokens on 401 |
| Photos | Expo Image Picker | Handles gallery + camera; uploads as multipart to `/api/v1/profiles/photos` |

---

## APP NAVIGATION STRUCTURE

```
Bottom Tab Navigator
├── Tab 1: Matches
│   ├── Home Feed (Best Matches default)
│   ├── Tab: New This Week
│   ├── Tab: Mutual
│   └── Tab: Near Me
│
├── Tab 2: Search
│   ├── Search Input + Filter Button
│   ├── Filter Bottom Sheet (modal)
│   └── Results List
│
├── Tab 3: Interests ❤️ (badge)
│   ├── Tab: Received
│   ├── Tab: Sent
│   ├── Tab: Accepted
│   └── Tab: Who Viewed Me
│
├── Tab 4: Messages 💬 (badge)
│   ├── Inbox List
│   └── Conversation View
│
└── Tab 5: Profile 👤
    ├── My Profile (view mode)
    ├── Edit Profile (5-section editor)
    ├── Kundli / Guna Milan
    ├── My Plans
    └── Settings

Stack Navigator (full-screen)
├── Auth Flow
│   ├── Landing Screen
│   ├── Phone Input Screen
│   ├── OTP Verification Screen
│   └── Onboarding (Gender → Basics → Photo)
│
└── Profile Detail Screen (other user's profile)
    ├── Photo Carousel
    ├── About / Career / Family sections
    ├── Guna Milan CTA
    └── Interest / Save / More CTAs
```

---

## API INTEGRATION PATTERN

### Axios instance with JWT interceptor

```
baseURL: https://ijodidar.com/api/v1
headers: { Authorization: Bearer <access_token> }

Response interceptor:
  If 401 AND refresh token valid → auto-refresh → retry request
  If 401 AND refresh token expired → navigate to login screen

Request interceptor:
  Attach access token from secure storage on every request
```

### SocketIO JWT connection

```
io.connect("wss://ijodidar.com", {
  auth: { token: access_token },
  transports: ["websocket"]
})
```

---

## PUSH NOTIFICATION INTEGRATION

### Device Registration Flow

```
1. App launches → request FCM permission
2. FCM returns device token
3. App calls POST /api/v1/devices { fcm_token, platform: "android" | "ios" }
4. Server stores in UserDevice table
5. On logout: DELETE /api/v1/devices/<fcm_token>
```

### Server-Side Push Task

```
Celery task: send_fcm_push_notification(user_id, title, body, data)
  → Fetch all UserDevice records for user_id
  → firebase_admin.messaging.send() for each device
  → Remove stale tokens on FirebaseError
```

### Push Events

| Event | Title | Body |
|-------|-------|------|
| Interest received | "New Interest 💚" | "{name} is interested in you" |
| Interest accepted | "Interest Accepted! 🎉" | "{name} accepted your interest" |
| New message | "New Message 💬" | "{name}: {message_preview}" |
| Daily digest | "Your Matches Today 💕" | "5 new matches for you" |
| Subscription expiring | "Your plan expires soon" | "Renew Gold to keep all features" |

---

## PWA → PLAY STORE (TWA — Faster Path)

If React Native timeline is delayed, ship via TWA in 1 week:

```
Requirements:
  ✅ HTTPS (already)
  ✅ manifest.json (already)
  ✅ Service worker (already)
  ⚠️ PWA icons 192px + 512px maskable (verify/create)
  ⚠️ /.well-known/assetlinks.json (create with release keystore SHA-256)

Tools:
  npm install -g @bubblewrap/cli
  bubblewrap init --manifest=https://ijodidar.com/static/manifest.json
  bubblewrap build
  → Signed APK → Play Store submission

Cost: ₹2,500 one-time (Play Store account)
Timeline: 3-5 days for review
```

---

## MOBILE READINESS CHECKLIST (Sprint-by-Sprint)

| Item | Sprint | Status |
|------|--------|--------|
| REST API Phase 1 (13 endpoints) | 2 | NOT DONE |
| JWT authentication | 2 | NOT DONE |
| SocketIO JWT auth | 2 | NOT DONE |
| FCM UserDevice model | 3 | NOT DONE |
| FCM Celery task | 3 | NOT DONE |
| PWA icons confirmed | Pre-sprint | VERIFY |
| assetlinks.json | Sprint 3 | NOT DONE |
| React Native project setup | 5 | NOT DONE |
| Auth screens | 5 | NOT DONE |
| Feed + Profile screens | 5 | NOT DONE |
| Interests + Messages screens | 5 | NOT DONE |
| Profile editor screens | 5 | NOT DONE |
| Push notification integration | 5 | NOT DONE |
| Play Store submission | 5 | NOT DONE |

---

*MOBILE_ARCHITECTURE.md | iJodidar v2 | June 2026*
