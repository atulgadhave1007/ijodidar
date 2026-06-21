import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-me-in-production'
    WTF_CSRF_ENABLED = True

    _db = os.environ.get('DATABASE_URL', '')
    if _db.startswith('postgres://'):
        _db = _db.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = (
        _db or f"sqlite:///{os.path.join(basedir, 'instance', 'dev.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10, 'max_overflow': 20,
        'pool_pre_ping': True, 'pool_recycle': 1800,
    }

    # AWS — leave empty until SES + S3 are configured
    # When MAIL_FROM or AWS_REGION is empty, send_email() returns False immediately
    # When AWS_S3_BUCKET or AWS_REGION is empty, upload_image_to_s3() returns error immediately
    AWS_REGION    = os.environ.get('AWS_REGION', '')          # set to ap-south-1 in .env after SES approved
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET', 'ijodidar-images')
    MAIL_FROM     = os.environ.get('MAIL_FROM', '')            # set to noreply@ijodidar.com in .env after SES approved

    # Razorpay
    RAZORPAY_KEY_ID        = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET    = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')  # set in Razorpay dashboard

    # SMS — Fast2SMS (interim, no DLT needed)
    FAST2SMS_API_KEY = os.environ.get('FAST2SMS_API_KEY', '')

    # SMS — MSG91 (production, after DLT approval)
    MSG91_AUTH_KEY    = os.environ.get('MSG91_AUTH_KEY', '')
    MSG91_SENDER_ID   = os.environ.get('MSG91_SENDER_ID', 'IJODDR')
    MSG91_TEMPLATE_ID = os.environ.get('MSG91_TEMPLATE_ID', '')

    # Admin
    ADMIN_EMAILS = [
        e.strip() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()
    ]

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024    # 5 MB (Pillow will resize down)
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    # ── Monitoring (Sentry) ─────────────────────────────────────────────────
    SENTRY_DSN = os.environ.get('SENTRY_DSN', '')   # Get from sentry.io → New Project → Python/Flask

    # ── Celery (async task queue — email, SMS, WhatsApp, S3 uploads) ────────
    # Worker: celery -A app.tasks.celery worker --loglevel=info --concurrency=2
    CELERY_BROKER_URL     = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

    # Rate limiting storage — use Redis in production for reliability across workers
    # In-memory = each Gunicorn worker has separate counter (3× effective limit)
    # Redis = shared counter across all workers — correct behaviour
    # Install: sudo apt install redis-server -y && sudo systemctl enable redis
    # .env: REDIS_URL=redis://localhost:6379/0
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')

    # JWT (REST API — Flask-JWT-Extended)
    JWT_SECRET_KEY             = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY') or 'change-me'
    JWT_ACCESS_TOKEN_EXPIRES   = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES  = timedelta(days=30)
    JWT_ALGORITHM              = 'HS256'
    JWT_TOKEN_LOCATION         = ['headers']
    JWT_HEADER_NAME            = 'Authorization'
    JWT_HEADER_TYPE            = 'Bearer'
    # Blocklist: Redis DB4 — populated on logout / password change
    JWT_REDIS_BLOCKLIST_URL    = os.environ.get('REDIS_URL', 'redis://localhost:6379/4')
    # App-layer cache: Redis DB2 — badge counts (60s TTL), match scores (1hr TTL)
    CACHE_REDIS_URL            = os.environ.get('REDIS_URL', 'redis://localhost:6379/2')

    # Aadhaar / KYC Verification (Phase 14.2)
    KYC_API_KEY      = os.environ.get('KYC_API_KEY', '')   # Surepass/Signzy/Karza
    KYC_PROVIDER     = os.environ.get('KYC_PROVIDER', 'surepass')

    # WhatsApp Business API (Phase 14.3)
    WHATSAPP_TOKEN           = os.environ.get('WHATSAPP_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}      # no pooling for SQLite


class ProductionConfig(Config):
    DEBUG = False
    # Security hardening for production (behind Nginx HTTPS)
    SESSION_COOKIE_SECURE   = True       # Only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY = True       # JS cannot read session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection
    REMEMBER_COOKIE_SECURE  = True       # Secure remember-me cookie
    PERMANENT_SESSION_LIFETIME = 86400   # 24-hour session lifetime
    PREFERRED_URL_SCHEME    = 'https'    # url_for() generates https:// links


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
