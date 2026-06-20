# iJodidar — Profile Management Redesign
## From 22 Pages → 1 Smart Profile Editor
## June 2026

---

## THE CORE PROBLEM

The current profile editing system has 22 separate routes, each a full HTML page:
`/profile/name` `/profile/birthday` `/profile/gender` `/profile/looking_for`
`/profile/height` `/profile/bio` `/profile/religion` `/profile/lifestyle`
`/profile/email` `/profile/phone` `/profile/address/current` `/profile/professional`
`/profile/education` `/profile/language` `/profile/nri` `/profile/hobbies`
`/profile/partner_preferences` `/profile/privacy` `/profile/referral`
plus 3 photo management routes.

**Each edit is a full page load → form fill → submit → redirect → full page load.**
On a mobile device over 4G, completing a profile means 40+ full HTTP round-trips.

**The industry abandoned this pattern in 2016.**
BharatMatrimony, Shaadi.com, Jeevansathi — all use inline editing on a single profile page.

---

## THE REDESIGNED ARCHITECTURE

### One URL: `/profile`
### Five sections: About · Career · Family · Photos · Preferences
### AJAX saves: No page reload for any edit
### One completeness ring: Updates in real-time as fields fill

### URL pattern
```
GET  /profile              → loads profile editor, defaults to About tab
GET  /profile?section=career   → career section active
GET  /profile?section=family   → family section
GET  /profile?section=photos   → photos section
GET  /profile?section=prefs    → partner preferences section
```

### AJAX save endpoints (new)
```
POST  /api/profile/about       → save basic + lifestyle fields
POST  /api/profile/career      → save occupation + education
POST  /api/profile/family      → save family details
POST  /api/profile/photos      → upload/reorder/delete photos
POST  /api/profile/preferences → save partner preferences
```

---

## SECTION 1: ABOUT (replaces 8 routes)

### Fields in this section
```
Identity:
  First name, Last name
  Date of birth (native date picker)
  Gender [Man / Woman] — large tap targets
  Looking for [Bride / Groom] — large tap targets
  Height (slider: 140-210cm, with ft/in display)
  Marital status (dropdown)

Location:
  Current city (searchable dropdown)
  Native place / hometown

Bio:
  About me (textarea, 50-500 chars, character counter)
  Hobbies (tag picker — multi-select chips)

Community:
  Religion (dropdown)
  Caste (text, or dropdown if religion=Hindu)
  Marathi sub-caste (conditional — if religion=Hindu + marathi-related)
  Mother tongue (dropdown)
  Gotra (text, with same-gotra warning)
  Manglik status (radio: Yes / No / Partial / Unknown)
```

### UX pattern: Inline editing with section save button

```
┌─────────────────────────────────────────────────┐
│  ABOUT SECTION                                  │
│  ─────────────────────────────────────────────  │
│                                                 │
│  Your name                                      │
│  [Atul          ] [Gadhave         ]           │
│                                                 │
│  Date of birth                                  │
│  [────────────────────────────────]            │
│  (native date input — opens OS picker)          │
│                                                 │
│  I am a                                         │
│  [● Man]  [ Woman]                             │
│                                                 │
│  Looking for                                    │
│  [ Bride]  [● Groom]                          │
│                                                 │
│  About me                                       │
│  [─────────────────────────────────────────]   │
│  [                                         ]   │
│  [                                         ]   │
│  127 / 500 characters                          │
│                                                 │
│  Height                                         │
│  ●────────────────────── 172 cm / 5'8"         │
│                                                 │
│  Hobbies                                        │
│  [Trekking ×] [Reading ×] [+ Add]             │
│                                                 │
│  Religion  [Hindu ▾]    Caste  [Maratha___]   │
│                                                 │
│  Mother tongue  [Marathi ▾]   Gotra  [___]    │
│                                                 │
│  Manglik                                        │
│  [ No]  [ Partial]  [ Yes]  [● Unknown]       │
│                                                 │
│  ─────────────────────────────────────────────  │
│  [Save About]                      14 / 25 pts  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## SECTION 2: CAREER (replaces 2 routes)

```
Education:
  Degree (B.Tech / MBBS / CA / MBA / Other...)
  Specialization (text)
  Institution (text)
  Graduation year (number)

