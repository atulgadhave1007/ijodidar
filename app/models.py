from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_mgr


@login_mgr.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────────
#  MEMBERSHIP PLAN
# ─────────────────────────────────────────────
class MembershipPlan(db.Model):
    __tablename__ = 'membership_plans'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), nullable=False, unique=True)   # Free, Silver, Gold, Platinum
    price_inr   = db.Column(db.Integer, nullable=False, default=0)
    duration_days = db.Column(db.Integer, nullable=False, default=0)      # 0 = forever (Free)
    max_interests   = db.Column(db.Integer, default=5)    # interests you can send per month
    can_message     = db.Column(db.Boolean, default=False)
    can_view_phone  = db.Column(db.Boolean, default=False)
    can_view_full_profile = db.Column(db.Boolean, default=True)
    highlighted     = db.Column(db.Boolean, default=False)  # show as recommended plan
    description     = db.Column(db.Text)

    subscriptions = db.relationship('UserSubscription', backref='plan', lazy='dynamic')


class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id     = db.Column(db.Integer, db.ForeignKey('membership_plans.id'), nullable=False)
    started_at  = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at  = db.Column(db.DateTime, nullable=True)   # None = no expiry (Free)
    is_active   = db.Column(db.Boolean, default=True)
    payment_ref = db.Column(db.String(100))               # Razorpay / UPI ref
    amount_paid = db.Column(db.Integer, default=0)        # in paise
    # Monthly interest tracking (Phase 17)
    interests_this_month = db.Column(db.Integer, default=0)
    interests_reset_at   = db.Column(db.DateTime, default=datetime.utcnow)
    # Manual payment tracking (Phase 17)
    # payment_ref 'PENDING:xxx' = awaiting admin verification

    def interests_remaining(self):
        """Return interests left this month. Auto-resets monthly."""
        from datetime import timedelta
        now = datetime.utcnow()
        reset = self.interests_reset_at or now
        if (now - reset).days >= 30:
            self.interests_this_month = 0
            self.interests_reset_at   = now
            # Caller must commit — properties/methods must not issue their own commits
        limit = self.plan.max_interests if self.plan else 5
        if limit <= 0:
            return 999   # unlimited
        return max(0, limit - self.interests_this_month)


