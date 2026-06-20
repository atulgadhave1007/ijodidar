# iJodidar — Screen-by-Screen Wireframes
## All Key Screens | Mobile + Desktop
## June 2026

---

## NOTATION

```
┌─┐ = card/container boundary
│ │ = content inside
[X] = interactive element (button, link, input)
(X) = icon
●   = radio selected
○   = radio unselected
═   = section divider
▸   = disclosure arrow / chevron
★   = star / rating
```

---

## SCREEN 1 — LANDING PAGE (Mobile)

```
┌───────────────────────────────┐
│ iJodidar              [Login] │  ← sticky nav
└───────────────────────────────┘

┌───────────────────────────────┐
│                               │
│    Find Your                  │
│    Perfect Match              │  ← headline
│    in Maharashtra             │
│                               │
│  ● Live Now: 1,247 profiles   │  ← social proof pill
│                               │
│  I am a    [Man    ▾]         │
│  Looking for [Bride  ▾]       │
│                               │
│  [   Register Free →   ]      │  ← primary CTA
│  [   Sign In            ]     │  ← secondary
│                               │
└───────────────────────────────┘

┌───────────────────────────────┐
│  ✓ Guna Milan matching        │
│  ✓ Marathi community focus    │
│  ✓ Verified profiles          │
│  ✓ Free to start              │
└───────────────────────────────┘

┌───────────────────────────────┐
│  How it works                 │
│  ①──────────────────────      │
│  Create your profile          │
│  ②──────────────────────      │
│  Browse matches               │
│  ③──────────────────────      │
│  Connect and chat             │
└───────────────────────────────┘

┌───────────────────────────────┐
│  Plans from ₹499/month        │
│  [View Plans]                 │
└───────────────────────────────┘

[Privacy] [Terms] [Grievance]
© 2026 iJodidar, Pune
```

---

## SCREEN 2 — REGISTRATION (Mobile, Phone-First)

```
┌───────────────────────────────┐
│ ← Back         Step 1 of 2   │
│ ─────────────────────────     │  ← progress bar 50%
│                               │
│  Create your account          │
│                               │
│  Your name                    │
│  [Atul Gadhave              ] │
│                               │
│  Phone number                 │
│  [+91  9876543210           ] │
│                               │
│  ─────────────────────────    │
│  Password                     │
│  [•••••••••••••             ] │
│                               │
│  [    ] I agree to Terms &    │
│         Privacy Policy        │
│         I am 18 or older      │
│                               │
│  [   Get OTP →   ]            │
│                               │
│  Already registered? [Login]  │
└───────────────────────────────┘
```

---

## SCREEN 3 — OTP VERIFICATION

```
┌───────────────────────────────┐
│ ← Back                        │
│                               │
│  Enter OTP                    │
│  Sent to +91 9876543210       │
│                               │
│  [  ] [  ] [  ] [  ] [  ] [  ]│  ← 6 individual digit boxes
│       Auto-fills from SMS     │
│                               │
│  Resend OTP in 0:47           │
│                               │
│  [   Verify   ]               │
│                               │
└───────────────────────────────┘
```

---

## SCREEN 4 — ONBOARDING STEP: GENDER

```
┌───────────────────────────────┐
│ ✕          Step 1 of 3       │
│ ─────── ●──────────────       │  ← progress bar 33%
│                               │
│  Hi Atul! 👋                  │
│  Tell us about you            │
│                               │
│  I am a                       │
│  ┌──────────┐  ┌──────────┐  │
│  │    👨    │  │    👩    │  │
│  │   Man    │  │  Woman   │  │
│  └──────────┘  └──────────┘  │
│                               │
│  Looking for                  │
│  ┌──────────┐  ┌──────────┐  │
│  │    👰    │  │    🤵    │  │
│  │  Bride   │  │  Groom   │  │
│  └──────────┘  └──────────┘  │
│                               │
│  [   Continue →   ]           │
└───────────────────────────────┘
```

---

## SCREEN 5 — ONBOARDING STEP: DOB + RELIGION

```
┌───────────────────────────────┐
│ ← Back       Step 2 of 3     │
│ ─────────── ●──────────       │  ← progress 66%
│                               │
│  A bit about you              │
│                               │
│  Date of birth                │
│  [June  ▾] [15 ▾] [1995 ▾] │
│  You must be 18 or older      │
│                               │
│  Religion                     │
│  [Hindu              ▾]       │
│                               │
│  Marital status               │
│  [Never Married      ▾]       │
│                               │
│  ─────────────────────────    │
│  [   Continue →   ]           │
│  [   Skip for now             │
└───────────────────────────────┘
```

