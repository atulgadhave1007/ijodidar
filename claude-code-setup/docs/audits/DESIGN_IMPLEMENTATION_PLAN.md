# iJodidar — Design Implementation Plan
## Phased Delivery: What to Build, In What Order
## June 2026

---

## GUIDING PRINCIPLE

Do not redesign everything at once.
Apply changes in priority order: fix what breaks the experience first,
enhance what differentiates second, build new capabilities third.

Each phase is independently deployable. No phase requires the next to be complete.

---

## PHASE 1 — CRITICAL FIXES (Week 1-2)
### These break the current experience. Fix before anything else.

### 1.1 Fix startup errors (Day 1)

```python
# Fix 1: Add manglik_compatible to app/utils_kundli.py
def manglik_compatible(profile_a, profile_b):
    if not profile_a or not profile_b:
        return True, "Manglik status not available."
    ma = (getattr(profile_a, 'manglik', '') or '').lower()
    mb = (getattr(profile_b, 'manglik', '') or '').lower()
    if not ma or not mb or ma == 'unknown' or mb == 'unknown':
        return True, "Manglik status not confirmed."
    if 'yes' in ma and 'yes' in mb:
        return True, "Both Manglik — compatible."
    if ('yes' in ma and mb == 'no') or (ma == 'no' and 'yes' in mb):
        return False, "⚠️ One Manglik, one not. Recommend consulting an astrologer."
    if 'partial' in ma or 'partial' in mb:
        return True, "Partial Manglik — mild concern. Consult an astrologer."
    return True, "No Manglik concerns detected."

def check_gotra_compatibility(gotra_a, gotra_b, religion_a='', religion_b=''):
    if not gotra_a or not gotra_b:
        return True, "Gotra not specified for one or both profiles."
    if gotra_a.strip().lower() == gotra_b.strip().lower():
        return False, f"⚠️ Same Gotra ({gotra_a}). Not recommended in Hindu tradition."
    return True, f"✅ Different gotras ({gotra_a} × {gotra_b}) — compatible."

# Fix 2: wsgi.py conditional gevent
import os as _os
if _os.environ.get('FLASK_ENV') == 'production':
    try:
        from gevent import monkey; monkey.patch_all()
    except ImportError:
        pass

# Fix 3: pip install Flask-Migrate==4.1.0
```

### 1.2 Add income filter to search (Day 1, 1 hour)
```python
# app/search/routes.py — inside search_profiles()
income_range = args.get('income_range', '').strip()
if income_range:
    if income_range.endswith('+'):
        min_lpa = int(income_range.replace('+', ''))
        query = query.outerjoin(ProfessionalDetails).filter(
            ProfessionalDetails.income_lpa >= min_lpa)
    elif '-' in income_range:
        parts = income_range.split('-')
        query = query.outerjoin(ProfessionalDetails).filter(
            ProfessionalDetails.income_lpa >= int(parts[0]),
            ProfessionalDetails.income_lpa <= int(parts[1]))
```

### 1.3 Add `last_active_at` (Day 1, 30 min + migration)
```python
# models.py — User
last_active_at = db.Column(db.DateTime, nullable=True, index=True)

# app/__init__.py — before_request
@app.before_request
def update_last_active():
    from flask_login import current_user
    from datetime import datetime, timedelta
    if (current_user.is_authenticated and
            (not current_user.last_active_at or
             (datetime.utcnow() - current_user.last_active_at).seconds > 3600)):
        current_user.last_active_at = datetime.utcnow()
        db.session.commit()
```

### 1.4 Fix profile card consistency (Day 2, 2 hours)
Profile view template (`my_profile.html`) uses Bootstrap `card` classes.
Change to `ij-card`, `ij-card-header`, `ij-card-body` to match design system.

---

## PHASE 2 — HIGH-IMPACT UX FIXES (Week 2-3)
### These improve conversion and retention without major architecture changes.

### 2.1 Completeness ring in navbar (Day 1, 2 hours)

```html
<!-- base.html — in navbar, after brand link, for authenticated users -->
<a href="{{ url_for('profile.profile') }}" 
   class="completeness-ring-wrap" title="{{ completeness_pct }}% profile complete">
  <svg width="36" height="36" viewBox="0 0 36 36">
    {% set circ = 3.14159 * 2 * 15 %}
    {% set filled = (completeness_pct / 100) * circ %}
    <circle cx="18" cy="18" r="15" fill="none" stroke="var(--border)" stroke-width="3"/>
    <circle cx="18" cy="18" r="15" fill="none" stroke="var(--brand)" stroke-width="3"
            stroke-dasharray="{{ filled }} {{ circ }}"
            stroke-dashoffset="{{ circ * 0.25 }}"
            transform="rotate(-90 18 18)"/>
  </svg>
  <div class="completeness-pct">{{ completeness_pct }}</div>
</a>
```

