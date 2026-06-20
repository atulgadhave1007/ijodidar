"""
auth/forms.py — WTForms definitions for all auth pages.

Field names match EXACTLY what routes.py reads via request.form
and what the User model columns are named.

RegistrationForm field → request.form key → User model field
  firstname  → first_name
  lastname   → last_name
  username   → username
  email      → email
  phone      → phone
  password   → password_hash (via set_password())
  password2  → (confirmation only, not stored)
"""
import re
from datetime import date, datetime
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField,
                     BooleanField, TelField, DateField)
from wtforms.validators import (DataRequired, Email, EqualTo,
                                Length, Regexp, ValidationError, Optional)
from app.models import User


# ── Shared validator ───────────────────────────────────────────────────────
_phone_re = re.compile(r'^\+?[\d\s\-]{10,15}$')


def _validate_phone(form, field):
    if not _phone_re.match(field.data.strip()):
        raise ValidationError('Enter a valid phone number (10–15 digits).')


# ── Registration ────────────────────────────────────────────────────────────
class RegistrationForm(FlaskForm):
    """
    Maps to: User(first_name, last_name, username, email, phone, password_hash)
    Field names here must match request.form keys used in register() route.
    """
    firstname = StringField(
        'First Name',
        validators=[DataRequired(message='First name is required.'),
                    Length(1, 50, message='Max 50 characters.')]
    )
    lastname = StringField(
        'Last Name',
        validators=[DataRequired(message='Last name is required.'),
                    Length(1, 50, message='Max 50 characters.')]
    )
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(3, 64, message='Username must be 3–64 characters.'),
            Regexp(r'^[a-z0-9_\.]+$',
                   message='Only lowercase letters, numbers, _ and . allowed.'),
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
            Length(max=120),
        ]
    )
    phone = TelField(
        'Phone',
        validators=[
            DataRequired(message='Phone number is required.'),
            _validate_phone,
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, message='Password must be at least 8 characters.'),
        ]
    )
    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ]
    )
    date_of_birth = DateField(
        'Date of Birth',
        validators=[Optional()],
        format='%Y-%m-%d',
    )
    consent = BooleanField(
        'I agree to the Privacy Policy and Terms of Service',
        validators=[DataRequired(message='You must accept the terms to register.')]
    )
    submit = SubmitField('Create Account')

    def validate_date_of_birth(self, field):
        if field.data:
            today = date.today()
            age = today.year - field.data.year - (
                (today.month, today.day) < (field.data.month, field.data.day)
            )
            if age < 18:
                raise ValidationError('You must be at least 18 years old to register.')

    # Cross-field DB uniqueness validators (called automatically by WTForms)
    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip().lower()).first():
            raise ValidationError('Username already taken. Please choose another.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError('Email already registered. Please log in instead.')


# ── Login ───────────────────────────────────────────────────────────────────
class LoginForm(FlaskForm):
    """Maps to: User.email + User.check_password()"""
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required.')]
    )
    remember = BooleanField('Remember me')
    submit   = SubmitField('Sign In')


# ── Forgot Password ─────────────────────────────────────────────────────────
class ForgotPasswordForm(FlaskForm):
    """Maps to: User.email for reset token generation."""
    email  = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
        ]
    )
    submit = SubmitField('Send Reset Link')


# ── Reset Password ──────────────────────────────────────────────────────────
class ResetPasswordForm(FlaskForm):
    """Maps to: User.set_password(password)"""
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters.'),
        ]
    )
    password2 = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.'),
        ]
    )
    submit = SubmitField('Reset Password')
