# iJodidar — Ideal Profile Structure
## Production-Grade Profile Data Model

---

## CURRENT STRUCTURE ASSESSMENT

### What's Well-Designed
- `Profile` model has 40+ fields covering most Indian matrimony attributes
- Separate `ProfessionalDetails`, `Education`, `FamilyDetails` models — correct normalisation
- `KundliDetail` separate from profile — correct
- `PartnerPreference` as separate model — correct
- `income_lpa` integer column exists (added Phase 2)

### What Needs Fixing

| Issue | Current | Ideal |
|-------|---------|-------|
| DOB | `date_of_birth` String (legacy) + `dob` Date | Use `dob` Date everywhere, drop String |
| Income preference | `min_income` String "3 LPA" | `min_income_lpa` Integer |
| Partner prefs | Single value per field (one religion) | JSON array (multiple religions acceptable) |
| `last_active_at` | Missing | Add to User model |
| Profile completeness | Calculated in Python on every request | Cache in `profiles.completeness_pct` |
| No "seeking on behalf of" | Missing | Father/Mother/Self/Sibling radio |

---

## IDEAL PROFILE DATA STRUCTURE

### Section 1 — Identity (Required for basic matching)

```python
class User:
    # Auth
    first_name          String(50)  NOT NULL
    last_name           String(50)  NOT NULL
    email               String(120) UNIQUE
    phone               String(15)  UNIQUE (verified)
    phone_verified      Boolean
    email_verified      Boolean     # is_verified in current code
    last_active_at      DateTime    # ADD THIS — "Active 2 days ago"
    
class Profile:
    user_id             Integer FK  UNIQUE
    gender              Enum(Male, Female, Other)
    looking_for         Enum(Male, Female, Any)
    profile_for         Enum(Self, Son, Daughter, Brother, Sister, Relative)  # ADD
    dob                 Date        # Use this, drop date_of_birth String
    birth_city          String(100)
    birth_state         String(100)
```

### Section 2 — Physical (Affects match score and search)

```python
    height              Integer     # cm (150-220 range)
    weight              Integer     # kg (optional)
    complexion          Enum(Very_Fair, Fair, Wheatish, Dark)
    body_type           Enum(Slim, Average, Athletic, Heavy)
```

### Section 3 — Religion & Community (Critical for Indian matrimony)

```python
    religion            String(50)  # Hindu, Muslim, Christian, Sikh, etc.
    caste               String(80)
    sub_caste           String(80)
    gotra               String(80)
    marathi_sub_caste   String(80)  # 96 Kuli Maratha, CKP, Deshastha etc.
    mother_tongue       String(50)
    manglik             Enum(Yes, No, Partial, Unknown)
    
    # Partner religion preference — MULTIPLE VALUES (JSON array)
    # Current: pref.religion = "Hindu" (single)
    # Ideal:   pref.religion_list = ["Hindu", "Jain", "Buddhist"] (JSON)
```

### Section 4 — Lifestyle

```python
    marital_status      Enum(Never_Married, Divorced, Widowed, Separated)
    have_children       Enum(No, Yes_living_together, Yes_not_living_together)
    diet                Enum(Vegetarian, Non_Vegetarian, Eggetarian, Vegan, Jain)
    smoking             Enum(Never, Occasionally, Regularly)
    drinking            Enum(Never, Occasionally, Regularly)
    
    bio                 Text        # 50-500 chars
    hobbies             JSON        # ["Reading", "Trekking", "Cooking"]
```

### Section 5 — Career & Education

```python
class ProfessionalDetails:
    user_id             Integer FK
    occupation          String(100)    # "Software Engineer"
    employment_type     Enum(Private, Government, Self_Employed, Business, NRI, Not_Working)
    company_name        String(100)
    designation         String(100)
    income_lpa          Integer        # Annual income in LPA
    # PartnerPreference.min_income_lpa   Integer (ADD THIS)
    # PartnerPreference.max_income_lpa   Integer (ADD THIS)

class Education:
    user_id             Integer FK
    degree              String(100)    # "B.Tech", "MBBS", "CA"
    specialization      String(100)    # "Computer Science"
    institution         String(200)
    year                Integer
    # education_level (computed): High School / Graduate / Post-Graduate / PhD
```

### Section 6 — Family

```python
class FamilyDetails:
    user_id             Integer FK
    family_type         Enum(Joint, Nuclear, Extended)
    family_status       Enum(Middle_Class, Upper_Middle_Class, Rich, Affluent)
    father_alive        Boolean
    father_occupation   String(100)
    mother_alive        Boolean
    mother_occupation   String(100)
    brothers            Integer     # count
    sisters             Integer     # count
    brothers_married    Integer
    sisters_married     Integer
    about_family        Text        # free text about family background
```

### Section 7 — Location

```python
class Address:
    user_id             Integer FK
    tag                 Enum(current, native, work)
    address1            String(200)
    address2            String(200)
    city_id             Integer FK → City
    state_id            Integer FK → State
    country_id          Integer FK → Country
    pincode             String(10)
    is_default          Boolean
```

### Section 8 — Kundli / Vedic

```python
class KundliDetail:
    user_id             Integer FK  UNIQUE
    birth_date          String(10)  # YYYY-MM-DD (for display)
    birth_time          String(5)   # HH:MM
    birth_city          String(100)
    birth_lat           Float
    birth_lng           Float
    nakshatra           String(40)  # auto-calculated
    rashi               String(30)  # auto-calculated
    charan              Integer     # 1-4
    gana                String(20)  # auto-calculated
    nadi                String(20)  # auto-calculated
    varna               String(20)  # auto-calculated
    yoni                String(30)  # auto-calculated
    manglik             String(20)  # approximate
    auto_calculated     Boolean     # True if computed from DOB+time+city
```