# ─────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), index=True, unique=True, nullable=False)
    first_name    = db.Column(db.String(50), nullable=False)
    last_name     = db.Column(db.String(50), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    phone         = db.Column(db.String(15))
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified   = db.Column(db.Boolean, default=False)   # email verified
    verify_token  = db.Column(db.String(100), nullable=True)
    reset_token   = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    is_active_acc = db.Column(db.Boolean, default=True)
    is_hidden      = db.Column(db.Boolean, default=False)   # hide from search
    is_staff       = db.Column(db.Boolean, default=False, index=True)  # exclude from all user feeds/stats
    phone_verified = db.Column(db.Boolean, default=False)   # SMS OTP verified
    phone_otp        = db.Column(db.String(255), nullable=True)  # hashed — was String(6)
    phone_otp_expiry = db.Column(db.DateTime,    nullable=True)
    # Email verification expiry (added Phase 17)
    verify_token_expiry = db.Column(db.DateTime, nullable=True)
    # Account lockout (added Phase 17)
    failed_login_count  = db.Column(db.Integer, default=0)
    locked_until        = db.Column(db.DateTime, nullable=True)
    # Consent (added Phase 17)
    consented_at        = db.Column(db.DateTime, nullable=True)
    session_version     = db.Column(db.Integer, default=1, nullable=False)  # increment on password change
    last_active_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile              = db.relationship('Profile',             backref='user', uselist=False, cascade='all, delete-orphan')
    addresses            = db.relationship('Address',             backref='user', cascade='all, delete-orphan')
    educations           = db.relationship('Education',           backref='user', cascade='all, delete-orphan')
    professional_details = db.relationship('ProfessionalDetails', backref='user', cascade='all, delete-orphan')
    family_details       = db.relationship('FamilyDetails',       backref='user', cascade='all, delete-orphan')
    phone_alternates     = db.relationship('PhoneAlternate',      backref='user', cascade='all, delete-orphan')
    profile_images       = db.relationship('ProfileImage',        backref='user', cascade='all, delete-orphan',
                                           order_by='ProfileImage.is_primary.desc()')
    languages            = db.relationship('Language',            backref='user', cascade='all, delete-orphan')
    subscriptions        = db.relationship('UserSubscription',    backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash  = generate_password_hash(password)
        self.session_version = (self.session_version or 1) + 1  # invalidate all sessions

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def active_subscription(self):
        now = datetime.utcnow()
        return (UserSubscription.query
                .filter_by(user_id=self.id, is_active=True)
                .filter((UserSubscription.expires_at == None) | (UserSubscription.expires_at > now))
                .order_by(UserSubscription.started_at.desc())
                .first())

    @property
    def plan_name(self):
        sub = self.active_subscription
        return sub.plan.name if sub else 'Free'

    @property
    def plan_can_view_photos(self):
        """Silver+ users can see unblurred photos of other users."""
        return self.plan_name != 'Free'

    def can_send_interest(self):
        sub = self.active_subscription
        if not sub:
            return True   # Free plan — limited by max_interests
        return sub.plan.max_interests > 0

    def __repr__(self):
        return f'<User {self.username}>'


# ─────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────
class Profile(db.Model):
    __tablename__ = 'profiles'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    gender          = db.Column(db.String(10), index=True)
    looking_for     = db.Column(db.String(10), index=True)
    date_of_birth   = db.Column(db.String(15), index=True)  # legacy — kept for compatibility
    dob             = db.Column(db.Date, nullable=True, index=True)  # new proper Date column
    birth_time      = db.Column(db.String(10))
    height          = db.Column(db.Integer, index=True)
    weight          = db.Column(db.Integer)
    complexion      = db.Column(db.String(30))
    body_type       = db.Column(db.String(30))
    # Birth place
    birth_village   = db.Column(db.String(100))
    birth_city      = db.Column(db.String(100))
    birth_state     = db.Column(db.String(100))
    birth_country   = db.Column(db.String(100))
    # Bio
    bio             = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    linkedin_url    = db.Column(db.String(255))
    # Religious / Community (critical for Indian matrimony)
    religion        = db.Column(db.String(50), index=True)
    caste           = db.Column(db.String(80), index=True)
    sub_caste       = db.Column(db.String(80))
    gotra           = db.Column(db.String(80))
    manglik         = db.Column(db.String(20))   # Yes / No / Partial
    mother_tongue   = db.Column(db.String(50))
    # Lifestyle
    diet            = db.Column(db.String(30))   # Vegetarian / Non-Veg / Eggetarian / Vegan
    smoking         = db.Column(db.String(20))   # Never / Occasionally / Regularly
    drinking        = db.Column(db.String(20))
    marital_status  = db.Column(db.String(30), index=True)  # Never Married / Divorced etc
    have_children   = db.Column(db.String(10))   # Yes / No
    # Family
    # Spotlight (Phase 8.2)
    is_spotlight        = db.Column(db.Boolean, default=False, index=True)
    spotlight_expires_at = db.Column(db.DateTime, nullable=True)
    no_brother      = db.Column(db.Boolean, default=False)
    no_sister       = db.Column(db.Boolean, default=False)
    family_type     = db.Column(db.String(30))   # Joint / Nuclear
    family_status   = db.Column(db.String(30))   # Middle Class / Upper Middle etc
    # Maharashtra competitor fields (Phase 12)
    marathi_sub_caste   = db.Column(db.String(80), index=True)   # 96 Kuli Maratha, CKP etc
    gotra_warning_seen  = db.Column(db.Boolean, default=False)   # user acknowledged gotra warning
    birth_nakshatra     = db.Column(db.String(40))               # for Kundli
    birth_rashi         = db.Column(db.String(30))               # Moon sign
    kundli_score        = db.Column(db.Integer)                  # cached Guna Milan 0-36
    hobbies             = db.Column(db.Text)                     # JSON list of hobby strings
    is_nri              = db.Column(db.Boolean, default=False, index=True)
    nri_country         = db.Column(db.String(60))
    id_verified         = db.Column(db.Boolean, default=False)   # admin-granted Aadhaar/ID
    id_verified_at      = db.Column(db.DateTime, nullable=True)
    ui_language         = db.Column(db.String(10), default='en') # 'en' or 'mr' (Marathi)


# ─────────────────────────────────────────────
#  INTEREST (Connect Request — like Shaadi.com)
# ─────────────────────────────────────────────
class Interest(db.Model):
    __tablename__ = 'interests'
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status      = db.Column(db.String(20), default='pending', index=True)
    # pending | accepted | declined | withdrawn
    message     = db.Column(db.String(300))   # optional note with interest
    sent_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender   = db.relationship('User', foreign_keys=[sender_id],   backref='interests_sent')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='interests_received')

    __table_args__ = (
        db.UniqueConstraint('sender_id', 'receiver_id', name='uq_interest'),
    )


# ─────────────────────────────────────────────
#  MESSAGING
# ─────────────────────────────────────────────
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id          = db.Column(db.Integer, primary_key=True)
    user1_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    interest_id = db.Column(db.Integer, db.ForeignKey('interests.id'), nullable=True)

    user1    = db.relationship('User', foreign_keys=[user1_id], backref='conversations_as_user1')
    user2    = db.relationship('User', foreign_keys=[user2_id], backref='conversations_as_user2')
    messages = db.relationship('Message', backref='conversation', lazy='dynamic',
                               order_by='Message.sent_at.asc()', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='uq_conversation'),
    )

    def other_user(self, current_id):
        return self.user2 if self.user1_id == current_id else self.user1

    def last_message(self):
        return self.messages.order_by(db.text('sent_at desc')).first()