---

## SCREEN 6 — ONBOARDING: PHOTO UPLOAD

```
┌───────────────────────────────┐
│ ← Back       Step 3 of 3     │
│ ─────────────────── ●─        │  ← progress 100%
│                               │
│  Add your photo               │
│                               │
│  Profiles with photos get     │
│  5× more interest requests    │
│                               │
│  ┌─────────────────────────┐  │
│  │                         │  │
│  │         📷              │  │
│  │   Tap to upload photo   │  │
│  │   JPG/PNG, max 5MB      │  │
│  │                         │  │
│  └─────────────────────────┘  │
│                               │
│  [   Upload Photo   ]         │
│  [   Skip — I'll do later     │
└───────────────────────────────┘
```

---

## SCREEN 7 — HOME FEED (Mobile)

```
┌───────────────────────────────┐
│ iJodidar                 (🔔2)│  ← minimal top bar
├───────────────────────────────┤
│ [Best] [New] [Mutual] [Nearby]│  ← discovery tabs
├───────────────────────────────┤
│                               │
│ ┌──────────┐  ┌──────────┐   │
│ │   📸     │  │   📸     │   │  ← 2-column card grid
│ │  ⚡84%   │  │  ⚡71%   │   │
│ ├──────────┤  ├──────────┤   │
│ │Priya,27  │  │Sneha,29  │   │
│ │Pune·Engg │  │Mumbai·Dr │   │
│ │Hindu·Mrt │  │Hindu·CKP │   │
│ │🟡 Phone  │  │🟠 ID Vrfd│   │
│ ├──────────┤  ├──────────┤   │
│ │[💚][♡]  │  │[💚][♡]  │   │
│ └──────────┘  └──────────┘   │
│                               │
│ ┌──────────┐  ┌──────────┐   │
│ │ UPGRADE  │  │   📸     │   │
│ │ TO VIEW  │  │  ⚡68%   │   │  ← blur overlay on Free
│ │ 🔒Silver+│  │          │   │
│ ├──────────┤  ├──────────┤   │
│ │Kavya,25  │  │Pooja,28  │   │
│ │Nagpur    │  │Pune      │   │
│ └──────────┘  └──────────┘   │
│                               │
├───────────────────────────────┤
│ [🏠] [🔍] [❤️3] [💬5] [👤]  │  ← bottom nav
└───────────────────────────────┘
```

---

## SCREEN 8 — HOME FEED (Desktop)

```
┌─────────────────────────────────────────────────────────────────────┐
│ iJodidar   [Search________________]   ❤️3  💬5  🔔2  [Avatar ▾]   │
├──────────┬──────────────────────────────────────────────────────────┤
│          │ [Best Matches] [New This Week] [Mutual] [Near Me]        │
│ SIDEBAR  ├────────────────────────────────────────────────────────  │
│          │                                                          │
│ [Avatar] │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │
│ Atul G.  │  │  📸    │  │  📸    │  │  📸    │  │  📸    │       │  ← 4 cols
│ 32 · Pun │  │ ⚡92%  │  │ ⚡87%  │  │ ⚡79%  │  │ ⚡71%  │       │
│ Free Plan│  ├────────┤  ├────────┤  ├────────┤  ├────────┤       │
│          │  │Priya,27│  │Sneha,29│  │Meena,26│  │Kavya,25│       │
│ ─────── │  │Pune·Eng│  │Mum·Dr  │  │Ngp·CA  │  │Pun·MBA │       │
│ 🏠 Home  │  │Hindu·Mr│  │Hindu·CK│  │Jain    │  │Hindu   │       │
│ 👤 Prof  │  │🟠 ID ✓ │  │🟡 Ph✓  │  │🟡 Ph✓  │  │        │       │
│ ❤️ Inter  │  ├────────┤  ├────────┤  ├────────┤  ├────────┤       │
│ 🔍 Search│  │[💚][♡] │  │[💚][♡] │  │[💚][♡] │  │[💚][♡] │       │
│ ♡ Saved  │  └────────┘  └────────┘  └────────┘  └────────┘       │
│ 👨‍👩‍👧 Family│                                                          │
│ ─────── │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │
│ ⭐ Upgrade│  │...     │  │...     │  │...     │  │...     │       │
│ Your Plan│  └────────┘  └────────┘  └────────┘  └────────┘       │
│          │                                                          │
└──────────┴──────────────────────────────────────────────────────────┘
```

