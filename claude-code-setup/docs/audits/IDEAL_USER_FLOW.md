# iJodidar — Ideal User Flow
## Production-Grade Matrimonial Journey
## Based on industry research + gap analysis

---

## DESIGN PRINCIPLES

1. **Phone-first** — Indian users trust phone OTP more than email
2. **Progressive disclosure** — collect minimum to start, deepen later
3. **Value before verification** — show value (blurred profiles) before asking for data
4. **Family context** — decisions are family-made; flows should accommodate this
5. **Trust-gated features** — verification unlocks features progressively

---

## FLOW 1 — REGISTRATION & FIRST LOGIN

### Current: 5-step wizard after email verify
### Ideal: Phone-OTP first, progressive profile build

```
┌─────────────────────────────────────────────┐
│  Landing Page                               │
│  "Find your life partner"                   │
│  CTA: "Register Free" / "Sign In"           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 1: Name + Phone (2 fields only)       │
│  "Hi, I'm ___ , my number is ___"           │
│  → Send OTP immediately                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 2: OTP verification (6 digits)        │
│  Auto-focuses. Pastes from clipboard.       │
│  Resend after 60 seconds.                   │
└──────────────────┬──────────────────────────┘
                   │ ← Account created here. User is in.
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 3: I am a ___ looking for ___         │
│  [Man] [Woman]   [Bride] [Groom]            │
│  Big tap cards. One tap each.               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 4: Basic details (DOB + Religion)     │
│  DOB: native date picker                    │
│  Religion: scrollable pills                 │
│  "Skip for now →" visible but small         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  STEP 5: See 3 blurred matches              │
│  "These are your matches — add a photo      │
│  to unlock them"                            │
│  [Upload Photo] [Skip — I'll do this later] │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  HOME FEED — First experience               │
│  Toast: "Complete your profile for 5×       │
│  more responses" with completeness ring     │
└─────────────────────────────────────────────┘
```

**Key changes from current:**
- Phone OTP replaces email as primary verification
- Account created at OTP success — not after email click
- User sees partial value (blurred matches) before completing profile
- 5 steps → 4 steps (removed career, preferences from onboarding)
- Email collected post-registration for notifications only

---

## FLOW 2 — PROFILE COMPLETION JOURNEY

### The Industry Model: "Completeness Nudge Loop"

```
Day 0: Register → 30% complete (name, phone, gender, DOB, religion)
       Nudge: "Add your photo — profiles with photos get 5× more responses"

Day 1: Push notification/email: "3 people viewed your profile yesterday"
       Nudge: "Complete your bio to stand out"

Day 2: "Add your profession and education"
       → Seeing more profiles in feed unlocks when occupation is added

Day 3: "Add your partner preferences for better matches"
       → Without prefs, feed shows "popular near you"

Day 7: "Upload Kundli details for Guna Milan matching"
       → Triggered only after base profile complete
```

### Profile Sections (Priority Order)

```
Tier 1 — Unlock basic matching (must have):
  ✓ Name + Phone (registration)
  ✓ Gender + Looking For (step 3)
  ✓ DOB + Religion (step 4)
  • Profile photo (nudge Day 0)

Tier 2 — Unlock better matches:
  • Bio (50 words minimum for full weight)
  • City / Location
  • Height
  • Occupation + Income
  • Education

Tier 3 — Unlock premium search visibility:
  • Caste / Sub-caste / Gotra
  • Marital status
  • Diet / Lifestyle
  • Family details (parents, siblings)
  • Partner preferences

Tier 4 — Trust signals:
  • Kundli / Birth details (auto-calc)
  • ID Verification (Aadhaar)
  • LinkedIn link

Completeness % target for first response: 60%
Completeness % target for best response rate: 85%
```

---

## FLOW 3 — DISCOVERY & MATCHING

### Current: Home feed + Search only
### Ideal: 4 discovery surfaces

```
HOME
├── [Best Matches]     ← scored by algorithm + Guna Milan
├── [New This Week]    ← profiles joined/updated in last 7 days
├── [Mutual Interest]  ← both shortlisted each other
└── [Near Me]          ← same city / nearby districts

SEARCH
├── Quick filters (gender, age, religion, city)
├── Advanced filters (15 filters, expandable)
├── [Saved Searches] — persist last 3 searches
└── Results sorted by: Newest · Best Match · Active Recently

WHO VIEWED ME (sidebar / notification)
└── Shows last 10 profile visitors
    Free: blurred avatar, just "Someone in Pune viewed you"
    Silver+: full name + photo

DAILY MATCHES EMAIL (8 AM IST via Celery Beat)
└── 5 curated profiles based on preferences
    Subject: "5 matches for you today, Atul"
```

---

## FLOW 4 — CONNECT JOURNEY

### Current State
```
View profile → Send Interest → Other accepts → Chat unlocks
```