class Message(db.Model):
    __tablename__ = 'messages'
    id              = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body            = db.Column(db.Text, nullable=False)
    is_read         = db.Column(db.Boolean, default=False)
    sent_at         = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='messages_sent')


# ─────────────────────────────────────────────
#  SHORTLIST / SAVED PROFILES
# ─────────────────────────────────────────────
class Shortlist(db.Model):
    __tablename__ = 'shortlists'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shortlisted_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user        = db.relationship('User', foreign_keys=[user_id],       backref='shortlisted')
    shortlisted = db.relationship('User', foreign_keys=[shortlisted_id], backref='shortlisted_by')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'shortlisted_id', name='uq_shortlist'),
    )


# ─────────────────────────────────────────────
#  LOCATION
# ─────────────────────────────────────────────
class Country(db.Model):
    __tablename__ = 'countries'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    states    = db.relationship('State',   backref='country', cascade='all, delete-orphan')
    cities    = db.relationship('City',    backref='country', cascade='all, delete-orphan')
    addresses = db.relationship('Address', backref='country', cascade='all, delete-orphan')


class State(db.Model):
    __tablename__ = 'states'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    cities    = db.relationship('City',    backref='state', cascade='all, delete-orphan')
    addresses = db.relationship('Address', backref='state', cascade='all, delete-orphan')


class City(db.Model):
    __tablename__ = 'cities'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    state_id   = db.Column(db.Integer, db.ForeignKey('states.id'),    nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    addresses  = db.relationship('Address', backref='city', cascade='all, delete-orphan')


class Address(db.Model):
    __tablename__ = 'addresses'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),     nullable=False)
    address1   = db.Column(db.String(255), nullable=False)
    address2   = db.Column(db.String(255))
    address3   = db.Column(db.String(255))
    city_id    = db.Column(db.Integer, db.ForeignKey('cities.id'),    nullable=False)
    state_id   = db.Column(db.Integer, db.ForeignKey('states.id'),    nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    zipcode    = db.Column(db.String(10), nullable=False)
    tag        = db.Column(db.String(50), nullable=False)


# ─────────────────────────────────────────────
#  EDUCATION / PROFESSIONAL
# ─────────────────────────────────────────────
class Education(db.Model):
    __tablename__ = 'educations'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    degree          = db.Column(db.String(100), nullable=False)
    specialization  = db.Column(db.String(100), nullable=False)
    university      = db.Column(db.String(255), nullable=False)
    institution     = db.Column(db.String(255), nullable=False)
    year_of_passing = db.Column(db.Integer)
    grade           = db.Column(db.String(20))


class ProfessionalDetails(db.Model):
    __tablename__ = 'professional_details'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    occupation          = db.Column(db.String(100))
    company_name        = db.Column(db.String(100))
    designation         = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer)
    package             = db.Column(db.String(50))   # legacy text field — kept for migration
    income_lpa          = db.Column(db.Integer, nullable=True)   # annual income in LPA (integer)
    turn_over           = db.Column(db.String(50))
    location            = db.Column(db.String(100))
    employment_type     = db.Column(db.String(50))