Professional:
  Employment type (Private / Govt / Self-employed / Business / Not working)
  Occupation / Job title (text)
  Company / Organisation (text)
  Annual income (income_lpa slider/dropdown: < ₹3L, ₹3-5L, ₹5-10L, ₹10-15L, ₹15-25L, ₹25-50L, ₹50L+)
```

---

## SECTION 3: FAMILY (replaces family/ routes)

```
About family:
  Family type (Joint / Nuclear / Extended)
  Family status (Middle class / Upper middle class / Rich)
  Father status (Alive – employed as _______ / Retired / Passed away)
  Mother status (same)
  Brothers (number) / Sisters (number)
  
About family text:
  [Tell families about your background — 200 chars]

NRI status:
  [ ] Working / living outside India
  Country: [___________]
```

---

## SECTION 4: PHOTOS

### Redesigned photo management

**Current problems:**
- Upload is at `/upload_image` (separate route)
- Primary photo set via `/set_primary_image/<id>`
- Delete via `/delete_image/<id>`
- No reordering

**Redesigned photo section:**
```
┌─────────────────────────────────────────────────┐
│  PHOTOS  (1-5 photos allowed)                   │
│                                                 │
│  ┌─────┐  ┌─────┐  ┌─────┐                    │
│  │ 📸  │  │ 📸  │  │ + ✚ │                    │
│  │ ★   │  │     │  │ Add │                    │
│  │Pri. │  │     │  │Photo│                    │
│  └─────┘  └─────┘  └─────┘                    │
│   Hold & drag to reorder                       │
│   Tap star to set as primary                   │
│   Tap × to delete                              │
│                                                 │
│  ℹ️ Photos with your face get 5× more responses │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Upload UX:**
- Tap "+ Add Photo" → opens system file picker
- Client-side preview before upload
- Shows upload progress ring
- Auto-rejects blurry/low-res (< 200×200px)
- Strips EXIF metadata on server before S3 upload

---

## SECTION 5: PREFERENCES (Partner Preferences)

```
Age range:
  Min age: [18] ←————————————→ Max age: [35]
  (dual-handle range slider)

Height range:
  Min height: [150cm] ←——→ Max height: [185cm]

Community (multi-select):
  Religion: [Any ▾] or multi-select checkboxes
  Caste: [Any / Specific: ___]

Location preference:
  [Maharashtra] [Tamil Nadu] [+ Add state]
  [Pune] [Mumbai] [+ Add city]

Income preference:
  [Any / ₹5 LPA+ / ₹10 LPA+ / ₹15 LPA+]

Lifestyle:
  Diet: [Veg only / Non-veg OK / Any]
  Marital status: [Never married / Divorced OK / Any]
  Manglik: [No preference / Manglik only / Non-Manglik only]

About partner (free text):
  "Tell us in your own words what you're looking for"
  [___________________________________]
```

---

## COMPLETENESS RING — IMPLEMENTATION

### Data model for completeness scoring

```python
SECTION_WEIGHTS = {
    'about': {
        'points': 25,
        'fields': {
            'first_name':    2,  'last_name':      2,
            'dob':           4,  'gender':         2,
            'looking_for':   1,  'height':         2,
            'bio':           5,  'hobbies':        2,
            'religion':      3,  'mother_tongue':  2,
        }
    },
    'career': {
        'points': 20,
        'fields': {
            'degree':        5,  'institution':    3,
            'occupation':    7,  'income_lpa':     5,
        }
    },
    'family': {
        'points': 15,
        'fields': {
            'family_type':   5,  'about_family':   5,
            'father_status': 3,  'mother_status':  2,
        }
    },
    'photos': {
        'points': 20,
        'fields': {
            'primary_photo': 12, 'second_photo':   5, 'third_photo': 3,
        }
    },
    'preferences': {
        'points': 10,
        'fields': {
            'pref_min_age':  3,  'pref_religion':  3, 'pref_location': 4,
        }
    },
}
# TOTAL: 90 base points + 10 from verification = 100
```

