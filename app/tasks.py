"""
app/tasks.py — Celery async task queue

All blocking I/O (email, SMS, WhatsApp, S3) runs here.
Gunicorn gevent workers return immediately; Celery worker handles the work.

Start worker on EC2:
    celery -A app.tasks.celery worker --loglevel=info --concurrency=2 &

Or via systemd (see DEPLOYMENT_GUIDE.md)
"""
from celery import Celery


def make_celery(app=None):
    """Create Celery instance. Accepts optional Flask app for context."""
    import os
    broker = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
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
        task_acks_late=True,           # re-queue on worker crash
        worker_prefetch_multiplier=1,  # fair distribution
        task_routes={
            'app.tasks.send_email_task':      {'queue': 'email'},
            'app.tasks.send_sms_task':        {'queue': 'sms'},
            'app.tasks.send_whatsapp_task':   {'queue': 'notifications'},
            'app.tasks.upload_image_task':    {'queue': 'uploads'},
        },
    )
    if app:
        celery.conf.update(app.config)
        TaskBase = celery.Task
        class ContextTask(TaskBase):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
        celery.Task = ContextTask
    return celery


# Standalone celery instance (used by worker process)
celery = make_celery()


# ─────────────────────────────────────────────────────────────────────────────
#  EMAIL TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to: str, subject: str, html_body: str):
    """Send email via AWS SES. Retries up to 3 times on failure."""
    import os
    import boto3
    try:
        mail_from  = os.environ.get('MAIL_FROM', '')
        aws_region = os.environ.get('AWS_REGION', '')
        if not mail_from or not aws_region:
            return {'status': 'skipped', 'reason': 'SES not configured'}
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
    """Send email verification link. Fetches fresh user data inside task."""
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
            from app.models import User
            from app.utils import generate_token, send_email
            from app import db
            from datetime import datetime, timedelta
            user = User.query.get(user_id)
            if not user or user.is_verified:
                return {'status': 'skipped'}
            # Generate fresh token
            token = generate_token()
            user.verify_token        = token
            user.verify_token_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            from flask import url_for
            with app.test_request_context():
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
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
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
              <li>Verify your email (check the other email we sent)</li>
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
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
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
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
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
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
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
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
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
    """Send OTP via MSG91. Retries on failure."""
    import os, requests as req
    try:
        key         = os.environ.get('MSG91_AUTH_KEY', '')
        template_id = os.environ.get('MSG91_TEMPLATE_ID', '')
        if not key:
            import logging
            logging.getLogger(__name__).info(f'[DEV OTP] Phone:{phone} OTP:{otp}')
            return {'status': 'dev_logged', 'otp': otp}
        resp = req.post(
            "https://api.msg91.com/api/v5/otp",
            json={"template_id": template_id,
                  "mobile": f"91{phone}",
                  "authkey": key,
                  "otp": otp},
            timeout=10,
        )
        return {'status': 'sent' if resp.status_code == 200 else 'failed',
                'code': resp.status_code}
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
#  WHATSAPP TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=2, default_retry_delay=60)
def send_whatsapp_task(self, phone: str, template: str, params: list):
    """Send WhatsApp Business API message. Non-critical — only 2 retries."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from wsgi import app
        with app.app_context():
            from app.utils import send_whatsapp
            send_whatsapp(phone, template, params)
            return {'status': 'sent'}
    except Exception as exc:
        raise self.retry(exc=exc)
