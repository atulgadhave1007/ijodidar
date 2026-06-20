# iJodidar — Deployment Guide
## Local Testing → EC2 Production

---

## PART 1 — LOCAL TESTING (Windows / Mac / Linux)

### Prerequisites
- Python 3.11 or 3.12
- Git

PostgreSQL and Redis are **NOT required** for local testing:
- SQLite is used automatically (no setup needed)
- Rate limiting uses in-memory fallback
- Emails log to console instead of sending

---

### Step 1 — Clone
```bash
git clone https://github.com/atulgadhave1007/ijodidar.git
cd ijodidar
```

### Step 2 — Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

If you get gevent errors on Windows:
```bash
pip install -r requirements-windows.txt
```

### Step 4 — Environment File
```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and set at minimum:
```
SECRET_KEY=any-random-string-for-local-dev-only
FLASK_ENV=development
```

Leave everything else blank for local testing.

### Step 5 — Database Setup
```bash
# Windows
set FLASK_APP=wsgi.py

# Mac / Linux
export FLASK_APP=wsgi.py

flask db upgrade
python seed.py
```

You should see:
```
✓ Membership plans seeded (4)
✓ Countries seeded (195)
✓ States seeded (35)
✓ Cities seeded (300+)
✓ Relation types seeded (42)
✓ Console admin created: atulgadhave58@gmail.com
All seed data inserted successfully.
```

### Step 6 — Run
```bash
python wsgi.py
```

```
  iJodidar starting in [development] mode
  Open http://localhost:5000
```

---

## PART 2 — WHAT WORKS LOCALLY (WITHOUT AWS)

| Feature | Works Locally? | Notes |
|---------|---------------|-------|
| Registration | ✅ | Email verify link logged to console |
| Login | ✅ | |
| Profile editing | ✅ | All 22 pages |
| Photo upload | ⚠️ Skipped | "S3 not configured" message shown |
| Home feed | ✅ | |
| Kundli auto-calc | ✅ | Pure Python, no external calls |
| Guna Milan | ✅ | |
| Interest send/accept | ✅ | |
| Real-time chat | ✅ | SocketIO works in dev |
| Search | ✅ | |
| Membership plans | ✅ | Razorpay modal (needs test keys) |
| Console | ✅ | No IP restriction in dev |
| OTP verification | ⚠️ | OTP logged to console, not sent |
| Referral | ✅ | |

---

## PART 3 — LOCAL TEST CREDENTIALS

After `python seed.py`:

**Console Login:**
- URL: http://localhost:5000/console/login
- Email: atulgadhave58@gmail.com  (or value of CONSOLE_CEO_EMAIL in .env)
- Password: set via CONSOLE_CEO_PASSWORD in .env, or default from seed.py

**Regular User:**
Register at http://localhost:5000/register then:
```bash
# Manually verify email (since SES not configured locally)
python3 -c "
from wsgi import app
with app.app_context():
    from app.models import User; from app import db
    u = User.query.filter_by(email='your@email.com').first()
    u.is_verified = True; db.session.commit(); print('Verified')
"
```

---

## PART 4 — EC2 PRODUCTION DEPLOYMENT

### SSH Access
```bash
ssh -i "C:\Users\Admin\Downloads\ijodidar-key.pem" ubuntu@13.205.222.218
```

### Deploy Code
```bash
cd ~/ijodidar
git pull origin main
source venv/bin/activate
pip install -r requirements.txt -q
export FLASK_APP=wsgi.py
flask db upgrade
sudo systemctl restart ijodidar ijodidar-celery
sudo systemctl status ijodidar
```

### Install Celery Worker (first time)
```bash
sudo cp celery.service /etc/systemd/system/ijodidar-celery.service
sudo systemctl daemon-reload
sudo systemctl enable ijodidar-celery
sudo systemctl start ijodidar-celery
sudo systemctl status ijodidar-celery
```

### .env on EC2 (complete reference)
```bash
nano ~/ijodidar/.env
```

```
# Core
SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=production

# Database
DATABASE_URL=postgresql://ijodidar_user:YOUR_DB_PASSWORD@localhost:5432/ijodidar

# AWS (set after SES + S3 configured)
AWS_REGION=ap-south-1
MAIL_FROM=noreply@ijodidar.com
AWS_S3_BUCKET=ijodidar-images

# Redis (required for production rate limiting)
REDIS_URL=redis://localhost:6379/0

# Razorpay (test keys until GST + live KYC done)
RAZORPAY_KEY_ID=rzp_test_XXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXX
RAZORPAY_WEBHOOK_SECRET=