### Ideal State (industry standard)
```
View profile
    │
    ├── [Express Interest]    FREE — sends interest, no message
    │       │
    │       └── Other accepts → Chat unlocks
    │
    ├── [Send Message]        SILVER+ — sends message without prior interest
    │       → Goes to inbox, counted as interest
    │
    └── [Shortlist]           FREE — save for later

Interest Received Flow:
    Notification: "Priya from Pune is interested in you"
    → View profile
    → [Accept] → Chat opens immediately
    → [Decline] → Gentle decline message sent
    → [View Later] → Marks as deferred
```

### Conversation Gates (progressive unlock)
```
Interest accepted → Text chat (Silver+)
                 → Phone number visible (Gold+)  ← revealed in chat itself
                 → Video call (Gold+)
                 → WhatsApp/Phone call           ← after both agree
```

---

## FLOW 5 — VERIFICATION JOURNEY

```
TRUST TIER 1 — 🔵 Registered
  Phone OTP verified
  Features: Browse (blurred), send 5 interests/month

TRUST TIER 2 — 🟡 Basic Verified
  Email verified (for notifications)
  Profile 60%+ complete
  Features: Full messaging, send interests

TRUST TIER 3 — 🟠 Identity Verified
  Aadhaar OTP (via Surepass API, ₹2/verification)
  Features: Phone number visible (if Gold+), highlighted in search
  Badge: "ID Verified" shown on profile card

TRUST TIER 4 — ✅ Fully Verified
  ID verified + background check (AuthBridge)
  Features: Top placement in search, "Verified" banner
  Badge: Gold verified checkmark
```

---

## FLOW 6 — MEMBERSHIP & PAYMENT JOURNEY

### Conversion Triggers (when to show upgrade prompt)
```
User sends 5th interest → "You've used all 5 free interests"
                           [Upgrade to Silver — 20 interests]

User tries to message  → "Upgrade to Silver to start messaging"
                         [Silver ₹499/month — includes unlimited messaging]

User views a profile with phone visible icon → "Phone number visible for Gold+ members"
                                               [Gold ₹333/month — ₹999/3 months]

User gets declined 3 times → Suggest profile completion
                              "Complete your profile for better matches"

User has been on platform 7 days → Email: "You've matched with 12 people"
                                    "Upgrade now for ₹499 to connect with them"
```

### Plans Page User Journey
```
/plans

Free vs Silver vs Gold vs Platinum

For each plan:
  Price per month
  Price per day (₹33/day = Silver Annual)
  What's included (visual icons)
  "247 members upgraded this week" (social proof)
  [Get Silver] → Razorpay modal
  No redirect to another page — modal inline

After payment:
  Success screen: "You're now Silver! Here are your first matches"
  → Redirect to home feed (not /plans)
```

---

## FLOW 7 — ASSISTED PLAN / RM JOURNEY

```
User signals for Assisted:
  1. User submits form: family preferences, preferred cities, budget
  2. Console: RM sees new request → assigned within 4 hours
  3. RM calls user (first call: 30 min family preference interview)
  4. RM creates shortlist (10-15 profiles in first week)
  5. User reviews → accepts/rejects each profile
  6. RM arranges introduction → tracks outcome in console
  7. Monthly progress report sent to user

Console RM workflow:
  /console/assisted → list of active cases
  Each case: client info + contact log + profile recommendation queue
  Mark profile as: shared → interested → meeting arranged → outcome
```

---

## FLOW 8 — POST-MATCH JOURNEY (Matrimony specific)

### Currently Missing from iJodidar

```
Stage 1: Chat (iJodidar platform)
Stage 2: Phone call (number shared via platform)
Stage 3: Video call (WebRTC exists, needs UI)
Stage 4: "I'm interested in meeting" — in-app signal
Stage 5: Family introduction arranged
         → iJodidar can suggest "Arrange a meeting" CTA
         → Future: Book a meeting room / virtual meeting link
Stage 6: Outcome tracking
         → "Are you engaged?" survey (after 3 months of active chat)
         → Success story submission → featured on landing page
```

---

## MOBILE UX PRINCIPLES

### Every screen must work on 375px (iPhone SE width)
### Touch targets minimum 44px
### Bottom navigation (5 tabs): Matches · Search · Interests · Messages · Profile

```
Bottom Nav:
  🏠 Matches     — Home feed + discovery tabs
  🔍 Search      — Full search with filters
  ❤️  Interests  — Sent/received interests
  💬 Messages    — Inbox
  👤 Profile     — Profile + settings
```

### Cards (primary interaction element)

```
Profile Card (home feed):
  ┌──────────────────────────────┐
  │  [PHOTO - 4:3 ratio]        │
  │  [Blur if Free plan]        │
  │  ● Spotlight badge if applicable
  ├──────────────────────────────┤
  │  Priya, 27 · Pune            │
  │  Software Engineer · TCS     │
  │  Hindu · Maratha             │
  │  ⚡ 84% Match                │
  │  🟠 ID Verified              │
  ├──────────────────────────────┤
  │  [✓ Interest]  [♡ Save]     │
  └──────────────────────────────┘
```

---

*Ideal User Flow | iJodidar | June 2026*
*Based on: Shaadi.com · BharatMatrimony · Jeevansathi · Weds.app research*
