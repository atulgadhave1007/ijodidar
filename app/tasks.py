"""
app/tasks.py — Celery async task queue

All blocking I/O (email, SMS, WhatsApp, S3) runs here.
Gunicorn eventlet workers return immediately; Celery worker handles the work.

Start worker on EC2:
    celery -A app.tasks.celery worker --loglevel=info --concurrency=2

Start Beat scheduler (separate process):
    celery -A app.tasks.celery beat --loglevel=info

Or via systemd (see DEPLOYMENT_GUIDE.md)
"""
import os
from celery import Celery
from celery.schedules import crontab


# ── Lazy Flask app (created once per worker process, not per task call) ──────
_flask_app = None

def _get_flask_app():
    global _flask_app
    if _flask_app is None:
        from app import create_app
        _flask_app = create_app(os.environ.get('FLASK_ENV', 'production'))
    return _flask_app


def make_celery():
    broker  = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    backend = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

    celery = Celery(
        'ijodidar',
        broker=broker,
        backend=backend,
        include=['app.tasks'],
    )
    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='Asia/Kolkata',
        enable_utc=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_routes={
            'app.tasks.send_email_task':      {'queue': 'email'},
            'app.tasks.send_sms_task':        {'queue': 'sms'},
            'app.tasks.send_whatsapp_task':   {'queue': 'notifications'},
            'app.tasks.upload_image_task':    {'queue': 'uploads'},
        },
        beat_schedule={
            'subscription-expiry-sweep': {
                'task':     'app.tasks.sweep_expired_subscriptions',
                'schedule': 3600.0,   # every hour
            },
            'daily-match-digest': {
                'task':     'app.tasks.send_daily_matches_all',
                'schedule': crontab(hour=2, minute=30),   # 02:30 UTC = 08:00 IST
            },
            'otp-and-token-cleanup': {
                'task':     'app.tasks.cleanup_expired_otps',
                'schedule': crontab(hour=3, minute=0),    # daily 03:00 UTC
            },
            'stale-notification-cleanup': {
                'task':     'app.tasks.cleanup_stale_notifications',
                'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Sunday 04:00 UTC
            },
            'nightly-match-score-refresh': {
                'task':     'app.tasks.refresh_match_scores',
                'schedule': crontab(hour=1, minute=0),    # daily 01:00 UTC
            },
        },
    )

    # ContextTask — provides Flask app context to every task automatically.
    # Replaces the old `from wsgi import app; with app.app_context():` pattern
    # that lived inside each task body (circular-import risk, redundant boilerplate).
    class ContextTask(celery.Task):
        abstract = True
        def __call__(self, *args, **kwargs):
            with _get_flask_app().app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()


