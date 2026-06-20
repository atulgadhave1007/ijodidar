# iJodidar — Matrimony & Matchmaking Platform

A full-featured matrimony web application built with Flask, PostgreSQL, and AWS.  
Profile management like Google Account · Matchmaking like Shaadi.com · Real-time chat · PWA ready.

---

## Features

| Category | Features |
|----------|----------|
| **Auth** | Register, Login, Email verification, Forgot/Reset password, Phone OTP (MSG91) |
| **Profile** | 20 individually-editable sections (Google Account style), Bio, Religion/Caste, Lifestyle, Height, Photos (3 sizes via Pillow), Partner preferences, Privacy controls |
| **Matchmaking** | Send/Accept/Decline/Withdraw interest, Shortlist, Block/Report, Match score algorithm (9 factors) |
| **Messaging** | Inbox, Real-time chat (Flask-SocketIO), Typing indicator, Read receipts, Polling fallback |
| **Search** | 11 filters — keyword, gender, age, height, religion, caste, marital status, mother tongue, manglik, diet, city |
| **Membership** | Free / Silver / Gold / Platinum plans, Razorpay payment gateway, Receipt emails, Manual UPI fallback |
| **Spotlight** | ₹199/week — float to top of home feed & search, auto-expiry, ⭐ badge |
| **Refer & Earn** | Unique IJD-XXXXXX referral code, WhatsApp/Twitter share, auto-reward Silver plan |
| **Notifications** | In-app bell dropdown, 30s polling, 5 trigger types, mark-all-read |
| **Family Tree** | 10 categories, 42+ relation types (Indian family structure) |
| **Admin Panel** | Dashboard, User management, Plan CRUD, Report moderation, Success stories, Analytics charts (Chart.js) |
| **SEO & PWA** | PWA manifest + service worker, robots.txt, sitemap.xml, Open Graph tags, mobile bottom nav |
| **Trust** | Email verified badge, Phone verified badge, Manglik compatibility indicator |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.1, SQLAlchemy 2.0, Flask-Migrate |
| Real-time | Flask-SocketIO 5.3, gevent (production), threading (development) |
| Database | PostgreSQL 14+ (production), SQLite (development/local) |
| Storage | AWS S3 (profile images — 3 sizes per upload via Pillow) |
| Email | AWS SES (transactional) |
| Payments | Razorpay (UPI/cards/wallets) + manual UPI fallback |
| SMS OTP | MSG91 (dev mode: OTP logged to console) |
| Frontend | Bootstrap 5.3, Bootstrap Icons, Cropper.js, Chart.js, Socket.IO JS |
| Server | Gunicorn + gevent-websocket (Linux/EC2) |

---

## Project Structure

```
ijodidar/
├── app/
│   ├── __init__.py          # App factory, blueprints, error handlers, context processor
│   ├── models.py            # 29 DB models
│   ├── utils.py             # S3 upload (3 sizes), SES email, match score, referral, manglik
│   ├── auth/                # Login, Register (+welcome email), Email verify, Forgot/Reset, Phone OTP
│   ├── profile/             # 20 edit routes + referral dashboard
│   ├── family/              # Family tree — add/edit/delete members
│   ├── search/              # 11-filter search with block filtering
│   ├── connect/             # Interest flow, shortlist, block, report
│   ├── messaging/           # Inbox, conversation, SocketIO events
│   ├── membership/          # Plans, Razorpay checkout, spotlight
│   ├── admin/               # Dashboard, users, plans, reports, stories, analytics
│   ├── main/                # Landing page, home feed (scored), profile view, sitemap
│   └── notifications/       # Unread count, list, mark-read API endpoints
├── templates/               # 44 Jinja2 HTML templates
├── static/
│   ├── css/style.css
│   ├── js/upload_cropper.js
│   ├── js/location_cascade.js
│   ├── manifest.json        # PWA manifest
│   ├── sw.js                # Service worker
│   └── robots.txt
├── migrations/              # Flask-Migrate / Alembic migration files
├── seed.py                  # India cities, relation types, plans, admin user
├── check_migrations.py      # Schema validation utility
├── config.py                # Dev / Production configs
├── wsgi.py                  # WSGI entry point
├── Procfile                 # For Railway / EC2 with gunicorn
├── requirements.txt
├── .env.example
├── LOCAL_DEV_GUIDE.md       # Step-by-step local setup guide
└── README.md
```

---

## Quick Start (Local Development)

