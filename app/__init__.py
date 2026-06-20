from flask import Flask, render_template, request, current_app

# Sentry error monitoring — initialised before app creation
# Set SENTRY_DSN in .env: get DSN from sentry.io → Projects → iJodidar → DSN
import os as _sentry_os
_sentry_dsn = _sentry_os.environ.get('SENTRY_DSN', '')
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[
            FlaskIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,   # 10% of requests traced (adjust as needed)
        send_default_pii=False,   # never send PII to Sentry
        environment=_sentry_os.environ.get('FLASK_ENV', 'development'),
    )
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db         = SQLAlchemy()
migrate    = Migrate()
login_mgr  = LoginManager()
csrf       = CSRFProtect()
limiter    = Limiter(key_func=get_remote_address)
# async_mode: 'threading' works everywhere (dev+Windows), 'gevent' for production
# Resolved at runtime based on installed packages
import os as _os
_async_mode = 'eventlet' if _os.environ.get('FLASK_ENV') == 'production' else 'threading'
socketio   = SocketIO(cors_allowed_origins="*", async_mode=_async_mode)

login_mgr.login_view             = 'auth.login'
login_mgr.login_message          = 'Please log in to access this page.'
login_mgr.login_message_category = 'info'


def create_app(env='default'):
    from config import config
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[env])

    # Refuse to start in production with the default insecure secret key
    if env == 'production':
        sk = app.config.get('SECRET_KEY', '')
        if not sk or sk == 'change-me-in-production' or len(sk) < 32:
            raise RuntimeError(
                'FATAL: SECRET_KEY is missing or insecure. '
                'Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))" '
                'and set it in your .env file.'
            )

    db.init_app(app)
    migrate.init_app(app, db)
    login_mgr.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────────
    from app.auth.routes          import auth_bp
    from app.profile.routes       import profile_bp
    from app.family.routes        import family_bp
    from app.search.routes        import search_bp
    from app.main.routes          import main_bp
    from app.connect.routes       import connect_bp
    from app.messaging.routes     import messaging_bp
    from app.membership.routes    import membership_bp
    from app.notifications.routes import notifications_bp
    from app.kundli.routes         import kundli_bp
    from app.console.routes        import console_bp
    from app.onboarding.routes     import onboarding_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(connect_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(membership_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(kundli_bp)
    app.register_blueprint(console_bp)
    app.register_blueprint(onboarding_bp)

    # ── Onboarding gate ──────────────────────────────────────────────────────
    # Force new users to set gender + looking_for before accessing home feed
    ONBOARDING_EXEMPT = {
        'auth.login', 'auth.register', 'auth.logout',
        'auth.verify_email', 'auth.forgot_password', 'auth.reset_password',
        'auth.send_phone_otp', 'auth.verify_phone',
        'onboarding.set_gender', 'onboarding.basics', 'onboarding.career',
        'onboarding.photo', 'onboarding.preferences', 'onboarding.done',
        'main.landing', 'main.privacy_policy', 'main.terms',
        'static',
    }

    @app.before_request
    def update_last_active():
        """Update last_active_at at most once per hour to avoid per-request DB writes."""
        from flask_login import current_user
        from flask import session
        if not current_user.is_authenticated:
            return
        from datetime import datetime
        now      = datetime.utcnow()
        last_str = session.get('_last_active_written')
        if last_str:
            try:
                last_dt = datetime.fromisoformat(last_str)
                if (now - last_dt).total_seconds() < 3600:
                    return
            except (ValueError, TypeError):
                pass
        current_user.last_active_at = now
        db.session.commit()
        session['_last_active_written'] = now.isoformat()

    @app.before_request
    def enforce_phone_verification():
        """Require phone OTP before accessing the platform (C1 — phone-first registration)."""
        from flask_login import current_user
        from flask import request as req, redirect, url_for
        if not current_user.is_authenticated:
            return
        if req.endpoint in ONBOARDING_EXEMPT or not req.endpoint:
            return
        if req.endpoint.startswith('console.'):
            return
        if not current_user.phone_verified:
            return redirect(url_for('auth.verify_phone'))

    @app.before_request
    def validate_session_version():
        """Invalidate sessions when user changes password."""
        from flask_login import current_user
        from flask import session, redirect, url_for, request as req
        if not current_user.is_authenticated:
            return
        # Check stored version matches model version
        stored  = session.get('_session_version')
        current = current_user.session_version or 1
        if stored is None:
            session['_session_version'] = current
        elif stored != current:
            # Password was changed — force re-login
            from flask_login import logout_user
            logout_user()
            session.clear()
            return redirect(url_for('auth.login') + '?reason=session_expired')

    @app.before_request
    def enforce_onboarding():
        from flask_login import current_user
        from flask import request as req, redirect, url_for
        if not current_user.is_authenticated:
            return
        if req.endpoint in ONBOARDING_EXEMPT or not req.endpoint:
            return
        if req.endpoint and req.endpoint.startswith('console.'):
            return
        # Skip if profile already has gender + looking_for
        p = current_user.profile
        if not p or not p.gender or not p.looking_for:
            return redirect(url_for('onboarding.set_gender'))

    # ── Context processor ─────────────────────────────────────────────
    from datetime import datetime, date

    # Console-specific context processor (pending badge counts in sidebar)
    @app.context_processor
    def inject_console_context():
        from flask import request as req
        if req.blueprint == 'console':
            from app.models import UserReport, AssistedRequest
            return dict(
                pending_reports_count  = UserReport.query.filter_by(status='pending').count(),
                assisted_pending_count = AssistedRequest.query.filter_by(status='pending').count(),
                now                    = __import__('datetime').datetime.utcnow(),
            )
        return {}

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models import Interest, Message, Conversation, Notification
        unread_messages   = 0
        pending_interests = 0
        unread_notifs     = 0
        if current_user.is_authenticated:
            unread_messages = (Message.query
                               .join(Conversation)
                               .filter(
                                   Message.sender_id != current_user.id,
                                   Message.is_read   == False,
                                   ((Conversation.user1_id == current_user.id) |
                                    (Conversation.user2_id == current_user.id))
                               ).count())
            pending_interests = (Interest.query
                                 .filter_by(receiver_id=current_user.id, status='pending')
                                 .count())
            unread_notifs = (Notification.query
                             .filter_by(user_id=current_user.id, is_read=False)
                             .count())
        return dict(
            datetime=datetime, date=date,
            unread_messages=unread_messages,
            pending_interests=pending_interests,
            unread_notifs=unread_notifs,
        )

    @app.template_filter('signed_url')
    def signed_url_filter(image_url, expiry=3600):
        """Template filter: {{ img.image_url | signed_url }} — returns pre-signed S3 URL."""
        if not image_url:
            return ''
        try:
            from app.utils import get_signed_image_url
            return get_signed_image_url(image_url, expiry)
        except Exception:
            return image_url

    @app.template_filter('from_json')
    def from_json_filter(s):
        import json
        try:
            return json.loads(s) if s else []
        except Exception:
            return []

    @app.template_filter('age')
    def age_filter(dob_input):
        """Accept date object, date string, or None. Returns age integer."""
        if not dob_input:
            return None
        try:
            if isinstance(dob_input, date):
                dob = dob_input
            else:
                for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
                    try:
                        dob = datetime.strptime(str(dob_input), fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return None
            today = date.today()
            return today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day))
        except Exception:
            return None

    # ── SocketIO events ───────────────────────────────────────────────
    from app.messaging.socket_events import register_socket_events
    register_socket_events(socketio)


    # ── Error handlers ───────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 error: {e}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html'), 429


    # ── Language support (Phase 13.2) ────────────────────────────────────
    @app.route('/set-language/<lang>')
    def set_language(lang):
        from flask import session, redirect, request as req
        if lang in ('en', 'mr'):
            session['ui_language'] = lang
        return redirect(req.referrer or '/')

    @app.context_processor
    def inject_language():
        from flask import session
        from flask_login import current_user
        lang = 'en'
        if current_user.is_authenticated and current_user.profile:
            lang = current_user.profile.ui_language or 'en'
        lang = session.get('ui_language', lang)
        return dict(ui_lang=lang)

    # ── Simple translation helper (no Babel dependency) ───────────────────
    # Load Marathi translations from translations/mr/messages.py
    try:
        import sys, os as _os
        _trans_path = _os.path.join(_os.path.dirname(__file__), '..', 'translations', 'mr')
        if _trans_path not in sys.path:
            sys.path.insert(0, _os.path.abspath(_trans_path))
        from messages import MARATHI as _MR_DICT
        TRANSLATIONS = {'mr': _MR_DICT}
    except ImportError:
        TRANSLATIONS = {'mr': {}}   # fallback

    @app.template_filter('t')
    def translate_filter(text):
        from flask import session
        from flask_login import current_user
        lang = session.get('ui_language', 'en')
        try:
            if current_user.is_authenticated and current_user.profile:
                lang = current_user.profile.ui_language or lang
        except Exception:
            pass
        if lang == 'en':
            return text
        return TRANSLATIONS.get(lang, {}).get(str(text), text)

    return app