### 2.2 Discovery tabs on home feed (Day 1-2, 4 hours)

```python
# main/routes.py — add tab parameter
tab = request.args.get('tab', 'best')

if tab == 'new':
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)
    q = q.filter(User.created_at >= cutoff)
elif tab == 'mutual':
    my_sl = {s.shortlisted_id for s in current_user.shortlists}
    sl_me = {s.user_id for s in Shortlist.query.filter_by(
        shortlisted_id=current_user.id).all()}
    mutual_ids = my_sl & sl_me
    if mutual_ids:
        q = q.filter(User.id.in_(mutual_ids))
    else:
        candidates = []
```

```html
<!-- home.html — add tabs above card grid -->
<div class="ij-tabs">
  {% for tab_id, label in [('best','Best Matches'),('new','New'),
                             ('mutual','Mutual'),('near','Near Me')] %}
  <a href="?tab={{ tab_id }}" 
     class="ij-tab {{ 'active' if tab == tab_id else '' }}">
    {{ label }}
    {% if tab_id == 'mutual' and mutual_count %}<span class="tab-count">{{ mutual_count }}</span>{% endif %}
  </a>
  {% endfor %}
</div>
```

### 2.3 Trust badge on profile cards (Day 2, 2 hours)

```python
# models.py — User
@property
def trust_score(self):
    score = 0
    if self.phone_verified:                       score += 1
    if self.is_verified:                          score += 1
    if self.profile and self.profile.id_verified: score += 2
    return score

@property
def trust_label(self):
    s = self.trust_score
    if s >= 3: return 'ID Verified'
    if s >= 2: return 'Phone Verified'
    if s >= 1: return 'Registered'
    return None

@property
def trust_tier(self):
    s = self.trust_score
    if s >= 3: return 'id'
    if s >= 2: return 'phone'
    if s >= 1: return 'registered'
    return 'none'
```

```html
<!-- In profile card template -->
{% if u.trust_label %}
<span class="trust-badge {{ u.trust_tier }}">
  <i class="bi bi-shield-check-fill"></i>
  {{ u.trust_label }}
</span>
{% endif %}
```

### 2.4 Per-day pricing on plans page (Day 2, 1 hour)

```html
<!-- membership/plans.html — under plan price -->
{% if plan.price_inr > 0 and plan.duration_days > 0 %}
<div style="font-size:12px;color:var(--text-3);margin-top:2px;">
  ₹{{ (plan.price_inr / plan.duration_days) | round | int }}/day
</div>
{% endif %}
```

### 2.5 Mobile filter bottom sheet for search (Day 3-4, 6 hours)

Add `<button class="filter-trigger">Filters</button>` to mobile search.
On tap: slide up bottom sheet with all filter fields.
Apply button refreshes results.

### 2.6 "Who Viewed Me" in Interests tabs (Day 3, 3 hours)

Add `/interests?tab=viewers` showing last 30 profile viewers.
Free users: blurred avatar + "Someone in Pune" (mystery drives upgrade).
Silver+: full name + photo.

---

## PHASE 3 — PROFILE EDITOR REDESIGN (Week 4-6)
### Consolidate 22 pages into 1 AJAX-driven profile editor.

### 3.1 Create AJAX save endpoints (Week 4)

```python
# app/api/profile.py — new file
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db

profile_api_bp = Blueprint('profile_api', __name__, url_prefix='/api/profile')

@profile_api_bp.route('/about', methods=['POST'])
@login_required
def save_about():
    data = request.get_json()
    p = current_user.profile
    if not p:
        from app.models import Profile
        p = Profile(user_id=current_user.id)
        db.session.add(p)
    
    # Map fields
    field_map = {
        'bio': ('profile', 'bio'),
        'height': ('profile', 'height'),
        'religion': ('profile', 'religion'),
        'caste': ('profile', 'caste'),
        'gotra': ('profile', 'gotra'),
        'manglik': ('profile', 'manglik'),
        'mother_tongue': ('profile', 'mother_tongue'),
        'marital_status': ('profile', 'marital_status'),
        'diet': ('profile', 'diet'),
    }
    for key, (model, attr) in field_map.items():
        if key in data:
            setattr(p, attr, data[key])
    
    if 'first_name' in data: current_user.first_name = data['first_name'].strip()
    if 'last_name' in data:  current_user.last_name  = data['last_name'].strip()
    if 'dob' in data:
        from datetime import datetime
        try:
            p.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
            p.date_of_birth = data['dob']
        except ValueError:
            pass
    
    db.session.commit()
    
    from app.utils import calculate_profile_completeness
    completeness = calculate_profile_completeness(current_user)
    return jsonify({'success': True, 'completeness': completeness})
```

