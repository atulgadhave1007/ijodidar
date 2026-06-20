# AWS_ARCHITECTURE.md
## iJodidar v2 — AWS Infrastructure Architecture
## June 2026

---

## CURRENT STATE: SINGLE EC2 MONOLITH

```
Region: ap-south-1 (Mumbai)
Account: Atul Gadhave AWS account

Infrastructure:
  EC2 t3.small (13.205.222.218)
    ├── Application: Flask + Gunicorn + SocketIO
    ├── Database: PostgreSQL 16 (port 5432)
    ├── Cache: Redis (port 6379)
    ├── Queue worker: Celery
    └── Web server: Nginx

Route 53: ijodidar.com → EC2 IP
SSL: Let's Encrypt (auto-renew via certbot)

S3: ijodidar-images (pending — not confirmed created)
SES: Pending production access approval

Monthly cost: ~₹957
```

---

## PHASE 1 — CURRENT (0-2K users, Month 1-4)

No infrastructure changes. Cost remains ~₹957/month.

**Immediate additions (zero cost):**

| Action | Service | Cost |
|--------|---------|------|
| SES production access | AWS SES | ₹0 (62K/month free from EC2) |
| S3 bucket creation | S3 | ~₹150/month (photos) |
| IAM role for EC2 → S3 + SES | IAM | ₹0 |
| UptimeRobot monitoring | External | ₹0 (free tier) |
| CloudWatch basic metrics | CloudWatch | ₹0 (free tier) |

**S3 bucket configuration:**
```
Bucket: ijodidar-images (ap-south-1)
ACL: Private (all objects)
Versioning: Disabled (photos only, no version history needed)
Lifecycle: Delete incomplete multipart uploads after 7 days
CORS: Allow PUT from ijodidar.com (for future client-side upload)
```

**IAM role configuration:**
```
Role: ijodidar-ec2-role
Trust: EC2 service
Policies:
  - AmazonS3FullAccess (scoped to ijodidar-images bucket)
  - AmazonSESFullAccess (scoped to ap-south-1)
Attach to: EC2 instance (removes need for access keys in .env)
```

---

## PHASE 2 — GROWTH (2K-10K users, Month 4-8)

**Trigger:** Revenue > ₹25,000/month OR 500+ daily active users

```
BEFORE:                          AFTER:
EC2 t3.small                     EC2 t3.small (app only)
  ├── App                          └── App + Nginx + Celery
  ├── PostgreSQL         →        RDS t3.micro PostgreSQL (dedicated)
  └── Redis                       ElastiCache t3.micro Redis (dedicated)
                                  EC2 t3.micro (Celery + Beat worker)
```

**Migration steps (RDS):**

```
1. Take pg_dump from EC2 PostgreSQL
2. Create RDS t3.micro, same VPC as EC2, private subnet
3. Restore dump to RDS
4. Update DATABASE_URL in .env
5. Verify connection via psql from EC2
6. Restart app; verify health
7. Stop EC2 PostgreSQL service
8. (Optional) delete PostgreSQL from EC2 after 2 weeks
```

**Estimated Phase 2 cost:**

| Service | Monthly |
|---------|---------|
| EC2 t3.small (app) | ₹700 |
| EC2 t3.micro (Celery) | ₹350 |
| RDS t3.micro | ₹1,400 |
| ElastiCache t3.micro | ₹1,400 |
| S3 + CloudFront | ₹500 |
| **Total** | **~₹4,350/month** |

---

## PHASE 3 — SCALE (10K-50K users, Month 12+)

**Trigger:** Revenue > ₹1,50,000/month OR 2,000+ concurrent users

```
                         ┌────────────────────────┐
Internet ──→ Route 53 ──→│ Application Load Balancer│
                         └────────────┬───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
             EC2 t3.medium    EC2 t3.medium      EC2 t3.small
             (App server 1)   (App server 2)    (Celery + Beat)
                    │                 │
                    └─────────┬───────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
         RDS t3.small    RDS t3.small    ElastiCache
         (Write primary)  (Read replica)  (Cluster)
```

**SocketIO horizontal scaling requirement:**
Multiple app servers require Redis pub/sub for SocketIO message routing.
Configure: `socketio = SocketIO(message_queue='redis://redis-host:6379/5')`
Must be done before adding second app server.

**Estimated Phase 3 cost:**

| Service | Monthly |
|---------|---------|
| EC2 t3.medium × 2 (app) | ₹3,200 |
| EC2 t3.small (Celery) | ₹700 |
| ALB | ₹800 |
| RDS t3.small + read replica | ₹6,400 |
| ElastiCache cluster | ₹2,800 |
| S3 + CloudFront | ₹800 |
| **Total** | **~₹14,700/month** |

---

## DISASTER RECOVERY PLAN

| Component | Backup Method | Frequency | RTO | RPO |
|-----------|--------------|-----------|-----|-----|
| PostgreSQL | pg_dump → S3 | Daily 2 AM IST | 2h | 24h |
| S3 photos | S3 Cross-Region Replication → ap-southeast-1 | Real-time | Minutes | Minutes |
| Application code | GitHub (all branches) | Every commit | 30 min | — |
| Redis | No persistence (ephemeral) | — | Minutes (restart) | — |
| SSL certificates | Let's Encrypt auto-renew | 90 days | — | — |

---

## MONITORING STACK

| Tool | What It Monitors | Alert |
|------|-----------------|-------|
| Sentry | Application errors, slow queries | Email on new error |
| UptimeRobot | HTTP health check every 5 min | SMS on downtime |
| CloudWatch | EC2 CPU, memory, disk | Alert at >80% |
| Celery Flower | Task queue depth, failed tasks | Manual check daily |
| Let's Encrypt | Certificate expiry | Email 30 days before |

---

*AWS_ARCHITECTURE.md | iJodidar v2 | June 2026*