### AJAX completeness update

```javascript
// After every field save, fetch updated completeness
async function refreshCompleteness() {
  const { total, sections } = await fetch('/api/profile/completeness').then(r => r.json());
  
  // Update ring
  const circle = document.querySelector('.completeness-circle');
  const circumference = 2 * Math.PI * 15;
  circle.style.strokeDasharray = `${(total / 100) * circumference} ${circumference}`;
  document.querySelector('.completeness-pct').textContent = total + '%';
  
  // Update section indicators
  sections.forEach(({ name, pct }) => {
    const el = document.querySelector(`[data-section="${name}"] .section-pct`);
    if (el) el.textContent = pct + '%';
  });
}
```

---

## MY PROFILE (PUBLIC VIEW) — REDESIGN

### URL: `/@username` (cleaner than current `/<username>`)
### The profile someone else sees when they click your card

```
┌─────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────┐  │
│  │     PHOTO GALLERY (swipeable)              │  │
│  │  [◀] [photo 1 of 3] [▶]                   │  │
│  │                                            │  │
│  │  ❤️ 84%  🟡 Phone Verified  ⭐ Spotlight   │  │
│  └────────────────────────────────────────────┘  │
│                                                 │
│  Priya Sharma, 27 · Pune                       │
│  Software Engineer at Infosys                   │
│  Hindu · Maratha · 165 cm · Never Married      │
│                                                 │
│  [💚 Send Interest]  [♡ Shortlist]  [⋯ More]  │
│                                                 │
├─────────────────────────────────────────────────┤
│  ABOUT                                          │
│  "I'm a software engineer who loves trekking   │
│  and reading. Looking for a like-minded..."    │
│                                                 │
├─────────────────────────────────────────────────┤
│  CAREER                                         │
│  💼 Software Engineer · Infosys                │
│  🎓 B.Tech Computer Science · COEP 2019        │
│  💰 ₹10-15 LPA                                │
│                                                 │
├─────────────────────────────────────────────────┤
│  FAMILY                                         │
│  Nuclear family · Middle class                  │
│  Father: Retired · Mother: Homemaker           │
│  1 brother (married)                            │
│                                                 │
├─────────────────────────────────────────────────┤
│  KUNDLI                                         │
│  Nakshatra: Rohini · Rashi: Vrishabha          │
│  Gana: Manushya · Nadi: Antya                  │
│  Manglik: No                                    │
│  [Check Guna Milan]                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## MIGRATION PLAN — FROM 22 ROUTES TO 1

### Phase A: Add consolidated editor (3 days)
Create new `/profile` page with tabs and AJAX save endpoints.
Keep all 22 old routes working (backward compat).

### Phase B: Wire AJAX endpoints (3 days)
```
POST /api/profile/about       → replaces /profile/name + /birthday + /bio + /height + /religion + /lifestyle
POST /api/profile/career      → replaces /profile/professional + /education
POST /api/profile/family      → replaces /family/edit
POST /api/profile/photos      → replaces /upload_image + /delete_image + /set_primary_image
POST /api/profile/preferences → replaces /profile/partner_preferences
```

### Phase C: Redirect old routes (1 day)
All old routes redirect to `/profile?section=X`.
Existing bookmarks work. Deep links work.

### Phase D: Remove old templates (Month 2)
After 30 days of stable operation, delete old templates and routes.

---

*Profile Management Redesign | iJodidar | June 2026*
