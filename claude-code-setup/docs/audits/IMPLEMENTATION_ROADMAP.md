# iJodidar — Implementation Roadmap
## 12-Month Execution Plan | June 2026

---

## OVERVIEW

| Quarter | Focus | Goal |
|---------|-------|------|
| Q3 2026 (Jul-Sep) | Stabilise + Launch | 500 registered users, ₹25K MRR |
| Q4 2026 (Oct-Dec) | Growth + Engagement | 2,000 users, ₹75K MRR |
| Q1 2027 (Jan-Mar) | Mobile + Scale | 5,000 users, ₹2L MRR |
| Q2 2027 (Apr-Jun) | Expansion | 15,000 users, ₹5L MRR |

---

## PHASE 1 — IMMEDIATE FIXES (Weeks 1-2)
### Platform must work before you invite users

These are blocking issues identified in gap analysis.

#### 1.1 Fix 3 errors preventing local run (This week)

**Error 1: `manglik_compatible` missing from utils_kundli**
```python
# Add to app/utils_kundli.py:
def manglik_compatible(profile_a, profile_b):
    """
    Check Manglik compatibility between two profiles.
    Returns (compatible: bool, message: str)
    """
    if not profile_a or not profile_b:
        return True, "Manglik status not available for one or both profiles."
    
    ma = (profile_a.manglik or '').strip().lower()
    mb = (profile_b.manglik or '').strip().lower()
    
    if not ma or not mb or ma == 'unknown' or mb == 'unknown':
        return True, "Manglik status not confirmed — please consult an astrologer."
    
    # Both Manglik — generally compatible
    if 'yes' in ma and 'yes' in mb:
        return True, "Both are Manglik — generally considered compatible."
    
    # One Manglik, one not — traditional concern
    if ('yes' in ma and 'no' in mb) or ('no' in ma and 'yes' in mb):
        return False, "⚠️ One partner is Manglik and the other is not. Many families seek an astrologer's advice in this case."
    
    # Partial Manglik cases
    if 'partial' in ma or 'partial' in mb:
        return True, "One or both partners have Partial Manglik — milder effect. Recommend consulting an astrologer."
    
    return True, "Manglik compatibility: No concerns detected."
```

**Error 2: Flask-Migrate not finding `db` command → requirements.txt issue**
```bash
# Ensure Flask-Migrate is installed in the venv
pip install Flask-Migrate==4.1.0
# Verify:
flask db --help
```

**Error 3: gevent on Windows crashes**
```python
# Fix wsgi.py — conditional gevent import
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass  # gevent not available on Windows dev — use threading mode
```

#### 1.2 Add income range filter to search (1 day)
`income_lpa` column exists but search doesn't use it.

```python
# In app/search/routes.py, add:
income_range = args.get('income_range', '').strip()
if income_range and '-' in income_range:
    parts = income_range.split('-')
    try:
        min_lpa = int(parts[0])
        max_lpa = int(parts[1]) if parts[1] != '+' else 9999
        query = query.outerjoin(ProfessionalDetails).filter(
            ProfessionalDetails.income_lpa >= min_lpa,
            ProfessionalDetails.income_lpa <= max_lpa,
        )
    except ValueError:
        pass
```

#### 1.3 Add `last_active_at` to User (2 hours)
```python
# models.py — User class
last_active_at = db.Column(db.DateTime, nullable=True, index=True)

# app/__init__.py — before_request hook
@app.before_request
def update_last_active():
    from flask_login import current_user
    if current_user.is_authenticated:
        from datetime import datetime, timedelta
        # Update at most once per hour to avoid DB writes on every request
        if (not current_user.last_active_at or 
                (datetime.utcnow() - current_user.last_active_at).seconds > 3600):
            current_user.last_active_at = datetime.utcnow()
            db.session.commit()
```

#### 1.4 Daily match email (2 hours)
```python
# Add to celery.service ExecStart:
# --beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
# OR simpler: run celery beat as separate process

# app/tasks.py
@celery.task
def send_daily_match_digest(user_id):
    """Send 5 match suggestions to one user."""
    # ... (implementation in RECOMMENDED_ARCHITECTURE.md)

# config.py — add Celery beat schedule
CELERYBEAT_SCHEDULE = {
    'daily-match-emails': {
        'task': 'app.tasks.send_daily_matches_all',
        'schedule': crontab(hour=2, minute=30),  # 8AM IST
    },
}
```

