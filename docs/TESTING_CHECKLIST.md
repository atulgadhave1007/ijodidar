# iJodidar — Testing Checklist
## Run locally before every EC2 deployment

---

## SETUP VERIFICATION

```bash
# Start fresh
python wsgi.py
```

- [ ] Server starts without errors on `python wsgi.py`
- [ ] http://localhost:5000 shows landing page
- [ ] http://localhost:5000/register loads registration form
- [ ] http://localhost:5000/console/login loads (no IP restriction in dev)

---

## REGISTRATION & ONBOARDING

- [ ] Register with valid data → success flash, redirect to login
- [ ] Under-18 DOB → "You must be at least 18 years old" error
- [ ] Duplicate email → "Email already registered" error
- [ ] Missing consent checkbox → validation error
- [ ] Verify email (manually set `is_verified=True`)
- [ ] Login → redirected to `/onboarding/gender` (new user)
- [ ] Select gender + looking_for → step 2 (basics)
- [ ] Skip on step 2 → goes to step 3
- [ ] Skip on steps 3-5 → arrives at /home
- [ ] Existing user with profile → NOT sent to onboarding

---

## KUNDLI AUTO-CALCULATION (Critical — test this every deploy)

```bash
# Direct engine test (no server needed)
python3 -c "
from app.vedic_engine import compute_vedic_birth_chart, compute_manglik_approximate
r = compute_vedic_birth_chart('1995-06-15', '09:30', 'Pune')
print('Nakshatra:', r['nakshatra'])
print('Rashi:', r['rashi'])
print('Charan:', r['charan'])
print('Gana:', r['gana'])
print('Nadi:', r['nadi'])
m = compute_manglik_approximate('1995-06-15', '09:30', 'Pune')
print('Manglik:', m['manglik'])
"
```

- [ ] Engine runs without errors
- [ ] Returns nakshatra name (one of 27)
- [ ] Returns rashi name (one of 12)
- [ ] Charan is 1-4
- [ ] Gana is Deva / Manushya / Rakshasa
- [ ] Nadi is Adi / Madhya / Antya

**API tests (server running):**

```bash
# Auto-calculate
curl "http://localhost:5000/kundli/api/calculate?date=1995-06-15&time=09:30&city=Pune"

# Expected: {"nakshatra":"...","rashi":"...","charan":...,"gana":"...","nadi":"...","auto_calculated":true}
```

- [ ] API returns JSON (not 404/500)
- [ ] `auto_calculated: true` in response

**Nadi accuracy tests:**
```bash
# Ashwini × Ardra: BOTH Adi → Nadi Dosha
curl "http://localhost:5000/kundli/api/match?n1=Ashwini&n2=Ardra"
# Expected: Nadi: [0, 8], nadi_dosha: true

# Ashwini × Bharani: Adi × Madhya → NO dosha
curl "http://localhost:5000/kundli/api/match?n1=Ashwini&n2=Bharani"
# Expected: Nadi: [8, 8], nadi_dosha: false
```

- [ ] Ashwini × Ardra: Nadi = 0/8 (dosha)
- [ ] Ashwini × Bharani: Nadi = 8/8 (no dosha)

**Edit form test:**
- [ ] /kundli/edit loads
- [ ] Enter date=1990-06-15, time=09:30, city=Mumbai → click Preview
- [ ] Preview box appears with nakshatra/rashi/gana/nadi/manglik
- [ ] Click "Calculate & Save" → saved to DB
- [ ] Visit any profile → Guna Milan button → match page shows score/36 + breakdown

---

## HOME FEED & MATCHING

- [ ] /home loads with profiles
- [ ] Free plan → profile photos are blurred (filter: blur(8px))
- [ ] Silver plan → photos clear (create test user with Silver plan)
- [ ] Spotlight profiles appear in top 3 slots only
- [ ] No same-gender profiles shown (looking_for filter working)

---

## CONNECT FLOW

- [ ] Send interest → success flash
- [ ] Interest limit: send 5+ interests on Free → limit message + redirect to /plans
- [ ] Block user → blocked user disappears from feed
- [ ] Report user → report created in DB
- [ ] Shortlist → shortlist icon toggles

---

## MESSAGING

- [ ] Accept interest → conversation created → redirect to chat
- [ ] /messages loads inbox
- [ ] /messages/<id> loads chat
- [ ] Send message WITHOUT phone verified → redirect to /auth/verify-phone
- [ ] Type message → appears in chat

---

## MEMBERSHIP

- [ ] /plans loads 4 plan cards (Free, Silver, Gold, Platinum)
- [ ] "Recommended" badge on Gold plan
- [ ] Click upgrade → (needs Razorpay test keys for full test)

---

## CONSOLE

- [ ] /console/login loads (in dev, no IP restriction)
- [ ] Login with wrong password 5 times → "locked for 60 minutes"
- [ ] Login successfully → dashboard loads
- [ ] Dashboard shows user count, registration chart, plan breakdown
- [ ] Users list → search works
- [ ] User detail → toggle active → logs to admin_audit_logs
- [ ] Reports list → filter by status works
- [ ] Assisted list → shows requests
- [ ] Assisted detail → contact log form → submit → log appears
- [ ] TOTP setup page loads at /console/totp-setup

---

## PRIVACY & COMPLIANCE

- [ ] /privacy-policy loads
- [ ] /terms loads
- [ ] Footer shows "Grievance" link on all authenticated pages
- [ ] /account/export → JSON file downloads
- [ ] JSON contains: profile, interests, messages, payments sections
- [ ] /account/delete → type "DELETE" → account anonymised

---

## PERFORMANCE CHECK

```bash
# Time the home feed
time curl -s http://localhost:5000/home -c /tmp/test_session.txt > /dev/null

# Time the kundli calculation
time curl -s "http://localhost:5000/kundli/api/calculate?date=1995-06-15&time=09:30&city=Pune" > /dev/null
```

- [ ] Home feed loads < 2 seconds
- [ ] Kundli API responds < 200ms
- [ ] No 500 errors in server logs

---

## REFERRAL SYSTEM

```bash
# Create referral link
python3 -c "
from wsgi import app
with app.app_context():
    from app.utils import get_or_create_referral
    from app.models import User
    u = User.query.first()
    ref = get_or_create_referral(u)
    print(f'Referral link: http://localhost:5000/register?ref={ref.code}')
"
```

- [ ] Referral link opens registration page
- [ ] Register → verify email + phone → dual reward granted (check DB)

---

## DB INTEGRITY CHECKS

```bash
python3 -c "
from wsgi import app
with app.app_context():
    from app.models import *
    print('Users:', User.query.count())
    print('Plans:', MembershipPlan.query.count())
    print('Cities:', City.query.count())
    print('Admins:', AdminUser.query.count())
    print('Migrations: OK')
"
```

- [ ] 4 membership plans exist
- [ ] 300+ cities seeded
- [ ] At least 1 admin user exists

---

## CHECKLIST SUMMARY

| Area | Tests | Status |
|------|-------|--------|
| Setup | 3 | |
| Registration | 5 | |
| Kundli (critical) | 8 | |
| Home feed | 4 | |
| Connect | 5 | |
| Messaging | 4 | |
| Membership | 3 | |
| Console | 10 | |
| Privacy | 5 | |
| Performance | 3 | |
| Referral | 2 | |
| DB integrity | 3 | |
| **TOTAL** | **55** | |

All 55 checks must pass before EC2 deployment.