### Section 9 — Partner Preferences (Upgraded)

```python
class PartnerPreference:
    user_id             Integer FK  UNIQUE
    
    # Age
    min_age             Integer
    max_age             Integer
    
    # Physical
    min_height          Integer     # cm
    max_height          Integer
    
    # Community — MULTIPLE VALUES (upgrade from single String)
    religion_list       JSON        # ["Hindu", "Jain"] — accept any of these
    caste_list          JSON        # ["Maratha", "Any"] 
    mother_tongue       String(50)
    
    # Income — Integer range (upgrade from String)
    min_income_lpa      Integer     # ADD THIS
    max_income_lpa      Integer     # ADD THIS
    
    # Status
    marital_status      String(30)
    manglik             String(20)
    
    # Lifestyle
    diet                String(30)
    smoking             String(20)
    drinking            String(20)
    
    # Location
    state_list          JSON        # ["Maharashtra", "Goa"]
    city_list           JSON        # ["Pune", "Mumbai", "Nagpur"]
    
    # Education
    min_education_level String(50)  # Graduate / Post-Graduate / PhD
    
    # About
    about               Text        # "I'm looking for..."
```

### Section 10 — Verification & Trust

```python
class Profile:
    # Verification flags
    id_verified         Boolean     # Aadhaar/PAN verified
    id_verified_at      DateTime
    id_document_type    String(20)  # Aadhaar / PAN / Passport
    background_verified Boolean     # Third-party background check
    photo_verified      Boolean     # Face present in photo (auto)
    
    # Computed trust score (0-5)
    @property
    def trust_score(self):
        score = 0
        if self.user.phone_verified:  score += 1
        if self.user.is_verified:     score += 1   # email
        if self.id_verified:          score += 2
        if self.background_verified:  score += 1
        return score
    
    # Profile completeness (cached, updated on save)
    completeness_pct    Integer     # 0-100, updated on profile save
```

---

## PROFILE COMPLETENESS SCORING (Revised)

### Current scoring: ad-hoc Python calculation on every request
### Ideal: stored integer, updated on each profile edit

```python
COMPLETENESS_WEIGHTS = {
    # Identity (30 pts)
    'photo':          10,  # primary photo
    'dob':             5,
    'religion':        5,
    'height':          3,
    'marital_status':  3,
    'gender':          2,
    'looking_for':     2,
    
    # Bio & Personality (20 pts)
    'bio':             10,  # minimum 50 chars
    'hobbies':          5,
    'diet':             5,
    
    # Career (20 pts)
    'occupation':      10,
    'income_lpa':       5,
    'education':        5,
    
    # Community (15 pts)
    'caste':            8,
    'mother_tongue':    4,
    'gotra':            3,
    
    # Family (10 pts)
    'family_type':      5,
    'about_family':     5,
    
    # Location (5 pts)
    'current_city':     5,
}
# TOTAL: 100 pts

# Milestones:
# 30 pts → "Basic profile complete — can send interests"
# 60 pts → "Good profile — getting responses"  
# 85 pts → "Complete profile — maximum visibility"
# 95 pts → "Premium profile" (requires ID verification)
```

---

## PROFILE VISIBILITY RULES

```python
def profile_visible_to(viewer, profile_owner):
    """What a viewer can see on a profile."""
    
    # Always visible (anyone can see)
    ALWAYS = ['name', 'age', 'city', 'religion', 'caste', 'occupation',
              'education', 'height', 'marital_status', 'bio']
    
    # Blurred photos for Free plan viewers
    photos_clear = viewer.plan_name != 'Free'
    
    # Phone number — Gold+ only, AND must have accepted interest
    phone_visible = (
        viewer.plan_name in ('Gold', 'Platinum') and
        interest_accepted(viewer, profile_owner)
    )
    
    # Full contact details (address, alternate phone)
    # Only after mutual interest acceptance
    full_contact = interest_accepted(viewer, profile_owner)
    
    return {
        'photos_clear':    photos_clear,
        'phone':           phone_visible,
        'full_contact':    full_contact,
    }
```

---

## DATABASE MIGRATION NEEDED

### To implement ideal structure:

```sql
-- 1. Use dob (Date) everywhere instead of date_of_birth (String)
ALTER TABLE profiles RENAME COLUMN date_of_birth TO date_of_birth_legacy;
-- (dob Date column already exists — just stop writing to date_of_birth_legacy)

-- 2. Add missing columns
ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP;
ALTER TABLE profiles ADD COLUMN profile_for VARCHAR(20) DEFAULT 'Self';
ALTER TABLE partner_preferences ADD COLUMN min_income_lpa INTEGER;
ALTER TABLE partner_preferences ADD COLUMN max_income_lpa INTEGER;
ALTER TABLE partner_preferences ADD COLUMN religion_list TEXT;  -- JSON
ALTER TABLE partner_preferences ADD COLUMN city_list TEXT;      -- JSON

-- 3. Add index on last_active_at (used in "active recently" sort)
CREATE INDEX ix_users_last_active ON users(last_active_at);

-- 4. Update completeness_pct on save (add trigger or app-level hook)
```

---

*Ideal Profile Structure | iJodidar | June 2026*