---

## PHASE 2 — PRE-LAUNCH (Weeks 3-6)
### Make platform compelling before public invite

#### 2.1 Profile Completeness Ring — persistent UI
Show completeness % on every authenticated page.
Currently calculated but not prominently displayed.

```html
<!-- In base.html navbar — after logo -->
{% if current_user.is_authenticated %}
<div class="completeness-ring" title="{{ completeness }}% profile complete">
  <svg width="36" height="36" viewBox="0 0 36 36">
    <circle cx="18" cy="18" r="15" fill="none" stroke="#e5e7eb" stroke-width="3"/>
    <circle cx="18" cy="18" r="15" fill="none" stroke="var(--brand)" stroke-width="3"
            stroke-dasharray="{{ (completeness / 100) * 94.25 }} 94.25"
            stroke-dashoffset="23.56" transform="rotate(-90 18 18)"/>
    <text x="18" y="21" text-anchor="middle" font-size="9" fill="var(--brand)">{{ completeness }}%</text>
  </svg>
</div>
{% endif %}
```

#### 2.2 "New Matches" and "Mutual" discovery tabs
Add 2 sub-tabs to home feed. Zero new DB queries — uses existing data.

```python
# main/routes.py home() — add tab parameter
tab = request.args.get('tab', 'best')

if tab == 'new':
    # Profiles created/updated in last 7 days
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)
    q = q.filter(User.created_at >= cutoff)
    
elif tab == 'mutual':
    # Both users have shortlisted each other
    my_shortlists = {s.shortlisted_id for s in current_user.shortlists}
    shortlisted_me = {s.user_id for s in 
                      Shortlist.query.filter_by(shortlisted_id=current_user.id).all()}
    mutual_ids = my_shortlists & shortlisted_me
    q = q.filter(User.id.in_(mutual_ids))
```

#### 2.3 Trust score badge on profile cards
```python
# Add to User model
@property
def trust_score(self):
    score = 0
    if self.phone_verified:                          score += 1
    if self.is_verified:                             score += 1
    if self.profile and self.profile.id_verified:    score += 2
    return score  # 0-4

@property
def trust_label(self):
    labels = {0: None, 1: 'Phone Verified', 2: 'Email + Phone', 
              3: 'ID Verified', 4: 'Fully Verified'}
    return labels.get(self.trust_score)
```

#### 2.4 Per-day pricing on plans page
```html
<!-- templates/membership/plans.html -->
<!-- Add below price -->
<div style="font-size:11px;color:var(--text-3);margin-top:2px;">
  ₹{{ (plan.price_inr / plan.duration_days) | round(0) | int }}/day
</div>
```

---

## PHASE 3 — GROWTH FEATURES (Month 2-3)
### After first 100 registered users

#### 3.1 Surepass Aadhaar KYC Integration (1 week)
```python
# app/utils.py
def verify_aadhaar_via_surepass(aadhaar_number, user_id):
    """
    Verify Aadhaar via Surepass API (₹2/verification).
    Step 1: Send OTP to Aadhaar-linked mobile
    Step 2: Verify OTP → get partial details
    """
    import requests
    API_KEY = current_app.config.get('KYC_API_KEY', '')
    if not API_KEY:
        return {'success': False, 'error': 'KYC not configured'}
    
    # Surepass Aadhaar OTP
    resp = requests.post(
        'https://kyc-api.surepass.io/api/v1/aadhaar-v2/generate-otp',
        json={'id_number': aadhaar_number},
        headers={'Authorization': f'Bearer {API_KEY}'},
        timeout=10,
    )
    return resp.json()
```

#### 3.2 REST API for Mobile (2 weeks)
See MOBILE_APP_READINESS.md for complete spec.
Key endpoints first: auth, profiles/feed, interests, conversations.

#### 3.3 Consolidated Profile Editor
Replace 22 separate pages with 5-section AJAX editor.
Biggest UX improvement for profile completion rate.

---

## PHASE 4 — MOBILE APP (Month 4-6)
### After REST API is stable

#### 4.1 React Native App
- Auth (phone OTP) + onboarding
- Home feed + discovery tabs
- Profile view + interest flow
- Chat (SocketIO with JWT)
- Profile editing

#### 4.2 PWA → Play Store via TWA (faster path)
If React Native timeline is too long, launch PWA via TWA first.
Full native app follows at Month 6.

