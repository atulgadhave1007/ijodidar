# iJodidar — Database Schema
## 34 Models | PostgreSQL 16 | June 2026

---

## TABLE INDEX

| Table | Rows at launch | Purpose |
|-------|---------------|---------|
| membership_plans | 4 | Free / Silver / Gold / Platinum |
| user_subscriptions | 1/user | Current plan per user |
| users | core | Auth + account state |
| profiles | 1/user | Matrimony attributes |
| interests | many | Send / accept / decline |
| conversations | 1/pair | Chat thread |
| messages | many | Chat messages |
| shortlists | many | Bookmarked profiles |
| countries | 195 | Seeded |
| states | 35 | India states/UTs |
| cities | 300+ | India cities |
| addresses | 1-3/user | Current/native/work |
| educations | many/user | Education history |
| professional_details | 1/user | Career details |
| relation_categories | 10 | Family relation groups |
| relation_types | 42 | Specific relation types |
| family_details | many | Parents / siblings |
| family_relations | many | Relation mappings |
| phone_alternates | many | Extra phone numbers |
| profile_images | 1-5/user | S3 photo references |
| languages | many/user | Languages spoken |
| profile_views | many | Who viewed whom |
| partner_preferences | 1/user | Match criteria |
| block_list | many | Blocked users |
| user_reports | many | Reports to admin |
| kundli_details | 1/user | Birth + Nakshatra data |
| notifications | many/user | In-app alerts |
| success_stories | few | Published couples |
| user_signals | many | Behavioral ranking data |
| referrals | 1/user | Referral code + tracking |
| assisted_requests | few | RM plan requests |
| rm_contact_logs | many | RM interaction history |
| admin_audit_logs | many | Staff action trail |
| admin_users | <10 | Console staff accounts |

---

## CORE TABLES

### users
```sql
CREATE TABLE users (
    id                  SERIAL PRIMARY KEY,
    username            VARCHAR(64) UNIQUE NOT NULL,
    first_name          VARCHAR(50) NOT NULL,
    last_name           VARCHAR(50) NOT NULL,
    email               VARCHAR(120) UNIQUE NOT NULL,
    phone               VARCHAR(15),
    password_hash       VARCHAR(255) NOT NULL,
    is_verified         BOOLEAN DEFAULT FALSE,      -- email verified
    verify_token        VARCHAR(100),
    verify_token_expiry TIMESTAMP,                  -- 24h expiry
    reset_token         VARCHAR(100),
    reset_token_expiry  TIMESTAMP,
    is_active_acc       BOOLEAN DEFAULT TRUE,
    is_hidden           BOOLEAN DEFAULT FALSE,
    is_staff            BOOLEAN DEFAULT FALSE,       -- exclude from feeds/stats
    phone_verified      BOOLEAN DEFAULT FALSE,
    phone_otp           VARCHAR(255),               -- bcrypt hashed OTP
    phone_otp_expiry    TIMESTAMP,
    failed_login_count  INTEGER DEFAULT 0,          -- lockout tracking
    locked_until        TIMESTAMP,                  -- 30-min lock after 10 fails
    consented_at        TIMESTAMP,                  -- DPDP consent timestamp
    session_version     INTEGER DEFAULT 1,          -- invalidate on password change
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
-- Indexes
CREATE UNIQUE INDEX ix_users_phone_verified_unique ON users(phone)
    WHERE phone_verified = TRUE AND phone IS NOT NULL;
CREATE INDEX ix_users_verify_token ON users(verify_token);
CREATE INDEX ix_users_reset_token  ON users(reset_token);
```

### profiles
```sql
CREATE TABLE profiles (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER REFERENCES users(id) NOT NULL UNIQUE,
    gender            VARCHAR(10),                 -- Male / Female / Other
    looking_for       VARCHAR(10),                 -- Male / Female / Any
    date_of_birth     VARCHAR(15),                 -- legacy string
    dob               DATE,                        -- new proper Date column
    birth_time        VARCHAR(10),
    birth_city        VARCHAR(100),
    bio               TEXT,
    height            INTEGER,                     -- cm
    religion          VARCHAR(50),
    caste             VARCHAR(100),
    gotra             VARCHAR(50),
    manglik           VARCHAR(20),                 -- Yes / No / Partial
    mother_tongue     VARCHAR(50),
    marital_status    VARCHAR(30),
    diet              VARCHAR(20),
    smoking           VARCHAR(20),
    drinking          VARCHAR(20),
    is_nri            BOOLEAN DEFAULT FALSE,
    nri_country       VARCHAR(60),
    profile_picture   VARCHAR(300),                -- S3 URL (primary photo)
    birth_nakshatra   VARCHAR(40),                 -- synced from kundli_details
    birth_rashi       VARCHAR(30),                 -- synced from kundli_details
    id_verified       BOOLEAN DEFAULT FALSE,
    id_verified_at    TIMESTAMP,
    is_spotlight      BOOLEAN DEFAULT FALSE,
    spotlight_expires_at TIMESTAMP,
    completeness_pct  INTEGER DEFAULT 0,
    ui_language       VARCHAR(5) DEFAULT 'en',
    hobbies           TEXT,                        -- JSON array
    linkedin_url      VARCHAR(200),
    about_family      TEXT,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);
```