# ─────────────────────────────────────────────────────────────────────────────
#  EMAIL TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to: str, subject: str, html_body: str):
    """Send email via AWS SES. Retries up to 3 times on failure."""
    try:
        mail_from  = os.environ.get('MAIL_FROM', '')
        aws_region = os.environ.get('AWS_REGION', '')
        if not mail_from or not aws_region:
            return {'status': 'skipped', 'reason': 'SES not configured'}
        import boto3
        ses = boto3.client('ses', region_name=aws_region)
        ses.send_email(
            Source=mail_from,
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body':    {'Html': {'Data': html_body, 'Charset': 'UTF-8'}},
            }
        )
        return {'status': 'sent', 'to': to}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_verification_email_task(self, user_id: int):
    """Send email verification link."""
    try:
        from app.models import User
        from app.utils import generate_token, send_email
        from app import db
        from datetime import datetime, timedelta
        user = User.query.get(user_id)
        if not user or user.is_verified:
            return {'status': 'skipped'}
        token = generate_token()
        user.verify_token        = token
        user.verify_token_expiry = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        verify_url = f"https://ijodidar.com/verify/{token}"
        html = f"""<div style="font-family:sans-serif;max-width:500px;margin:0 auto;">
        <h2 style="color:#dc3545;">Welcome to iJodidar, {user.first_name}!</h2>
        <p>Click the button below to verify your email address.</p>
        <a href="{verify_url}" style="background:#dc3545;color:white;
        padding:12px 28px;border-radius:25px;text-decoration:none;
        display:inline-block;margin:16px 0;">Verify Email</a>
        <p style="color:#999;font-size:12px;">
        Link expires in 24 hours. If you did not register, ignore this email.</p>
        </div>"""
        send_email(user.email, 'Verify your iJodidar account', html)
        return {'status': 'sent', 'user_id': user_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email_task(self, user_id: int):
    """Send welcome email after registration."""
    try:
        from app.models import User
        from app.utils import send_email
        user = User.query.get(user_id)
        if not user:
            return {'status': 'skipped'}
        html = f"""<div style="font-family:sans-serif;max-width:500px;margin:0 auto;">
        <h2 style="color:#dc3545;">You're all set! 🎉</h2>
        <p>Hi {user.first_name}, welcome to iJodidar!</p>
        <p>Here's how to get started:</p>
        <ol style="color:#555;line-height:1.9;">
          <li>Verify your phone (required to send interests)</li>
          <li>Complete your profile to get 5× more responses</li>
          <li>Set your partner preferences</li>
          <li>Browse matches and send interests!</li>
        </ol>
        <a href="https://ijodidar.com/home"
           style="background:#dc3545;color:white;padding:12px 28px;
           border-radius:25px;text-decoration:none;display:inline-block;margin-top:10px;">
           Find Your Match</a>
        </div>"""
        send_email(user.email, f'Welcome to iJodidar, {user.first_name}!', html)
        return {'status': 'sent', 'user_id': user_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_interest_email_task(self, receiver_id: int, sender_name: str):
    """Notify user they received an interest."""
    try:
        from app.models import User
        from app.utils import send_email
        receiver = User.query.get(receiver_id)
        if not receiver:
            return {'status': 'skipped'}
        html = (f"<h2>New Interest on iJodidar!</h2>"
                f"<p><strong>{sender_name}</strong> has sent you an interest request.</p>"
                f"<a href='https://ijodidar.com/interests' "
                f"style='background:#dc3545;color:white;padding:10px 22px;"
                f"border-radius:20px;text-decoration:none;display:inline-block;'>"
                f"View Interest</a>")
        send_email(receiver.email, f'{sender_name} sent you an interest!', html)
        return {'status': 'sent'}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_interest_accepted_email_task(self, sender_id: int, acceptor_name: str, conv_id: int):
    """Notify interest sender that their interest was accepted."""
    try:
        from app.models import User
        from app.utils import send_email
        sender = User.query.get(sender_id)
        if not sender:
            return {'status': 'skipped'}
        html = (f"<h2>Interest Accepted! 🎉</h2>"
                f"<p><strong>{acceptor_name}</strong> accepted your interest. You can now chat!</p>"
                f"<a href='https://ijodidar.com/messages/{conv_id}' "
                f"style='background:#dc3545;color:white;padding:10px 22px;"
                f"border-radius:20px;text-decoration:none;display:inline-block;'>"
                f"Start Chat</a>")
        send_email(sender.email, f'{acceptor_name} accepted your interest!', html)
        return {'status': 'sent'}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_message_email_task(self, receiver_id: int, sender_name: str,
                             body_preview: str, conv_id: int):
    """Notify user of new chat message."""
    try:
        from app.models import User
        from app.utils import send_email
        receiver = User.query.get(receiver_id)
        if not receiver:
            return {'status': 'skipped'}
        html = (f"<h2>New Message on iJodidar</h2>"
                f"<p><strong>{sender_name}</strong> sent you a message.</p>"
                f"<blockquote style='border-left:3px solid #dc3545;padding:8px 16px;"
                f"color:#555;'>{body_preview[:200]}</blockquote>"
                f"<a href='https://ijodidar.com/messages/{conv_id}' "
                f"style='background:#dc3545;color:white;padding:10px 22px;"
                f"border-radius:20px;text-decoration:none;display:inline-block;'>"
                f"Reply Now</a>")
        send_email(receiver.email, f'{sender_name} sent you a message!', html)
        return {'status': 'sent'}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email_task(self, user_id: int, reset_url: str):
    """Send password reset email."""
    try:
        from app.models import User
        from app.utils import send_email
        user = User.query.get(user_id)
        if not user:
            return {'status': 'skipped'}
        html = f"""<div style="font-family:sans-serif;max-width:500px;margin:0 auto;">
        <h2 style="color:#dc3545;">Password Reset Request</h2>
        <p>Click below to reset your password. Link expires in <strong>1 hour</strong>.</p>
        <a href="{reset_url}" style="background:#dc3545;color:white;
        padding:12px 28px;border-radius:25px;text-decoration:none;
        display:inline-block;margin:16px 0;">Reset Password</a>
        <p style="color:#999;font-size:12px;">
        If you did not request this, you can safely ignore this email.</p>
        </div>"""
        send_email(user.email, 'Reset your iJodidar password', html)
        return {'status': 'sent'}
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  SMS TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_sms_task(self, phone: str, otp: str):
    """Send OTP via Fast2SMS (primary) → MSG91 (after DLT) → console (dev)."""
    import requests as req, logging
    log = logging.getLogger(__name__)

    fast2sms_key = os.environ.get('FAST2SMS_API_KEY', '')
    msg91_key    = os.environ.get('MSG91_AUTH_KEY', '')

    try:
        if fast2sms_key:
            resp = req.get(
                "https://www.fast2sms.com/dev/bulkV2",
                params={"authorization": fast2sms_key,
                        "message": f"Your iJodidar verification code is {otp}. Valid for 10 minutes. Do not share.",
                        "route": "q",
                        "numbers": phone},
                headers={"cache-control": "no-cache"},
                timeout=10,
            )
            data = resp.json()
            if data.get('return') is True:
                return {'status': 'sent', 'provider': 'fast2sms'}
            log.error(f"Fast2SMS error: {data}")
            return {'status': 'failed', 'provider': 'fast2sms'}

        if msg91_key:
            template_id = os.environ.get('MSG91_TEMPLATE_ID', '')
            resp = req.post(
                "https://api.msg91.com/api/v5/otp",
                json={"template_id": template_id,
                      "mobile": f"91{phone}",
                      "authkey": msg91_key,
                      "otp": otp},
                timeout=10,
            )
            return {'status': 'sent' if resp.status_code == 200 else 'failed',
                    'provider': 'msg91'}

        log.info(f'[DEV OTP] Phone:{phone} OTP:{otp}')
        return {'status': 'dev_logged', 'otp': otp}

    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  WHATSAPP TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=2, default_retry_delay=60)
def send_whatsapp_task(self, phone: str, template: str, params: list):
    """Send WhatsApp Business API message."""
    try:
        from app.utils import send_whatsapp
        send_whatsapp(phone, template, params)
        return {'status': 'sent'}
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  CELERY BEAT — SCHEDULED TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery.task
def sweep_expired_subscriptions():
    """Mark paid subscriptions as inactive when their expiry has passed.
    Runs hourly. Without this, expired users keep paid features indefinitely."""
    from datetime import datetime
    from app.models import UserSubscription
    from app import db
    now     = datetime.utcnow()
    expired = (UserSubscription.query
               .filter(UserSubscription.is_active == True,
                       UserSubscription.expires_at != None,
                       UserSubscription.expires_at < now)
               .all())
    count = 0
    for sub in expired:
        sub.is_active = False
        count += 1
    if count:
        db.session.commit()
    return {'expired_count': count}


@celery.task
def send_daily_matches_all():
    """Fan-out daily match digest to all active users with complete profiles.
    Runs daily at 02:30 UTC (08:00 IST). Each user gets their own sub-task."""
    from datetime import datetime, timedelta
    from app.models import User, Profile
    cutoff = datetime.utcnow() - timedelta(days=90)
    users = (User.query
             .join(Profile)
             .filter(
                 User.is_active_acc == True,
                 User.is_hidden     == False,
                 User.is_staff      == False,
                 Profile.gender     != None,
                 Profile.looking_for != None,
             )
             .filter(
                 (User.last_active_at == None) | (User.last_active_at > cutoff)
             )
             .with_entities(User.id)
             .all())
    count = 0
    for (uid,) in users:
        send_daily_match_digest.delay(uid)
        count += 1
    return {'queued': count}


@celery.task(bind=True, max_retries=2, default_retry_delay=120)
def send_daily_match_digest(self, user_id: int):
    """Send one user their top-3 new daily matches by email."""
    try:
        from app.models import User, Profile, Interest
        from app.utils import send_email
        user = User.query.get(user_id)
        if not user or not user.email:
            return {'status': 'skipped'}
        p = user.profile
        if not p or not p.gender or not p.looking_for:
            return {'status': 'skipped', 'reason': 'incomplete profile'}

        # Find up to 3 matches not yet interacted with
        sent_ids     = {i.receiver_id for i in user.interests_sent}
        received_ids = {i.sender_id   for i in user.interests_received}
        exclude      = sent_ids | received_ids | {user.id}

        candidates = (User.query
                      .join(Profile)
                      .filter(
                          User.is_active_acc  == True,
                          User.is_hidden      == False,
                          User.is_staff       == False,
                          Profile.gender      == p.looking_for,
                          Profile.looking_for == p.gender,
                          User.id.notin_(exclude),
                      )
                      .limit(3).all())

        if not candidates:
            return {'status': 'no_matches'}

        rows = ''.join(
            f"<tr><td style='padding:8px'>{c.first_name} {c.last_name[0]}.</td>"
            f"<td style='padding:8px'>"
            f"<a href='https://ijodidar.com/profile/{c.id}' style='color:#dc3545'>View</a>"
            f"</td></tr>"
            for c in candidates
        )
        html = f"""<div style="font-family:sans-serif;max-width:500px;margin:0 auto;">
        <h2 style="color:#dc3545;">Today's Matches, {user.first_name}!</h2>
        <p>Here are new profiles you might like:</p>
        <table style="width:100%;border-collapse:collapse">{rows}</table>
        <a href="https://ijodidar.com/home"
           style="background:#dc3545;color:white;padding:12px 28px;
           border-radius:25px;text-decoration:none;display:inline-block;margin-top:16px;">
           See All Matches</a>
        <p style="color:#999;font-size:11px;margin-top:16px;">
        <a href="https://ijodidar.com/profile/settings" style="color:#999">
        Unsubscribe from daily digest</a></p>
        </div>"""
        send_email(user.email, f'Your daily matches on iJodidar, {user.first_name}!', html)
        return {'status': 'sent', 'user_id': user_id, 'matches': len(candidates)}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery.task
def cleanup_expired_otps():
    """Clear expired OTPs, reset tokens, and verify tokens. Runs daily."""
    from datetime import datetime
    from app.models import User
    from app import db
    now   = datetime.utcnow()
    count = 0
    users = User.query.filter(
        (User.phone_otp_expiry  < now) |
        (User.reset_token_expiry < now) |
        (User.verify_token_expiry < now)
    ).all()
    for u in users:
        if u.phone_otp_expiry and u.phone_otp_expiry < now:
            u.phone_otp        = None
            u.phone_otp_expiry = None
            count += 1
        if u.reset_token_expiry and u.reset_token_expiry < now:
            u.reset_token        = None
            u.reset_token_expiry = None
            count += 1
        if u.verify_token_expiry and u.verify_token_expiry < now and not u.is_verified:
            u.verify_token        = None
            u.verify_token_expiry = None
            count += 1
    if count:
        db.session.commit()
    return {'cleaned': count}


@celery.task
def cleanup_stale_notifications():
    """Delete read notifications older than 90 days. Runs weekly."""
    from datetime import datetime, timedelta
    from app.models import Notification
    from app import db
    cutoff = datetime.utcnow() - timedelta(days=90)
    deleted = (Notification.query
               .filter(Notification.is_read == True,
                       Notification.created_at < cutoff)
               .delete())
    db.session.commit()
    return {'deleted': deleted}


@celery.task
def refresh_match_scores():
    """Placeholder: log active user count for monitoring. Nightly.
    Sprint 4 will replace this with MatchScoreCache pre-computation."""
    from app.models import User
    count = User.query.filter_by(is_active_acc=True, is_hidden=False, is_staff=False).count()
    return {'active_users': count, 'note': 'match score cache not yet implemented'}