---

## PHASE 5 — SCALE (Month 7-12)

#### 5.1 Migrate PostgreSQL to RDS (when revenue > ₹15K/month)
#### 5.2 Match score pre-computation (Celery cache)
#### 5.3 Annual plan option (30% discount)
#### 5.4 Background check integration (AuthBridge)
#### 5.5 Video calls UX polish (WebRTC already exists)
#### 5.6 Company registration (Pvt Ltd at milestone)

---

## BUSINESS MILESTONES

| Milestone | Target | What Unlocks |
|-----------|--------|-------------|
| 100 registered users | Month 1 | Real user feedback loop |
| First paid subscriber | Month 1 | Validates pricing model |
| ₹10,000 MRR | Month 2 | Confident in product-market fit |
| GST registration complete | Month 1-2 | Razorpay live payments |
| MSG91 DLT approved | Month 1 | Phone OTP live |
| 500 users | Month 3 | Marketing investment justified |
| ₹50,000 MRR | Month 4 | Hire part-time RM + developer |
| Mobile app launched | Month 6 | 3-5× user acquisition |
| ₹2,00,000 MRR | Month 9 | Consider Pvt Ltd + Series A prep |

---

## WHAT TO DO THIS WEEK (Ordered by impact)

### Day 1
```bash
# Fix the 3 startup errors:
# 1. Add manglik_compatible to utils_kundli.py (10 min)
# 2. Fix wsgi.py gevent Windows error (5 min)
# 3. pip install Flask-Migrate (2 min)
# 4. flask db upgrade && python seed.py
# 5. python wsgi.py → verify http://localhost:5000 loads
```

### Day 2
```bash
# Deploy fixed code to EC2
cd ~/ijodidar && git pull origin main
flask db upgrade
sudo systemctl restart ijodidar ijodidar-celery
# Verify https://ijodidar.com loads
```

### Day 3
```
- Add income filter to search (1 hour)
- Add last_active_at column (migration, 1 hour)
- Invite 5 people from your network to register and test
```

### Day 4-5
```
- Set up Sentry (30 min, free tier)
- Configure MSG91 DLT registration (start now — 3-5 day wait)
- Manually verify test users' email and phone
- Watch them use the platform, note friction points
```

### Week 2
```
- Trust badge on profile cards
- Per-day pricing on plans page
- New matches tab in home feed
- Daily match email (Celery Beat)
```

---

## REVENUE MODEL PROJECTION

### Conservative (Marathi community focus, Pune + Maharashtra)

| Month | Users | Silver Subs | Gold Subs | MRR |
|-------|-------|------------|-----------|-----|
| 1 | 100 | 5 | 2 | ₹4,500 |
| 2 | 250 | 15 | 5 | ₹12,500 |
| 3 | 500 | 35 | 12 | ₹29,500 |
| 4 | 900 | 65 | 22 | ₹54,500 |
| 5 | 1,500 | 110 | 38 | ₹92,500 |
| 6 | 2,500 | 185 | 65 | ₹1,57,000 |

### Key assumptions:
- 5-8% free → paid conversion (industry: 3-12%)
- Silver ₹499/month, Gold ₹333/month (₹999/3mo)
- Assisted plan: 2% of users, ₹4,999 one-time = additional ~₹15,000/month from Month 3
- Referral brings 20% of new users (assumed based on dual-sided reward)

---

## TECH DEBT REGISTER

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| `date_of_birth` String → use `dob` Date everywhere | HIGH | 2h | Age filter accuracy |
| `PartnerPreference.min_income` String → Integer | HIGH | 2h | Income filter works |
| PartnerPreference single religion → JSON list | MEDIUM | 3h | Better preference matching |
| Profile edit 22 pages → 5-section AJAX | HIGH | 1 week | +50% completion rate |
| Score caching in Redis | LOW | 3h | Performance at 5K+ users |
| SocketIO JWT auth | HIGH | 4h | Required for mobile app |
| Flask-JWT-Extended API layer | HIGH | 2 weeks | Required for mobile app |
| Annual subscription plan | MEDIUM | 4h | +LTV |
| Soft-delete for messages | LOW | 2h | User privacy |
| Background check integration | LOW | 1 week | Trust premium feature |

---

*Implementation Roadmap | iJodidar | June 2026*
*Review and update monthly*