# SMS (set after MSG91 DLT approved)
MSG91_AUTH_KEY=
MSG91_SENDER_ID=IJODDR
MSG91_TEMPLATE_ID=

# Monitoring
SENTRY_DSN=

# Console access
CONSOLE_ALLOWED_IPS=your.home.ip.address
CONSOLE_CEO_EMAIL=atulgadhave58@gmail.com
CONSOLE_CEO_PASSWORD=YourSecurePassword123!

# Admin
ADMIN_EMAIL=atulgadhave1007@gmail.com
ADMIN_EMAILS=atulgadhave58@gmail.com,atulgadhave1007@gmail.com
```

---

## PART 5 — AWS SES SETUP (Email)

```
1. AWS Console → SES → Verified Identities → Create Identity → Domain → ijodidar.com
2. Route 53 auto-adds DKIM/DMARC DNS records (5 min to verify)
3. SES → Account Dashboard → Request Production Access
   Fill in:
     Mail type: Transactional
     Website URL: https://ijodidar.com
     Description: "Matrimony platform. Transactional only: registration
                   verification, password reset, interest notifications,
                   payment receipts. No bulk marketing. ~500/day max."
4. Wait 24-48 hours for approval
5. After approval:
   nano ~/ijodidar/.env
   → AWS_REGION=ap-south-1
   → MAIL_FROM=noreply@ijodidar.com
   sudo systemctl restart ijodidar

6. Test:
   python3 -c "
   from wsgi import app
   with app.app_context():
       from app.utils import send_email
       print(send_email('your@email.com', 'Test', '<h2>SES Working!</h2>'))
   "
```

---

## PART 6 — S3 PHOTO STORAGE SETUP

```
1. AWS Console → S3 → Create bucket
   Name: ijodidar-images
   Region: ap-south-1
   → Uncheck "Block all public access"

2. IAM → Roles → Create Role
   Trusted entity: EC2
   Policies: AmazonS3FullAccess + AmazonSESFullAccess
   Role name: ijodidar-ec2-role

3. EC2 Console → Select your instance
   → Actions → Security → Modify IAM Role
   → Select: ijodidar-ec2-role → Update

4. Test upload:
   python3 -c "
   import boto3
   s3 = boto3.client('s3', region_name='ap-south-1')
   s3.put_object(Bucket='ijodidar-images', Key='test.txt', Body=b'ok')
   print('S3 working!')
   "

5. Make existing photos private (one-time, run after S3 setup):
   python3 << 'EOF'
   from wsgi import app
   with app.app_context():
       import boto3
       from app.models import ProfileImage
       from flask import current_app
       bucket = current_app.config.get('AWS_S3_BUCKET', '')
       region = current_app.config.get('AWS_REGION', '')
       if bucket and region:
           s3 = boto3.client('s3', region_name=region)
           for img in ProfileImage.query.all():
               try:
                   key = img.image_url.split('.amazonaws.com/')[-1]
                   s3.put_object_acl(Bucket=bucket, Key=key, ACL='private')
               except Exception as e:
                   print(f'Skip: {e}')
           print('Done')
   EOF
```

---

## PART 7 — GITHUB ACTIONS AUTO-DEPLOY (Optional)

```bash
# On EC2: create deploy key
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy  # copy this for GitHub secret
```

On GitHub → Settings → Secrets → Actions → Add:
- `EC2_HOST` = 13.205.222.218
- `EC2_USER` = ubuntu
- `EC2_SSH_KEY` = (paste private key)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to EC2
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/ijodidar
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt -q
            export FLASK_APP=wsgi.py
            flask db upgrade
            sudo systemctl restart ijodidar ijodidar-celery
            echo "Deployed: $(date)"
```

---

## QUICK DIAGNOSTIC COMMANDS

```bash
# Check all services
sudo systemctl status ijodidar ijodidar-celery nginx postgresql redis

# Live app logs
sudo journalctl -u ijodidar -f

# Live Celery task logs
sudo journalctl -u ijodidar-celery -f

# Update console IPs
curl http://checkip.amazonaws.com   # get your current IP
nano ~/ijodidar/.env                # update CONSOLE_ALLOWED_IPS
sudo systemctl restart ijodidar

# DB health check
psql -U ijodidar_user -d ijodidar -h localhost -c "
SELECT tablename, n_live_tup as rows
FROM pg_stat_user_tables
ORDER BY rows DESC LIMIT 10;"

# Manual backup
PGPASSWORD='pass' pg_dump -U ijodidar_user -h localhost ijodidar \
  > ~/db_backups/backup_$(date +%Y%m%d_%H%M).sql
```
