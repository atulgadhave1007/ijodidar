# DATABASE_ARCHITECTURE.md
## iJodidar v2 — Database Architecture
## June 2026

---

## OVERVIEW

**Engine:** PostgreSQL 16 (EC2 co-located; RDS in Phase 2)
**ORM:** SQLAlchemy 2.0 with Flask-SQLAlchemy 3.1
**Migrations:** Alembic 1.16 via Flask-Migrate 4.1
**Connection pool:** pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=1800s

Total: 34 models across 34 tables. All correctly normalised for 3NF.
Foreign keys and cascade rules are correctly defined.

---

## DOMAIN MODEL MAP

```
AUTHENTICATION DOMAIN
  users (core — all auth state)
  └── user_subscriptions (active plan per user)
       └── membership_plans (plan configuration)

PROFILE DOMAIN
  users → profiles (1:1 — matrimony attributes)
  users → addresses (1:N — current/native/work)
  users → educations (1:N)
  users → professional_details (1:N — career + income)
  users → languages (1:N)
  users → profile_images (1:N — S3 URLs, 3 sizes each)
  users → kundli_details (1:1 — birth chart data)
  users → partner_preferences (1:1 — match criteria)
  users → phone_alternates (1:N)

LOCATION DOMAIN
  countries → states → cities → addresses

FAMILY DOMAIN
  users → family_details (1:N — family member records)
  family_details → family_relations (M:M with self)
  relation_categories → relation_types → family_relations

SOCIAL DOMAIN
  users → interests (1:N sent, 1:N received)
  users × users → conversations (unique pair)
  conversations → messages (1:N)
  users → shortlists (1:N)
  users → block_list (1:N)
  users → user_reports (1:N)
  users → profile_views (1:N viewer, 1:N viewed)
  users → notifications (1:N)
  users → user_signals (1:N given, 1:N received)

BUSINESS DOMAIN
  users → referrals (1:N made, 1:1 referred_by)
  users → assisted_requests (1:1)
  assisted_requests → rm_contact_logs (1:N)
  users → success_stories (decoupled — no FK)

ADMIN DOMAIN
  admin_users (completely separate from users)
  admin_users → admin_audit_logs (1:N — immutable)
  admin_users → rm_contact_logs (FK as admin who logged)
  (future) users → user_devices (1:N FCM tokens)
```

---

## INDEX STRATEGY

### Existing Indexes (confirmed in migration 258790d00566 + a1b2c3d4e5f6)

| Table | Indexed Columns | Purpose |
|-------|----------------|---------|
| users | username, email, is_staff, verify_token, reset_token | Auth lookups |
| profiles | gender, looking_for, religion, marital_status, caste, is_spotlight, dob, height, is_nri, marathi_sub_caste | Home feed + search filters |
| interests | status, sender_id, receiver_id | Interest queries |
| conversations | user1_id, user2_id | Inbox queries |
| messages | conversation_id, is_read | Unread count |
| notifications | user_id, is_read | Badge count |
| user_subscriptions | user_id, is_active | Active plan lookup |
| user_signals | (user_id, target_user_id), (user_id, signal_type) | Signal boost queries |
| admin_audit_logs | admin_id, created_at, (target_type, target_id) | Audit queries |

### New Indexes Required (v2)

| Table | New Index | Purpose |
|-------|-----------|---------|
| users | last_active_at | "Active recently" sort + Celery Beat target |
| profile_views | UNIQUE (viewer_id, viewed_id, DATE(timestamp)) | Daily deduplication |
| profiles | completeness_pct | Completeness-based sorting |
| user_devices | UNIQUE (user_id, fcm_token) | Prevent FCM duplicates |

---

## KNOWN DATA QUALITY ISSUES

| Table | Column | Issue | Resolution |
|-------|--------|-------|-----------|
| profiles | date_of_birth | String format inconsistent (YYYY-MM-DD vs DD-MM-YYYY vs DD/MM/YYYY) | All new writes use `dob` Date column; `date_of_birth` frozen |
| partner_preferences | min_income | String "3 LPA" — not queryable | New `min_income_lpa` Integer column |
| user_subscriptions | interests_reset_at | Set only at creation; monthly reset logic in model property (wrong) | Move to Celery Beat task |
| profile_views | (all) | No daily deduplication at DB level | Add unique index Sprint 2 |

---

## MIGRATION CHAIN (complete)

```
258790d00566  Initial — 34 tables, all base schema
      ↓
a1b2c3d4e5f6  Phase 17 — lockout columns, 10 indexes
      ↓
b2c3d4e5f6a7  Phase 1 Strategic — session_version
      ↓
c3d4e5f6a7b8  Phase 2 Strategic — dob Date, income_lpa, audit_logs
      ↓
d4e5f6a7b8c9  Phase 3 Strategic — user_signals, rm_contact_logs, TOTP
      ↓
e5f6a7b8c9d0  v2 Sprint 1 — last_active_at, completeness_pct, partner_pref columns
      ↓
f6a7b8c9d0e1  v2 Sprint 2 — family consent, profile_views unique index
      ↓
g7b8c9d0e1f2  v2 Sprint 3 — user_devices, profile_for
      ↓
h8c9d0e1f2g3  v2 Sprint 4 — match_score_cache, message soft-delete
```

---

## SCALABILITY THRESHOLDS

| Threshold | Trigger | Action |
|-----------|---------|--------|
| 500 active users | DB CPU > 60% sustained | Tune query indexes; add read-through cache for notification counts |
| 2K active users | DB CPU > 80% | Migrate PostgreSQL to RDS t3.small |
| 5K active users | Home feed latency > 500ms | Enable match score pre-computation cache |
| 10K active users | RDS t3.small CPU > 70% | Add RDS read replica; route read queries to replica |
| 50K active users | Read replica under load | Upgrade RDS instance; consider connection pooling (PgBouncer) |

---

*DATABASE_ARCHITECTURE.md | iJodidar v2 | June 2026*