### membership_plans
```sql
CREATE TABLE membership_plans (
    id                    SERIAL PRIMARY KEY,
    name                  VARCHAR(50) UNIQUE NOT NULL,
    price_inr             INTEGER NOT NULL DEFAULT 0,
    duration_days         INTEGER NOT NULL DEFAULT 0,  -- 0 = forever (Free)
    max_interests         INTEGER DEFAULT 5,
    can_message           BOOLEAN DEFAULT FALSE,
    can_view_phone        BOOLEAN DEFAULT FALSE,
    can_view_full_profile BOOLEAN DEFAULT TRUE,
    highlighted           BOOLEAN DEFAULT FALSE,       -- "Recommended" badge
    description           TEXT
);
-- Seed data
INSERT INTO membership_plans VALUES
(1,'Free',0,0,5,false,false,true,false,'Basic access'),
(2,'Silver',499,30,20,true,false,true,false,'Most popular'),
(3,'Gold',999,90,50,true,true,true,true,'Best value'),
(4,'Platinum',1999,180,-1,true,true,true,false,'Unlimited');
```

### kundli_details
```sql
CREATE TABLE kundli_details (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) NOT NULL UNIQUE,
    birth_date  VARCHAR(15),
    birth_time  VARCHAR(10),
    birth_city  VARCHAR(100),
    birth_lat   FLOAT,
    birth_lng   FLOAT,
    rashi       VARCHAR(30),         -- Moon sign / Janma Rashi
    nakshatra   VARCHAR(40),         -- Birth star (auto-calculated)
    charan      INTEGER,             -- Pada 1-4 (auto-calculated)
    gana        VARCHAR(20),         -- Deva / Manushya / Rakshasa (auto)
    nadi        VARCHAR(20),         -- Adi / Madhya / Antya (auto)
    varna       VARCHAR(20),         -- auto-calculated
    vashya      VARCHAR(20),         -- auto-calculated
    yoni        VARCHAR(30),         -- auto-calculated
    graha_maitri VARCHAR(20),
    bhakoot     VARCHAR(20),
    manglik     VARCHAR(20)          -- Yes / No / Partial (approximate)
);
```

### admin_audit_logs
```sql
CREATE TABLE admin_audit_logs (
    id          SERIAL PRIMARY KEY,
    admin_id    INTEGER REFERENCES admin_users(id) NOT NULL,
    action      VARCHAR(80) NOT NULL,
    target_type VARCHAR(30),      -- 'user' | 'subscription' | 'report'
    target_id   INTEGER,
    detail      TEXT,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
-- Indexes
CREATE INDEX ix_audit_admin_id   ON admin_audit_logs(admin_id);
CREATE INDEX ix_audit_created_at ON admin_audit_logs(created_at);
CREATE INDEX ix_audit_target     ON admin_audit_logs(target_type, target_id);
```

### user_signals
```sql
CREATE TABLE user_signals (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) NOT NULL,
    target_user_id  INTEGER REFERENCES users(id) NOT NULL,
    signal_type     VARCHAR(30) NOT NULL,
    -- interest_sent | interest_accepted | interest_declined
    -- profile_viewed | shortlisted | blocked | reported
    signal_value    FLOAT NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_signal_user_target ON user_signals(user_id, target_user_id);
CREATE INDEX ix_signal_user_type   ON user_signals(user_id, signal_type);
```

### admin_users
```sql
CREATE TABLE admin_users (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(80) NOT NULL,
    email               VARCHAR(120) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    role                VARCHAR(30) NOT NULL DEFAULT 'executive',
    -- ceo | manager | executive | rm | moderator
    is_active           BOOLEAN DEFAULT TRUE,
    last_login          TIMESTAMP,
    failed_login_count  INTEGER DEFAULT 0,
    locked_until        TIMESTAMP,
    totp_secret         VARCHAR(64),              -- TOTP 2FA
    totp_enabled        BOOLEAN DEFAULT FALSE,
    totp_verified_at    TIMESTAMP,
    created_at          TIMESTAMP DEFAULT NOW(),
    created_by_id       INTEGER REFERENCES admin_users(id)
);
```

---

## KEY RELATIONSHIPS

```
User 1→1 Profile
User 1→* UserSubscription  →  MembershipPlan
User 1→* Address  →  City  →  State  →  Country
User 1→* Education
User 1→* ProfessionalDetails
User 1→* FamilyDetails  →  FamilyRelation  →  RelationType
User 1→* ProfileImage (S3 URLs)
User 1→* Language
User 1→1 KundliDetail
User 1→1 PartnerPreference
User 1→1 Referral (code)
User 1→? AssistedRequest  →  RMContactLog

Interest: sender_id → User, receiver_id → User
Conversation: user1_id → User, user2_id → User
Message: conversation_id → Conversation, sender_id → User
UserSignal: user_id → User, target_user_id → User
AdminAuditLog: admin_id → AdminUser
```

---

## PERFORMANCE INDEXES

```sql
-- Home feed query
CREATE INDEX ix_profiles_gender         ON profiles(gender);
CREATE INDEX ix_profiles_looking_for    ON profiles(looking_for);
CREATE INDEX ix_profiles_religion       ON profiles(religion);
CREATE INDEX ix_profiles_is_spotlight   ON profiles(is_spotlight);
CREATE INDEX ix_profiles_dob            ON profiles(dob);

-- Message inbox
CREATE INDEX ix_conversations_user1_id     ON conversations(user1_id);
CREATE INDEX ix_conversations_user2_id     ON conversations(user2_id);
CREATE INDEX ix_messages_conversation_id   ON messages(conversation_id);
CREATE INDEX ix_messages_is_read           ON messages(is_read);

-- Notifications
CREATE INDEX ix_notifications_user_id      ON notifications(user_id);
CREATE INDEX ix_notifications_is_read      ON notifications(is_read);

-- Subscriptions
CREATE INDEX ix_user_subscriptions_user_id   ON user_subscriptions(user_id);
CREATE INDEX ix_user_subscriptions_is_active ON user_subscriptions(is_active);

-- Signals
CREATE INDEX ix_signal_user_target ON user_signals(user_id, target_user_id);
```