---

## SCREEN 9 — PROFILE VIEW (Mobile)

```
┌───────────────────────────────┐
│ ← Back              ⋯ (Menu) │
├───────────────────────────────┤
│                               │
│  ┌─────────────────────────┐  │
│  │                         │  │
│  │      [PHOTO]            │  │  ← full-width hero photo
│  │   ◀ 1 of 3 ▶           │  │  ← swipeable
│  │                         │  │
│  │  ⚡84%    🟠 ID Verified │  │  ← floating badges
│  └─────────────────────────┘  │
│                               │
│  Priya Sharma, 27             │
│  📍 Pune · Hindu · Maratha    │
│  💼 Software Engineer, TCS    │
│  🎓 B.Tech COEP 2019          │
│  💰 ₹10-15 LPA                │
│  📏 165 cm · Never Married    │
│  🕉️ Nakshatra: Rohini · No🔴  │  ← Manglik flag
│                               │
│  ═══════════════════════════  │
│  About me                     │
│  "I'm a software engineer     │
│  who loves trekking and..."   │
│  Hobbies: Trekking, Reading   │
│                               │
│  ═══════════════════════════  │
│  Family                       │
│  Nuclear · Middle class       │
│  Father: Retired              │
│  Mother: Homemaker            │
│  1 brother (married)          │
│                               │
│  ═══════════════════════════  │
│  [Check Guna Milan]           │
│                               │
│                               │
├───────────────────────────────┤
│  [💚 Send Interest] [♡ Save] │  ← sticky bottom CTA
└───────────────────────────────┘
```

---

## SCREEN 10 — PROFILE EDITOR (Mobile, About Tab)

```
┌───────────────────────────────┐
│ ← Back         My Profile    │
├───────────────────────────────┤
│        72% Complete ○         │  ← completeness ring inline
│  [About] [Career] [Family]    │
│  [Photos] [Prefs]             │
├───────────────────────────────┤
│                               │
│  Your name                    │
│  [Atul        ] [Gadhave    ] │
│                               │
│  Date of birth                │
│  [15 June 1990              ] │
│                               │
│  I am a                       │
│  [● Man] [○ Woman]           │
│                               │
│  Looking for                  │
│  [● Bride] [○ Groom]         │
│                               │
│  Height                       │
│  ●──────────── 172cm / 5'8"  │  ← slider
│                               │
│  About me  (127/500)          │
│  ┌──────────────────────────┐ │
│  │ I'm a product manager    │ │
│  │ who loves trekking...    │ │
│  └──────────────────────────┘ │
│                               │
│  Hobbies                      │
│  [Trekking ×] [Reading ×]     │
│  [+ Add hobby]                │
│                               │
│  Religion  [Hindu ▾]          │
│  Caste     [Maratha         ] │
│  Gotra     [Kashyap         ] │
│  Manglik   [● No] [○ Yes]    │
│                               │
│  [      Save About      ]     │
│  18 of 25 points complete     │
│                               │
└───────────────────────────────┘
```

---

## SCREEN 11 — INTERESTS (Mobile)

```
┌───────────────────────────────┐
│ ← Back           Interests   │
├───────────────────────────────┤
│ [Received(3)] [Sent] [Mutual] │
│              [Viewers]        │
├───────────────────────────────┤
│                               │
│  ┌───────────────────────┐    │
│  │ [Avatar] Priya S., 27 │    │
│  │ Pune · Eng · Hindu    │    │
│  │ "I'd love to connect" │    │  ← interest message
│  │ 2 hours ago           │    │
│  │                       │    │
│  │ [✓ Accept] [✗ Decline]│    │
│  └───────────────────────┘    │
│                               │
│  ┌───────────────────────┐    │
│  │ [Avatar] Sneha M., 29 │    │
│  │ Mumbai · Doctor       │    │
│  │ 1 day ago             │    │
│  │                       │    │
│  │ [✓ Accept] [✗ Decline]│    │
│  └───────────────────────┘    │
│                               │
│  ┌───────────────────────┐    │
│  │ [Avatar] Ananya K.,25 │    │
│  │ Nagpur · CA           │    │
│  │ 3 days ago            │    │
│  │                       │    │
│  │ [✓ Accept] [✗ Decline]│    │
│  └───────────────────────┘    │
│                               │
├───────────────────────────────┤
│ [🏠] [🔍] [❤️3] [💬5] [👤]  │
└───────────────────────────────┘
```