# ─────────────────────────────────────────────
#  FAMILY
# ─────────────────────────────────────────────
class RelationCategory(db.Model):
    __tablename__ = 'relation_categories'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    relation_types = db.relationship('RelationType', backref='category', lazy='dynamic')


class RelationType(db.Model):
    __tablename__ = 'relation_types'
    id          = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('relation_categories.id'), nullable=False)
    name        = db.Column(db.String(100), nullable=False)


class FamilyDetails(db.Model):
    __tablename__ = 'family_details'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name     = db.Column(db.String(50), nullable=False)
    last_name      = db.Column(db.String(50), nullable=False)
    occupation     = db.Column(db.String(100))
    contact_number = db.Column(db.String(15))
    age            = db.Column(db.Integer)
    email          = db.Column(db.String(120))
    marital_status = db.Column(db.String(20), nullable=False, index=True)
    address_id     = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True)

    relations_from = db.relationship('FamilyRelation', foreign_keys='FamilyRelation.person_id',
                                     backref='person', lazy='dynamic', cascade='all, delete-orphan')
    relations_to   = db.relationship('FamilyRelation', foreign_keys='FamilyRelation.related_person_id',
                                     backref='related_person', lazy='dynamic', cascade='all, delete-orphan')


class FamilyRelation(db.Model):
    __tablename__ = 'family_relations'
    id                = db.Column(db.Integer, primary_key=True)
    person_id         = db.Column(db.Integer, db.ForeignKey('family_details.id'), nullable=False)
    related_person_id = db.Column(db.Integer, db.ForeignKey('family_details.id'), nullable=False)
    relation_type     = db.Column(db.String(50), nullable=False)
    __table_args__ = (
        db.UniqueConstraint('person_id', 'related_person_id', 'relation_type', name='uq_family_relation'),
    )


# ─────────────────────────────────────────────
#  MISC
# ─────────────────────────────────────────────
class PhoneAlternate(db.Model):
    __tablename__ = 'phone_alternates'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone   = db.Column(db.String(15), nullable=False)


class ProfileImage(db.Model):
    __tablename__ = 'profile_images'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_url   = db.Column(db.String(500), nullable=False)   # full size
    thumb_url   = db.Column(db.String(500), nullable=True)    # 150px square
    card_url    = db.Column(db.String(500), nullable=True)    # 400px
    is_primary  = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Language(db.Model):
    __tablename__ = 'languages'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name          = db.Column(db.String(50), nullable=False)
    proficiency   = db.Column(db.String(50))
    certification = db.Column(db.String(80))
    notes         = db.Column(db.Text)


class ProfileView(db.Model):
    __tablename__ = 'profile_views'
    id        = db.Column(db.Integer, primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref='views_made')
    viewed = db.relationship('User', foreign_keys=[viewed_id], backref='views_received')


# ─────────────────────────────────────────────
#  PHASE 4 MODELS
# ─────────────────────────────────────────────

class PartnerPreference(db.Model):
    """What this user wants in a match."""
    __tablename__ = 'partner_preferences'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    min_age        = db.Column(db.Integer)
    max_age        = db.Column(db.Integer)
    min_height     = db.Column(db.Integer)   # cm
    max_height     = db.Column(db.Integer)
    religion       = db.Column(db.String(50))
    caste          = db.Column(db.String(80))
    mother_tongue  = db.Column(db.String(50))
    marital_status = db.Column(db.String(30))
    min_income     = db.Column(db.String(30))     # legacy text — kept for migration
    min_income_lpa = db.Column(db.Integer, nullable=True)   # Integer LPA (C8 resolution)
    max_income_lpa = db.Column(db.Integer, nullable=True)
    education_level = db.Column(db.String(100))
    manglik        = db.Column(db.String(20))
    diet           = db.Column(db.String(30))
    smoking        = db.Column(db.String(20))
    drinking       = db.Column(db.String(20))
    location_preference = db.Column(db.String(100))
    about          = db.Column(db.Text)        # free text "what I'm looking for"

    user = db.relationship('User', backref=db.backref('partner_preference', uselist=False))


