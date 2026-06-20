# iJodidar — Database Migrations
## Alembic Migration Chain | 5 Versions

---

## MIGRATION CHAIN

```
(base)
  └─ 258790d00566  Initial schema (all 34 tables)
       └─ a1b2c3d4e5f6  Phase 17 security fixes
            └─ b2c3d4e5f6a7  Phase 1 Strategic
                 └─ c3d4e5f6a7b8  Phase 2 Strategic
                      └─ d4e5f6a7b8c9  Phase 3 Strategic  ← HEAD
```

---

## MIGRATION 1: 258790d00566 — Initial Schema

Creates all 34 tables. Run once on a fresh database.

**Tables created:**
membership_plans, user_subscriptions, users, profiles, interests, conversations,
messages, shortlists, countries, states, cities, addresses, educations,
professional_details, relation_categories, relation_types, family_details,
family_relations, phone_alternates, profile_images, languages, profile_views,
partner_preferences, block_list, user_reports, kundli_details, notifications,
success_stories, user_signals, referrals, assisted_requests, rm_contact_logs,
admin_users

---

## MIGRATION 2: a1b2c3d4e5f6 — Phase 17 Security Fixes

**New columns (users):**
- `verify_token_expiry` TIMESTAMP — email verify link expires in 24h
- `failed_login_count` INTEGER DEFAULT 0 — brute force tracking
- `locked_until` TIMESTAMP — 30-min lockout after 10 failures
- `consented_at` TIMESTAMP — DPDP consent recording
- `phone_otp` widened from VARCHAR(6) → VARCHAR(255) for bcrypt hash

**New columns (user_subscriptions):**
- `interests_this_month` INTEGER DEFAULT 0 — monthly interest tracking
- `interests_reset_at` TIMESTAMP — auto-reset trigger

**New columns (admin_users):**
- `failed_login_count` INTEGER DEFAULT 0
- `locked_until` TIMESTAMP

**New indexes (10 total):**
- conversations: user1_id, user2_id
- messages: conversation_id, is_read
- notifications: user_id, is_read
- user_subscriptions: user_id, is_active
- users: verify_token, reset_token

**Unique partial index:**
```sql
CREATE UNIQUE INDEX ix_users_phone_verified_unique
ON users(phone) WHERE phone_verified = TRUE AND phone IS NOT NULL;
```

---

## MIGRATION 3: b2c3d4e5f6a7 — Phase 1 Strategic

**New columns (users):**
- `session_version` INTEGER DEFAULT 1 — session invalidation on password change

---

## MIGRATION 4: c3d4e5f6a7b8 — Phase 2 Strategic

**New columns (profiles):**
- `dob` DATE — proper Date type alongside legacy `date_of_birth` string

**Data migration:** Copies existing `date_of_birth` strings → `dob` Date
(handles YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY formats)

**New columns (professional_details):**
- `income_lpa` INTEGER — annual income in LPA for range filtering

**Data migration:** Parses `package` text (e.g. "10-15 LPA") → `income_lpa` integer

**New table: admin_audit_logs**
```
id, admin_id, action, target_type, target_id, detail, ip_address, created_at
```

---

## MIGRATION 5: d4e5f6a7b8c9 — Phase 3 Strategic

**New table: user_signals** (if not already created by initial migration)
```
id, user_id, target_user_id, signal_type, signal_value, created_at
```

**New table: rm_contact_logs** (if not already created)
```
id, request_id, admin_id, contact_type, summary, outcome, next_action, logged_at
```

**New columns (admin_users):**
- `totp_secret` VARCHAR(64) — TOTP 2FA secret
- `totp_enabled` BOOLEAN DEFAULT FALSE
- `totp_verified_at` TIMESTAMP

**New columns (assisted_requests):**
- `assigned_rm_id` INTEGER FK → admin_users
- `profiles_target` INTEGER DEFAULT 15
- `profiles_sent` INTEGER DEFAULT 0
- `family_pref_notes` TEXT
- `plan_tier` VARCHAR(20) DEFAULT 'basic'
- `payment_ref` VARCHAR(100)

**New columns (referrals):**
- `referred_rewarded_at` TIMESTAMP
- `ip_address` VARCHAR(45)
- `device_fingerprint` VARCHAR(100)

---

## DEPLOY COMMANDS

### Fresh database (first time)
```bash
# On EC2 or local
export FLASK_APP=wsgi.py
flask db upgrade

# Seed reference data
python seed.py
```

### Incremental update (code already has migrations)
```bash
cd ~/ijodidar
git pull origin main
source venv/bin/activate
export FLASK_APP=wsgi.py
flask db upgrade
sudo systemctl restart ijodidar ijodidar-celery
```

### Verify current state
```bash
flask db current
flask db history
```

### Rollback one migration
```bash
flask db downgrade -1
```

### Rollback to specific migration
```bash
flask db downgrade a1b2c3d4e5f6
```

---

## LOCAL TESTING (SQLite — no PostgreSQL needed)

```bash
# .env has no DATABASE_URL → SQLite used automatically
flask db upgrade        # creates instance/dev.db
python seed.py          # seeds plans, cities, admin
python wsgi.py          # start server
```

SQLite location: `instance/dev.db`

View with: DB Browser for SQLite (https://sqlitebrowser.org/)

---

## PRODUCTION DATABASE MAINTENANCE

```bash
# Daily backup (already configured as cron)
PGPASSWORD='pass' pg_dump -U ijodidar_user -h localhost ijodidar \
  > ~/db_backups/backup_$(date +%Y%m%d_%H%M).sql

# Check table sizes
psql -U ijodidar_user -d ijodidar -h localhost -c "
SELECT tablename, n_live_tup as rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC LIMIT 15;"

# Check index usage
psql -U ijodidar_user -d ijodidar -h localhost -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC LIMIT 20;"
```