---

## SCREEN 12 — MESSAGES INBOX (Mobile)

```
┌───────────────────────────────┐
│ ← Back           Messages     │
├───────────────────────────────┤
│  [  Search conversations...] │
├───────────────────────────────┤
│                               │
│  ┌───────────────────────┐    │
│  │ [Avatar] Priya S.  2h │    │
│  │ "That sounds great!" ●│    │  ← ● = unread dot
│  └───────────────────────┘    │
│                               │
│  ┌───────────────────────┐    │
│  │ [Avatar] Meena J.  1d │    │
│  │ "Are you free this we"│    │
│  └───────────────────────┘    │
│                               │
│  ┌───────────────────────┐    │
│  │ [Avatar] Kavya R.  3d │    │
│  │ "I'd love to know..." │    │
│  └───────────────────────┘    │
│                               │
├───────────────────────────────┤
│ [🏠] [🔍] [❤️] [💬3] [👤]   │
└───────────────────────────────┘
```

---

## SCREEN 13 — CONVERSATION (Mobile)

```
┌───────────────────────────────┐
│ ←   [Avatar] Priya S.   📞🎥 │  ← back + name + call buttons
│      🟡 Phone Verified        │
├───────────────────────────────┤
│                               │
│         Monday, 15 Jun        │  ← date separator
│                               │
│               ┌─────────────┐ │
│               │ Hi! I saw   │ │  ← sent (right align)
│               │ your profile│ │
│               │    2:30 PM ✓│ │
│               └─────────────┘ │
│  ┌─────────────┐              │
│  │ Thank you!  │              │  ← received (left align)
│  │ Would love  │              │
│  │ to chat!    │              │
│  │ 2:35 PM     │              │
│  └─────────────┘              │
│                               │
│               ┌─────────────┐ │
│               │ Check our   │ │
│               │ Guna Milan  │ │
│               │ ⚡ 28/36 ✓  │ │  ← inline Guna Milan card
│               └─────────────┘ │
│                               │
├───────────────────────────────┤
│ [📎] [Type a message...] [▶] │  ← input bar
└───────────────────────────────┘
```

---

## SCREEN 14 — MEMBERSHIP PLANS (Mobile)

```
┌───────────────────────────────┐
│ ← Back       Upgrade Plan    │
├───────────────────────────────┤
│  Unlock your full potential   │
│  247 members upgraded this wk │  ← social proof
├───────────────────────────────┤
│                               │
│  ┌───────────────────────┐   │
│  │ FREE           ₹0     │   │
│  │ ─────────────────     │   │
│  │ ✓ 5 interests/month   │   │
│  │ ✗ Messaging           │   │
│  │ ✗ Phone numbers       │   │
│  │ ✗ Full photos         │   │
│  │ [Current Plan]        │   │
│  └───────────────────────┘   │
│                               │
│  ┌───────────────────────┐   │
│  │ ⭐ SILVER  ₹16/day   │   │  ← per-day pricing
│  │            ₹499/month │   │
│  │ ─────────────────     │   │
│  │ ✓ 20 interests/month  │   │
│  │ ✓ Messaging enabled   │   │
│  │ ✓ Clear photos        │   │
│  │ ✗ Phone numbers       │   │
│  │ [Upgrade to Silver →] │   │  ← primary CTA
│  └───────────────────────┘   │
│                               │
│  ┌───────────────────────┐   │
│  │ ★ GOLD    ₹11/day    │   │
│  │            ₹999/3mo   │   │
│  │ ✓ 50 interests/month  │   │
│  │ ✓ Phone numbers       │   │
│  │ ✓ All Silver features │   │
│  │ [Upgrade to Gold]     │   │
│  └───────────────────────┘   │
│                               │
│  🤝 Personal Matchmaking      │
│     from ₹4,999 [Learn More]  │
│                               │
└───────────────────────────────┘
```

---

## SCREEN 15 — KUNDLI / GUNA MILAN