class BlockList(db.Model):
    """User A has blocked User B."""
    __tablename__ = 'block_list'
    id          = db.Column(db.Integer, primary_key=True)
    blocker_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    blocker = db.relationship('User', foreign_keys=[blocker_id], backref='blocks_made')
    blocked = db.relationship('User', foreign_keys=[blocked_id], backref='blocked_by')

    __table_args__ = (
        db.UniqueConstraint('blocker_id', 'blocked_id', name='uq_block'),
    )


class UserReport(db.Model):
    """Report a profile to admins."""
    __tablename__ = 'user_reports'
    id          = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason      = db.Column(db.String(100), nullable=False)
    details     = db.Column(db.Text)
    status      = db.Column(db.String(20), default='pending')  # pending|reviewed|dismissed
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_made')
    reported = db.relationship('User', foreign_keys=[reported_id], backref='reports_received')



# ─────────────────────────────────────────────
#  KUNDLI DETAIL  (Phase 12)
# ─────────────────────────────────────────────
class KundliDetail(db.Model):
    """Stores birth chart details for horoscope matching."""
    __tablename__ = 'kundli_details'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    birth_date  = db.Column(db.String(15))
    birth_time  = db.Column(db.String(10))
    birth_city  = db.Column(db.String(100))
    birth_lat   = db.Column(db.Float, nullable=True)
    birth_lng   = db.Column(db.Float, nullable=True)
    rashi       = db.Column(db.String(30))         # Moon sign / Janma Rashi
    nakshatra   = db.Column(db.String(40))         # Birth star
    charan      = db.Column(db.Integer)            # Nakshatra pada (1-4)
    gana        = db.Column(db.String(20))         # Deva / Manushya / Rakshasa
    nadi        = db.Column(db.String(20))         # Adi / Madhya / Antya
    varna       = db.Column(db.String(20))         # Brahmin / Kshatriya / Vaishya / Shudra
    vashya      = db.Column(db.String(20))
    yoni        = db.Column(db.String(30))
    graha_maitri = db.Column(db.String(20))        # planetary friendship
    bhakoot     = db.Column(db.String(20))
    manglik     = db.Column(db.String(20))         # Yes/No/Partial

    user = db.relationship('User', backref=db.backref('kundli', uselist=False))


# ─────────────────────────────────────────────
#  NOTIFICATION  (Phase 5.4)
# ─────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type       = db.Column(db.String(40), nullable=False)
    # Types: interest_received | interest_accepted | new_message | profile_viewed | system
    message    = db.Column(db.String(200), nullable=False)
    link       = db.Column(db.String(200), default='')
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')


# ─────────────────────────────────────────────
#  SUCCESS STORY  (Phase 7.4)
# ─────────────────────────────────────────────
class SuccessStory(db.Model):
    __tablename__ = 'success_stories'
    id           = db.Column(db.Integer, primary_key=True)
    bride_name   = db.Column(db.String(80), nullable=False)
    groom_name   = db.Column(db.String(80), nullable=False)
    city         = db.Column(db.String(80))
    photo_url    = db.Column(db.String(500))
    story        = db.Column(db.Text, nullable=False)
    wedding_year = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  USER BEHAVIOR SIGNALS  (Phase 3 Strategic)