### 3.2 New profile editor template (Week 4-5)

Single `/profile` page with:
- Completeness ring (large, 80px, in sidebar on desktop / sticky header on mobile)
- 5 tab sections (About, Career, Family, Photos, Preferences)
- Each section: inline form fields, single "Save Section" button per section
- JavaScript: submit via `fetch()`, show spinner, update completeness ring
- No page reload on any action

### 3.3 Photo section with drag-to-reorder (Week 5)

Use the HTML5 Drag API or a lightweight library (SortableJS — 5KB).
Reordering sends `PATCH /api/profile/photos/order` with new order array.

---

## PHASE 4 — REST API (Month 2)
### Required for mobile app. See API_FIRST_ARCHITECTURE.md.

Priority order:
1. `POST /api/v1/auth/send-otp` + `POST /api/v1/auth/verify-otp` → JWT tokens
2. `GET /api/v1/profiles/feed` → JSON home feed
3. `GET /api/v1/profiles/@username` → JSON profile view
4. `POST /api/v1/interests` + `PATCH /api/v1/interests/<id>`
5. `GET/POST /api/v1/conversations` + messages
6. `POST /api/v1/devices` → FCM token registration
7. All remaining endpoints

### Estimated effort: 2-3 weeks for a developer who knows the Flask codebase.

---

## PHASE 5 — MOBILE APP (Month 3-5)
### After REST API is stable.

Option A: **PWA → TWA → Play Store** (fastest, 2-3 weeks)
- Current PWA + `/.well-known/assetlinks.json`
- Generate signed APK via Bubblewrap CLI
- Submit to Play Store
- No new code beyond REST API

Option B: **React Native** (full native, 8-10 weeks)
- New repository: `ijodidar-mobile`
- Auth → Matches → Profile → Interests → Messages
- Uses all `/api/v1/` endpoints

**Recommendation: Ship TWA first (week 1 of Month 3), build React Native in parallel.**

---

## WHAT NOT TO BUILD (Scope Control)

These are tempting but should NOT be built before Phase 3:

| Don't Build | Build Instead |
|-------------|--------------|
| Swipe cards (Tinder-style) | Fix existing grid first |
| Video matrimony events | Make chat reliable first |
| Horoscope analysis deep-dive | Guna Milan is sufficient |
| AI chatbot | Fix profile editor first |
| Dating-style discovery | Matrimony is intent-based |

---

## IMPLEMENTATION ORDER SUMMARY

```
Week 1:
  ✓ Fix 3 startup errors
  ✓ Add income filter to search
  ✓ Add last_active_at column + migration
  ✓ Fix profile card consistency (Bootstrap → design system)

Week 2:
  ✓ Completeness ring in navbar
  ✓ Discovery tabs (Best/New/Mutual/Near)
  ✓ Trust badge on profile cards
  ✓ Per-day pricing on plans page

Week 3:
  ✓ Mobile search filter bottom sheet
  ✓ Who Viewed Me tab in Interests
  ✓ Daily match email (Celery Beat)
  ✓ Invite 5 beta users → observe real usage

Week 4-6:
  ✓ Profile editor consolidation (22 pages → 1 page, 5 AJAX sections)
  ✓ Photo section with reorder

Month 2:
  ✓ REST API (auth + feed + interests + messaging)
  ✓ FCM push notification device registration

Month 3:
  ✓ TWA → Play Store
  ✓ Begin React Native app

Month 4-5:
  ✓ React Native app (Android + iOS)
```

---

## SUCCESS METRICS

| Metric | Current (estimated) | Target (3 months) |
|--------|--------------------|--------------------|
| Profile completion rate | ~20% | 65% |
| Registration → first interest sent | ~30% | 60% |
| Free → paid conversion | ~2% | 7% |
| 7-day retention | ~25% | 50% |
| Time to first message | ~3 days | <8 hours |
| Kundli adoption rate | ~10% | 40% |
| Mobile traffic conversion | ~30% | 65% |

---

*Design Implementation Plan | iJodidar | June 2026*
*Review progress against success metrics monthly*