```
┌───────────────────────────────┐
│ ← Back         Kundli        │
├───────────────────────────────┤
│  Auto-calculate from birth    │
│  details — no manual entry    │
├───────────────────────────────┤
│  Date of birth                │
│  [15 June 1990              ] │
│                               │
│  Time of birth                │
│  [09:30 AM                  ] │
│                               │
│  Birth city                   │
│  [Pune                      ] │
│  Coordinates: 18.52°N, 73.85°E│
│                               │
│  [  Preview  ] [Calculate & Save]│
│                               │
│  ┌───────────────────────┐    │
│  │ ✓ Calculated result:  │    │
│  │                       │    │
│  │ Nakshatra: Shatabhisha│    │
│  │ Rashi: Kumbha         │    │
│  │ Charan: 4             │    │
│  │ Gana: Rakshasa        │    │
│  │ Nadi: Adi             │    │
│  │ Manglik: Partial      │    │
│  │                       │    │
│  │ ℹ️ Accuracy: ±0.3°   │    │
│  └───────────────────────┘    │
│                               │
│  ▸ Already have a kundli?     │
│    Enter details manually     │
│                               │
└───────────────────────────────┘
```

---

## SCREEN 16 — GUNA MILAN MATCH REPORT

```
┌───────────────────────────────┐
│ ← Back       Guna Milan       │
│ You × Priya Sharma            │
├───────────────────────────────┤
│                               │
│         28 / 36               │  ← large score
│      ▓▓▓▓▓▓▓▓▓░░░           │  ← progress bar
│       Good Match              │
│                               │
├───────────────────────────────┤
│  Koot Breakdown               │
│                               │
│  Varna     (max 1)   ●●      │  ← 1/1
│  Vashya    (max 2)   ●●     │  ← 2/2
│  Tara      (max 3)   ●●●    │  ← 3/3
│  Yoni      (max 4)   ●●●○   │  ← 3/4
│  Graha Mt. (max 5)   ●●●●○  │  ← 4/5
│  Gana      (max 6)   ●●●●●● │  ← 6/6
│  Bhakoot   (max 7)   ●●●●●○○│  ← 5/7
│  Nadi      (max 8)   ●●●●●●●●│  ← 8/8 (best!)
│                               │
├───────────────────────────────┤
│  Gotra Check                  │
│  ✅ Different gotras          │
│  Kashyap × Bharadwaj — OK     │
│                               │
│  Manglik                      │
│  ✅ Both: No — Compatible     │
│                               │
└───────────────────────────────┘
```

---

## SCREEN 17 — SEARCH (Mobile, filter bottom sheet)

```
Main screen:
┌───────────────────────────────┐
│ ← Back            Search     │
├───────────────────────────────┤
│ [🔍 Religion, city, name...] │
│ [🎛️ Filters (3 active)]      │
├───────────────────────────────┤
│ Hindu ×  24-35 ×  Pune ×    │  ← active filter pills (scroll horiz)
├───────────────────────────────┤
│ 142 profiles found            │
│ Sort: [Newest ▾]              │
├───────────────────────────────┤
│ ┌──────────┐  ┌──────────┐   │
│ │  card    │  │  card    │   │
│ └──────────┘  └──────────┘   │

Filter bottom sheet (slides up from bottom):
┌───────────────────────────────┐
│   ────                        │  ← drag handle
│         Filters               │
│  [Clear All]                  │
├───────────────────────────────┤
│  Age range                    │
│  [18]────────────────[50]     │  ← range slider
│                               │
│  Religion                     │
│  [Any] Hindu  Muslim Sikh ... │  ← pill select
│                               │
│  City                         │
│  [Pune            ]           │
│                               │
│  Height (cm)                  │
│  [150]────────────────[200]   │
│                               │
│  Marital status               │
│  [● Never Married]            │
│  [○ Divorced OK  ]            │
│  [○ Any          ]            │
│                               │
│  Manglik                      │
│  [Any] [Non-M only] [M only]  │
│                               │
│  Income (LPA)                 │
│  [Any] [5+] [10+] [15+] [25+]│
│                               │
│  [Apply Filters — 142 results]│  ← sticky bottom
└───────────────────────────────┘
```

---

*Screen-by-Screen Wireframes | iJodidar | June 2026*
*All dimensions are relative — implement with CSS, not fixed pixels*
