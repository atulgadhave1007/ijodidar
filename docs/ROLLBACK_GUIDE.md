# iJodidar — Rollback Guide
## Emergency Procedures for EC2 Production

---

## QUICK REFERENCE

| Scenario | Method | Time |
|---------|--------|------|
| Bad code deploy | git revert + restart | 2 min |
| Bad migration | flask db downgrade | 5 min |
| Data corruption | restore from backup | 15 min |
| Celery issues | restart or disable | 1 min |
| Full outage | check services + restart | 5 min |

---

## SCENARIO 1 — Bad Code Deploy

```bash
ssh -i "ijodidar-key.pem" ubuntu@13.205.222.218
cd ~/ijodidar

# Check last 5 commits
git log --oneline -5

# Option A: Revert last commit (safe — creates new commit)
git revert HEAD
sudo systemctl restart ijodidar

# Option B: Hard reset (destructive — loses local changes)
git reset --hard HEAD~1
sudo systemctl restart ijodidar

# Option C: Checkout specific commit
git checkout <COMMIT_HASH> -- app/ templates/ config.py
sudo systemctl restart ijodidar
```

---

## SCENARIO 2 — Bad Migration

Migration chain for reference:
```
258790d00566  Initial — DO NOT downgrade below this
a1b2c3d4e5f6  Phase 17 security
b2c3d4e5f6a7  Phase 1 Strategic
c3d4e5f6a7b8  Phase 2 Strategic
d4e5f6a7b8c9  Phase 3 Strategic ← HEAD
```

```bash
cd ~/ijodidar
source venv/bin/activate
export FLASK_APP=wsgi.py

# Check current state
flask db current

# Downgrade one step
flask db downgrade -1

# Downgrade to specific version
flask db downgrade c3d4e5f6a7b8

# Restart after downgrade
sudo systemctl restart ijodidar
```

---

## SCENARIO 3 — Restore from Backup

```bash
# List backups
ls -lh ~/db_backups/ | tail -10

# Stop app writes
sudo systemctl stop ijodidar ijodidar-celery

# Restore specific backup
PGPASSWORD='YourDBPass' psql \
  -U ijodidar_user -h localhost ijodidar \
  < ~/db_backups/backup_YYYYMMDD_HHMM.sql

# Restart
sudo systemctl start ijodidar ijodidar-celery
```

---

## SCENARIO 4 — Celery Worker Issues

Web app continues working even if Celery is down.
Emails/SMS will queue and send when Celery restarts.

```bash
# Restart Celery
sudo systemctl restart ijodidar-celery
sudo journalctl -u ijodidar-celery -f   # watch logs

# If Celery keeps crashing
sudo systemctl stop ijodidar-celery
sudo systemctl disable ijodidar-celery
# App continues without async tasks (emails sent synchronously or fail gracefully)
```

---

## SCENARIO 5 — Full Service Outage

```bash
# Check all services
sudo systemctl status ijodidar nginx postgresql redis

# Check disk space (full disk kills everything)
df -h

# Check memory
free -h

# Restart in order
sudo systemctl restart postgresql
sleep 3
sudo systemctl restart redis
sleep 1
sudo systemctl restart ijodidar ijodidar-celery
sudo systemctl restart nginx

# Check logs
sudo journalctl -u ijodidar --since "5 minutes ago" | grep -E "ERROR|CRIT"
```

---

## PRE-DEPLOYMENT SAFETY CHECKLIST

Run this before every EC2 deployment:

```bash
# 1. Backup current DB
PGPASSWORD='pass' pg_dump \
  -U ijodidar_user -h localhost ijodidar \
  > ~/db_backups/pre_deploy_$(date +%Y%m%d_%H%M).sql
echo "Backup: OK"

# 2. Note current state
git log --oneline -1
flask db current

# 3. Deploy
git pull origin main
pip install -r requirements.txt -q
flask db upgrade
sudo systemctl restart ijodidar ijodidar-celery

# 4. Verify
sleep 3
sudo systemctl is-active ijodidar && echo "App: OK" || echo "App: FAILED"
curl -s http://localhost:5000/ | grep -c "iJodidar" > /dev/null && echo "HTTP: OK"
```