# ─────────────────────────────────────────────
class UserSignal(db.Model):
    """
    Tracks implicit user behavior for match ranking improvement.
    Signals: interest_sent(+1), interest_accepted(+2), interest_declined(-1),
             profile_viewed(+0.3), shortlisted(+0.5), blocked(-2), reported(-3)
    Used to boost or suppress similar profiles in home feed for this user.
    NOT shown to users — internal ranking data only.
    """
    __tablename__ = 'user_signals'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    signal_type   = db.Column(db.String(30), nullable=False)
    # signal_type: interest_sent | interest_accepted | interest_declined |
    #              profile_viewed | shortlisted | blocked | reported
    signal_value  = db.Column(db.Float, nullable=False, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user   = db.relationship('User', foreign_keys=[user_id],
                             backref='signals_given')
    target = db.relationship('User', foreign_keys=[target_user_id],
                             backref='signals_received')

    __table_args__ = (
        db.Index('ix_signal_user_target', 'user_id', 'target_user_id'),
        db.Index('ix_signal_user_type',   'user_id', 'signal_type'),
    )


# ─────────────────────────────────────────────
#  REFERRAL  (Phase 8.1)
# ─────────────────────────────────────────────
class Referral(db.Model):
    __tablename__ = 'referrals'
    id                = db.Column(db.Integer, primary_key=True)
    referrer_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    code              = db.Column(db.String(12), unique=True, nullable=False, index=True)
    rewarded_at       = db.Column(db.DateTime, nullable=True)     # when REFERRER reward granted
    referred_rewarded_at = db.Column(db.DateTime, nullable=True)  # when REFERRED reward granted
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    # Fraud prevention
    ip_address        = db.Column(db.String(45), nullable=True)   # IP at registration time
    device_fingerprint = db.Column(db.String(100), nullable=True) # optional device signal

    referrer = db.relationship('User', foreign_keys=[referrer_id], backref='referrals_made')
    referred = db.relationship('User', foreign_keys=[referred_id], backref='referred_by')


# ─────────────────────────────────────────────
#  ASSISTED PLAN REQUEST  (Phase 14.4)
# ─────────────────────────────────────────────
class AssistedRequest(db.Model):
    """Tracks users on Assisted (Relationship Manager) plan."""
    __tablename__ = 'assisted_requests'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_rm_id  = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    assigned_manager= db.Column(db.String(80), nullable=True)   # display name
    manager_phone   = db.Column(db.String(20), nullable=True)
    notes           = db.Column(db.Text, nullable=True)         # internal RM notes
    status          = db.Column(db.String(20), default='pending')
    # Status: pending | active | completed | cancelled
    curated_profiles= db.Column(db.Text, nullable=True)         # JSON list of user_ids shared
    profiles_target = db.Column(db.Integer, default=15)         # target profiles to send
    profiles_sent   = db.Column(db.Integer, default=0)          # how many sent so far
    family_pref_notes = db.Column(db.Text, nullable=True)       # notes from family preference call
    plan_tier       = db.Column(db.String(20), default='basic') # basic | premium
    payment_ref     = db.Column(db.String(100), nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user       = db.relationship('User', foreign_keys=[user_id], backref='assisted_request')
    assigned_rm = db.relationship('AdminUser', foreign_keys=[assigned_rm_id],
                                  backref='assigned_cases')
    contact_logs = db.relationship('RMContactLog', backref='request',
                                   cascade='all, delete-orphan',
                                   order_by='RMContactLog.logged_at.desc()')


class RMContactLog(db.Model):
    """Records each RM-client interaction for Assisted plan workflow."""
    __tablename__ = 'rm_contact_logs'
    id            = db.Column(db.Integer, primary_key=True)
    request_id    = db.Column(db.Integer, db.ForeignKey('assisted_requests.id'), nullable=False)
    admin_id      = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    contact_type  = db.Column(db.String(30), nullable=False)
    # contact_type: call | whatsapp | email | meeting | profile_shared | outcome_noted
    summary       = db.Column(db.Text, nullable=False)
    outcome       = db.Column(db.String(50), nullable=True)
    # outcome: interested | not_interested | meeting_arranged | family_approved | pending
    next_action   = db.Column(db.Text, nullable=True)
    logged_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    admin = db.relationship('AdminUser', foreign_keys=[admin_id])


# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN AUDIT LOG  (Phase 2 Strategic — tracks all staff actions)
# ─────────────────────────────────────────────────────────────────────────────
class AdminAuditLog(db.Model):
    """
    Immutable audit trail for all staff actions via /console/.
    Never update or delete rows — only insert.
    """
    __tablename__ = 'admin_audit_logs'

    id          = db.Column(db.Integer, primary_key=True)
    admin_id    = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    action      = db.Column(db.String(80), nullable=False)
    # action examples: suspend_user, activate_user, activate_subscription,
    #                  dismiss_report, suspend_reported_user, grant_id_verify,
    #                  revoke_id_verify, update_assisted, create_staff, deactivate_staff
    target_type = db.Column(db.String(30), nullable=True)   # 'user' | 'subscription' | 'report'
    target_id   = db.Column(db.Integer,    nullable=True)
    detail      = db.Column(db.Text,       nullable=True)   # JSON or plain text note
    ip_address  = db.Column(db.String(45), nullable=True)
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow, nullable=False)

    admin = db.relationship('AdminUser', foreign_keys=[admin_id], backref='audit_logs')


# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN USER  (Phase 16 — Staff Console)
#  Completely separate from User model — staff are NOT matchmaking users
# ─────────────────────────────────────────────────────────────────────────────
class AdminUser(db.Model):
    """
    Staff accounts — completely separate from User (matchmaking) accounts.
    AdminUsers can log in to /console/ only.
    They are NOT counted in user stats, NOT visible in search, NOT matched.

    Roles and permissions:
        ceo              — full access to everything
        vp               — analytics + user management + reports, no plan pricing
        business_owner   — analytics + revenue + plans + reports
        relationship_manager — only their assigned assisted requests + user notes
        executive        — user management + reports, no analytics/revenue
    """
    __tablename__ = 'admin_users'

    ROLES = ['ceo', 'vp', 'business_owner', 'relationship_manager', 'executive']

    PERMISSIONS = {
        'ceo': {
            'dashboard', 'analytics', 'revenue', 'users', 'plans',
            'reports', 'stories', 'assisted', 'staff', 'settings',
        },
        'vp': {
            'dashboard', 'analytics', 'users', 'reports', 'stories', 'assisted',
        },
        'business_owner': {
            'dashboard', 'analytics', 'revenue', 'plans', 'reports', 'stories',
        },
        'relationship_manager': {
            'dashboard', 'assisted',
        },
        'executive': {
            'dashboard', 'users', 'reports', 'stories',
        },
    }

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(80), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(30), nullable=False, default='executive')
    is_active           = db.Column(db.Boolean, default=True)
    last_login          = db.Column(db.DateTime, nullable=True)
    failed_login_count  = db.Column(db.Integer, default=0)   # brute force protection
    locked_until        = db.Column(db.DateTime, nullable=True)
    # TOTP 2FA (Google Authenticator)
    totp_secret         = db.Column(db.String(64), nullable=True)  # base32 secret
    totp_enabled        = db.Column(db.Boolean, default=False)
    totp_verified_at    = db.Column(db.DateTime, nullable=True)    # when 2FA was first confirmed
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id       = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)

    created_by = db.relationship('AdminUser', remote_side=[id], backref='staff_created')

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def generate_totp_secret(self):
        """Generate a new TOTP secret. Call once during 2FA setup."""
        import pyotp
        self.totp_secret = pyotp.random_base32()
        return self.totp_secret

    def get_totp_uri(self):
        """Return the otpauth:// URI for QR code generation."""
        import pyotp
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name='iJodidar Console'
        )

    def verify_totp(self, code: str) -> bool:
        """Verify a 6-digit TOTP code. Allows 30s window drift."""
        if not self.totp_secret or not self.totp_enabled:
            return True   # 2FA not set up — allow login
        import pyotp
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(str(code).strip(), valid_window=1)

    def can(self, permission):
        return permission in self.PERMISSIONS.get(self.role, set())

    @property
    def role_label(self):
        return {
            'ceo':                  'CEO',
            'vp':                   'VP',
            'business_owner':       'Business Owner',
            'relationship_manager': 'Relationship Manager',
            'executive':            'Executive',
        }.get(self.role, self.role.title())

    def __repr__(self):
        return f'<AdminUser {self.email} ({self.role})>'


# ─────────────────────────────────────────────
#  USER DEVICE  (Sprint 3 — FCM push tokens)
# ─────────────────────────────────────────────
class UserDevice(db.Model):
    """FCM push token registry for mobile push notifications."""
    __tablename__ = 'user_devices'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    fcm_token   = db.Column(db.String(300), nullable=False, unique=True)
    platform    = db.Column(db.String(10), nullable=False)   # android | ios | web
    app_version = db.Column(db.String(20), nullable=True)
    last_seen   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='devices')