```bash
# 1. Clone / unzip
cd ijodidar

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env
cp .env.example .env
# Edit .env — set SECRET_KEY and ADMIN_EMAILS at minimum

# 5. Create database tables
flask db init
flask db migrate -m "initial schema"
flask db upgrade

# 6. Seed data (India cities, plans, relation types)
python seed.py

# 7. Run
python wsgi.py
# Open http://localhost:5000
```

See **LOCAL_DEV_GUIDE.md** for detailed Windows instructions, common errors, and testing tips.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Required
SECRET_KEY=your-secret-key-min-32-chars
FLASK_ENV=development                    # or 'production'
ADMIN_EMAILS=you@email.com              # comma-separated

# Database (leave blank for SQLite in dev)
DATABASE_URL=postgresql://user:pass@host:5432/ijodidar

# AWS S3 (for photo uploads — required for full functionality)
AWS_REGION=ap-south-1
AWS_S3_BUCKET=ijodidar-images

# AWS SES (for emails — leave blank for dev, emails logged to console)
MAIL_FROM=noreply@ijodidar.in

# Razorpay (leave blank for dev — manual UPI fallback used)
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...

# MSG91 SMS OTP (leave blank for dev — OTP printed to console)
MSG91_AUTH_KEY=...
MSG91_SENDER_ID=IJODDR
MSG91_TEMPLATE_ID=...

# Admin user creation via seed.py
ADMIN_EMAIL=you@email.com
ADMIN_PASSWORD=YourStrongPassword
```

---

## Database Models (29 total)

`MembershipPlan` · `UserSubscription` · `User` · `Profile` · `PartnerPreference`  
`Interest` · `Conversation` · `Message` · `Shortlist`  
`Country` · `State` · `City` · `Address`  
`Education` · `ProfessionalDetails`  
`RelationCategory` · `RelationType` · `FamilyDetails` · `FamilyRelation`  
`PhoneAlternate` · `ProfileImage` · `Language` · `ProfileView`  
`BlockList` · `UserReport` · `Notification` · `SuccessStory` · `Referral`

---

## URL Routes Reference

```
/                    Landing page (public)
/login               Login
/register            Register (supports ?ref=IJD-XXXXXX for referrals)
/verify/<token>      Email verification
/forgot-password     Forgot password
/reset-password/<t>  Reset password
/home                Home feed (match-scored, login required)
/<username>          Public profile view
/profile             Profile settings dashboard
/name, /gender, /birthday, /bio, /height, /religion, /lifestyle
/email, /phone, /address/<tag>, /professional, /education, /language
/partner_preferences, /privacy, /referral
/search              Search with 11 filters
/interests           My interests (sent/received)
/shortlist           My shortlisted profiles
/messages            Inbox
/messages/<id>       Conversation
/plans               Membership plans
/spotlight           Buy spotlight
/send-phone-otp      Send OTP
/verify-phone        Verify phone OTP
/success-stories     Public success stories
/sitemap.xml         SEO sitemap
/admin/              Admin dashboard
/admin/users         User management
/admin/reports       Content moderation
/admin/stories       Success stories
/admin/analytics     Charts and KPIs
/notifications/list  Notification API
```

---

## Production Deployment (AWS EC2 + RDS)

See **ijodidar_deployment_guide.md** for step-by-step:
1. AWS account, S3 bucket, IAM user
2. EC2 (Ubuntu 24, t3.small) + Elastic IP
3. RDS PostgreSQL (db.t3.micro)
4. Git push → EC2 pull
5. Gunicorn systemd service
6. Nginx reverse proxy
7. Cloudflare (free CDN + SSL)

**Monthly cost at 10K users: ~₹1,550/month**

---

## Membership Plans

| Plan | Price | Interests | Chat | Phone View | Validity |
|------|-------|-----------|------|------------|----------|
| Free | ₹0 | 5/month | ❌ | ❌ | Forever |
| Silver | ₹499 | 20/month | ✅ | ❌ | 30 days |
| Gold | ₹999 | 50/month | ✅ | ✅ | 90 days |
| Platinum | ₹1,999 | Unlimited | ✅ | ✅ | 180 days |
| Spotlight | ₹199 | — | — | — | 7 days (add-on) |

---

## Admin Access

1. Set `ADMIN_EMAILS=your@email.com` in `.env`
2. Register/login with that email
3. Access `/admin/` — full dashboard available

Or create admin via seed.py:
```bash
ADMIN_EMAIL=you@email.com ADMIN_PASSWORD=pass python seed.py
```

---

## License

Private / Proprietary — iJodidar © 2025. All rights reserved.
