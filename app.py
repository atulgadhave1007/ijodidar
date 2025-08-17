from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from dotenv import load_dotenv
from sqlalchemy import or_, and_, not_
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from collections import defaultdict  # ✅ Add this import
from flask_migrate import Migrate

# Load .env file (works both locally and on EC2)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# instantiate application and database
# Instantiate Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Auto-switch between PostgreSQL and SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # fallback to local SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


import boto3
import os

# Config
REGION = os.getenv("AWS_REGION", "ap-south-1")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET", "ijodidar-images")

# Use IAM role (no keys needed on EC2)
s3 = boto3.client("s3", region_name=REGION)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


db = SQLAlchemy(app)
app.app_context().push()
migrate = Migrate(app, db)

@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)


# User Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete")
    addresses = db.relationship('Address', backref='user', cascade="all, delete")
    educations = db.relationship('Education', backref='user', cascade="all, delete")
    professional_details = db.relationship('ProfessionalDetails', backref='user', cascade="all, delete")
    family_details = db.relationship('FamilyDetails', backref='user', cascade="all, delete")
    phone_alternates = db.relationship('PhoneAlternate', backref='user', cascade="all, delete")
    profile_images = db.relationship('ProfileImage', backref='user', cascade="all, delete")
    languages = db.relationship('Language', backref='user', cascade="all, delete")

    
    #dinner_patry = db.relationship('DinnerParty')
    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Profile(UserMixin, db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    gender = db.Column(db.String(10), index=True)
    looking_for = db.Column(db.String(10), index=True)
    date_of_birth = db.Column(db.String(15), index=True)  # Prefer storing as string if not using Date
    birth_time = db.Column(db.String(10), nullable=True)  # Added for storing birth time like '14:45'

    height = db.Column(db.Integer, index=True)
    
    # Place of birth split into components
    birth_village = db.Column(db.String(100), nullable=True)
    birth_city = db.Column(db.String(100), nullable=True)
    birth_state = db.Column(db.String(100), nullable=True)
    birth_country = db.Column(db.String(100), nullable=True)

    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)

    # existing fields ...
    no_brother = db.Column(db.Boolean, default=False)
    no_sister = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Profile {self.user.first_name} {self.user.last_name}>"

class Address(UserMixin, db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address1 = db.Column(db.String(255), nullable=False)
    address2 = db.Column(db.String(255))
    address3 = db.Column(db.String(255))
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    zipcode = db.Column(db.String(10), nullable=False)
    # New tag field
    tag = db.Column(db.String(50), nullable=False)  # 'permanent', 'current', or 'work'


class City(UserMixin, db.Model):
   __tablename__ = 'cities'
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), nullable=False)
   state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
   country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
   
   # Relationships
   addresses = db.relationship('Address', backref='city', cascade="all, delete")


class State(UserMixin, db.Model):
   __tablename__ = 'states'
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), nullable=False)
   country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
   
   # Relationships
   cities = db.relationship('City', backref='state', cascade="all, delete")
   addresses = db.relationship('Address', backref='state', cascade="all, delete")

class Country(UserMixin, db.Model):
   __tablename__ = 'countries'
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), nullable=False)
   
   #Relationships
   cities = db.relationship('City', backref='country', cascade="all, delete")
   states = db.relationship('State', backref='country', cascade="all, delete")
   addresses = db.relationship('Address', backref='country', cascade="all, delete")

class Education(UserMixin, db.Model):
    __tablename__ = 'educations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    university = db.Column(db.String(255), nullable=False)  # New field
    institution = db.Column(db.String(255), nullable=False)
    year_of_passing = db.Column(db.Integer)
    grade = db.Column(db.String(20))

class ProfessionalDetails(db.Model):
    __tablename__ = 'professional_details'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    occupation = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer)
    package = db.Column(db.String(50))
    turn_over = db.Column(db.String(50))
    location = db.Column(db.String(100))    
    # ✅ New field for employment type
    employment_type = db.Column(db.String(50))  # e.g., 'Full-time', 'Part-time', 'Contract'


class RelationCategory(db.Model):
    __tablename__ = 'relation_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    relation_types = db.relationship('RelationType', backref='category', lazy='dynamic')

class RelationType(db.Model):
    __tablename__ = 'relation_types'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('relation_categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)


class FamilyRelation(db.Model):
    __tablename__ = 'family_relations'
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('family_details.id'), nullable=False)
    related_person_id = db.Column(db.Integer, db.ForeignKey('family_details.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('person_id', 'related_person_id', 'relation_type', name='uq_family_relation'),
    )

    def __repr__(self):
        return f"<FamilyRelation {self.person_id} -> {self.related_person_id} ({self.relation_type})>"


class FamilyDetails(db.Model):
    __tablename__ = 'family_details'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    occupation = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(15), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(120))
    marital_status = db.Column(db.String(20), nullable=False, index=True)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True)

    relations_from = db.relationship(
        "FamilyRelation",
        foreign_keys="FamilyRelation.person_id",
        backref="person",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    relations_to = db.relationship(
        "FamilyRelation",
        foreign_keys="FamilyRelation.related_person_id",
        backref="related_person",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FamilyDetails {self.first_name} {self.last_name}>"



class PhoneAlternate(db.Model):
    __tablename__ = 'phone_alternates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    

class ProfileImage(db.Model):
    __tablename__ = 'profile_images'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Language(db.Model):
    __tablename__ = 'languages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    proficiency = db.Column(db.String(50), nullable=True)
    certification = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Language {self.name} ({self.proficiency})>"

class ProfileView(db.Model):
    __tablename__ = 'profile_views'

    id = db.Column(db.Integer, primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships to User
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref='views_made')
    viewed = db.relationship('User', foreign_keys=[viewed_id], backref='views_received')


class ProfileSearchForm(FlaskForm):
    keyword = StringField("Search", render_kw={"placeholder": "Search by name, city, company..."})
    gender = SelectField("Gender", choices=[('', 'Any'), ('Male', 'Male'), ('Female', 'Female')])
    min_age = IntegerField("Min Age")
    max_age = IntegerField("Max Age")
    caste = StringField("Caste")
    same_caste_only = BooleanField("Same Caste Only")
    religion = StringField("Religion")
    education = StringField("Education")
    marital_status = SelectField("Marital Status", choices=[('', 'Any'), ('Never Married', 'Never Married'), ('Divorced', 'Divorced')])
    city = StringField("City")
    submit = SubmitField("Search")


# create login manager
login_manager = LoginManager()
login_manager.init_app(app)

# registration form
class RegistrationForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  firstname = StringField('First Name', validators=[DataRequired()])
  lastname = StringField('Last Name', validators=[DataRequired()])
  phone = StringField('Phone', validators=[DataRequired()])
  email = StringField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Register')

# login form
class LoginForm(FlaskForm):
  email = StringField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')

# registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(csrf_enabled=False)
    if request.method == 'POST':
        username = request.form.get('username')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        user = User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists.', category='error')
        elif password != password2:
            flash('Password don\'t match', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(username=username, first_name=firstname, last_name=lastname, phone=phone, email=email, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()

            flash('Account created!', category='success')
            return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form, user=current_user)

# user loader
@login_manager.user_loader
def load_user(id):

  return User.query.get(int(id))
# login route
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET','POST'])
def login():
  form = LoginForm(csrf_enabled=False)
  if request.method == 'POST':
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    username = User.query.filter_by(username=username).first() 
    user = User.query.filter_by(email=email).first()
    if user:
      if check_password_hash(user.password_hash, password):
        flash('Logged in sucessfully!', category='success')
        login_user(user, remember=True)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))
      else:
        flash('Incorrect password, try again.', category='error')
    elif username:
      if check_password_hash(user.password_hash, password):
        flash('Logged in sucessfully!', category='success')
        login_user(user, remember=True)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))
      else:
        flash('Incorrect password, try again.', category='error')
    else:
      flash('Username or Email does not exist.', category='error')
      return redirect(url_for('login'))
  return render_template('login.html', form=form, user=current_user)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
  user=User.query.filter_by(id=id).first()
  db.session.delete(user)
  db.session.commit()
  return redirect(url_for('home'))



# landing page route
@app.route('/home')
@login_required
def home():
  current_users = User.query.all()
  return render_template('home.html', current_users = current_users, user=current_user)

# Profile Update
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = RegistrationForm(csrf_enabled=False)
    user = current_user
    profile = Profile.query.filter_by(user_id=user.id).first()
    

    # Convert string to date if needed
    if profile and isinstance(profile.date_of_birth, str):
        try:
            profile.date_of_birth = datetime.strptime(profile.date_of_birth, '%Y-%m-%d').date()
        except ValueError:
            profile.date_of_birth = None  # fallback

    phone_alternate = PhoneAlternate.query.filter_by(user_id=user.id)
    address=Address.query.filter_by(user_id=user.id).first();
    city = City.query.get(address.city_id) if address else None
    state = State.query.get(address.state_id) if address else None
    country = Country.query.get(address.country_id) if address else None
    # Get addresses by tag
    permanent = Address.query.filter_by(user_id=user.id, tag='Permanent').first()
    current = Address.query.filter_by(user_id=user.id, tag='Current').first()
    work = Address.query.filter_by(user_id=user.id, tag='Work').first()
    professional = ProfessionalDetails.query.filter_by(user_id=user.id).first()
    education = Education.query.filter_by(user_id=user.id).first()
    
    #✅ Fetch images
    profile_images = ProfileImage.query.filter_by(user_id=user.id).all()
    primary_image = next((img for img in profile_images if img.is_primary), None)


    return render_template(
        'profile.html',
        user=user,
        profile=profile,
        phone_alternate=phone_alternate,
        city=city,
        state=state,
        country=country,
        permanent=permanent,
        current=current,
        work=work,
        professional = professional,
        education=education,
        profile_images=profile_images,
        primary_image=primary_image,
        form=form
    )


#Unauthorized Warning
@app.route('/unauthorized', methods=['GET', 'POST'])
@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    return "You are not logged in. Click here to get <a href="+ str("/")+">back to Landing Page</a>"


# landing page route
@app.route('/assets')
@login_required
def assets():
  user_id=current_user.id
  address=Address.query.filter_by(user_id=user_id).first();
  current_users = User.query.all()
  return render_template('assets.html', address=address, current_users = current_users, user=current_user)


# User Update
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
  form = RegistrationForm(csrf_enabled=False)
  if request.method == 'POST':
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    user=User.query.filter_by(id=id).first()
    user.first_name = firstname
    user.last_name = lastname
    user.email = email
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('home'))
      
  user=User.query.filter_by(id=id).first()
  return render_template('update.html', user=user, form=form)


@app.route('/name', methods=['GET', 'POST'])
@login_required
def name():
    form = RegistrationForm(csrf_enabled=False)
    user=current_user
    if request.method == 'POST':
        # Retrieve the form data
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        user.first_name = first_name
        user.last_name = last_name
        db.session.add(user)
        db.session.commit()

        # Redirect back to the homepage (or wherever you wish)
        return redirect(url_for('profile'))
    
    return render_template('name.html', user=user)

@app.route('/looking_for', methods=['GET', 'POST'])
@login_required
def looking_for():
    user = current_user
    profile = Profile.query.filter_by(user_id=user.id).first()


    if request.method == 'POST':
        looking_for_value = request.form.get('looking_for')

        if profile:
            profile.looking_for = looking_for_value
        else:
            profile = Profile(user_id=user.id, looking_for=looking_for_value)
            db.session.add(profile)

        db.session.commit()
        flash("Looking For updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('looking_for.html', user=user, profile=profile)


@app.route('/email', methods=['GET', 'POST'])
@login_required
def email():
    user = current_user

    if request.method == 'POST':
        new_email = request.form.get('email')

        # Basic validation
        if not new_email:
            flash("Email field cannot be empty.", "danger")
            return redirect(url_for('email'))

        # Optional: Check for duplicate emails
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != user.id:
            flash("This email is already registered with another account.", "danger")
            return redirect(url_for('email'))

        # Update and commit
        user.email = new_email
        db.session.commit()
        flash("Email updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('email.html', user=user)

@app.route('/phone', methods=['GET', 'POST'])
@login_required
def phone():
    user = current_user
    alternate_phones = PhoneAlternate.query.filter_by(user_id=user.id).all()

    if request.method == 'POST':
        # Update primary phone
        new_primary = request.form.get('phone')
        if new_primary:
            user.phone = new_primary

        # Handle new alternate phones (input limit = 2)
        submitted_alts = request.form.getlist('alternate_phones')
        submitted_alts = [p.strip() for p in submitted_alts if p.strip()]

        # Prevent more than 2 alternate numbers
        if len(submitted_alts) > 2:
            flash('You can only add up to 2 alternate phone numbers.', 'danger')
            return redirect(url_for('phone'))

        # Delete old alternate phones
        PhoneAlternate.query.filter_by(user_id=user.id).delete()

        # Add only the new ones (max 2)
        for phone in submitted_alts[:2]:
            db.session.add(PhoneAlternate(user_id=user.id, phone=phone))

        db.session.commit()
        flash('Phone numbers updated successfully.', 'success')
        return redirect(url_for('phone'))

    return render_template('phone.html', user=user, alternate_phones=alternate_phones)


# Helper function to convert month name to number
def convert_month_to_number(month_name):
    try:
        return datetime.strptime(month_name, "%B").month  # Converts "January" → 1
    except ValueError:
        return None  # Handle invalid month gracefully

@app.route('/birthday', methods=['GET', 'POST'])
@login_required
def birthday():
    user = current_user
    profile = Profile.query.filter_by(user_id=user.id).first()

    # Initialize fields
    month = day = year = None
    birth_time = ""
    birth_village = ""
    birth_city = ""
    birth_state = ""
    birth_country = ""

    if profile:
        # Extract DOB parts if available
        if profile.date_of_birth:
            try:
                if isinstance(profile.date_of_birth, str):
                    dob = datetime.strptime(profile.date_of_birth, "%Y-%m-%d")
                else:
                    dob = profile.date_of_birth

                month = dob.strftime("%B")
                day = dob.day
                year = dob.year
            except Exception as e:
                print("DOB parsing error:", e)

        # Pre-fill other values
        birth_time = profile.birth_time or ""
        birth_village = profile.birth_village or ""
        birth_city = profile.birth_city or ""
        birth_state = profile.birth_state or ""
        birth_country = profile.birth_country or ""

    # Handle form submit
    if request.method == 'POST':
        # Basic DOB fields
        month_name = request.form.get('month')
        day = request.form.get('date')
        year = request.form.get('year')

        # New fields
        birth_time = request.form.get('birth_time', '').strip()
        birth_village = request.form.get('birth_village', '').strip()
        birth_city = request.form.get('birth_city', '').strip()
        birth_state = request.form.get('birth_state', '').strip()
        birth_country = request.form.get('birth_country', '').strip()

        if not (month_name and day and year):
            flash("Date of birth fields are required.", "danger")
            return redirect(url_for('birthday'))

        try:
            month_number = datetime.strptime(month_name, "%B").month
            dob = datetime(int(year), month_number, int(day)).date()

            if not profile:
                profile = Profile(user_id=user.id)
                db.session.add(profile)

            profile.date_of_birth = dob
            profile.birth_time = birth_time
            profile.birth_village = birth_village
            profile.birth_city = birth_city
            profile.birth_state = birth_state
            profile.birth_country = birth_country

            db.session.commit()
            flash("Birth details updated successfully!", "success")
            return redirect(url_for('profile'))

        except Exception as e:
            print("Birthday update error:", e)
            flash("Invalid input. Please check the data.", "danger")

    return render_template('birthday.html', user=user, profile=profile,
                           month=month, day=day, year=year,
                           birth_time=birth_time,
                           birth_village=birth_village,
                           birth_city=birth_city,
                           birth_state=birth_state,
                           birth_country=birth_country)

@app.route('/gender', methods=['GET', 'POST'])
@login_required
def gender():
    user = current_user
    profile = Profile.query.filter_by(user_id=user.id).first()

    if request.method == 'POST':
        selected_gender = request.form.get('gender')

        if not selected_gender:
            flash("Please select a gender", "danger")
            return redirect(url_for('gender'))

        if profile:
            profile.gender = selected_gender
        else:
            profile = Profile(user_id=user.id, gender=selected_gender)
            db.session.add(profile)

        db.session.commit()
        flash("Gender updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('gender.html', user=user, profile=profile)

@app.route('/address/<tag>', methods=['GET', 'POST'])
@login_required
def address(tag):
    if tag.lower() not in ['permanent', 'current', 'work']:
        return "Invalid address tag", 400

    user = current_user
    address = Address.query.filter_by(user_id=user.id, tag=tag.capitalize()).first()

    cities = City.query.all()
    states = State.query.all()
    countries = Country.query.all()

    if request.method == 'POST':
        if not address:
            address = Address(user_id=user.id, tag=tag.capitalize())

        address.address1 = request.form.get('address1')
        address.address2 = request.form.get('address2')
        address.address3 = request.form.get('address3')
        address.city_id = request.form.get('city_id')
        address.state_id = request.form.get('state_id')
        address.country_id = request.form.get('country_id')
        address.zipcode = request.form.get('zipcode')
        address.tag=tag.capitalize()

        db.session.add(address)
        db.session.commit()
        return redirect(url_for('profile'))

    return render_template('address.html', user=user, address=address, cities=cities, states=states, countries=countries, tag=tag)

@app.route('/professional', methods=['GET', 'POST'])
@login_required
def professional():
    user = current_user
    professional = ProfessionalDetails.query.filter_by(user_id=user.id).first()

    if not professional:
        professional = ProfessionalDetails(user_id=user.id)
        db.session.add(professional)

    if request.method == 'POST':
        occupation_input = request.form.get('occupation')
        if occupation_input:
            professional.occupation = occupation_input

        db.session.commit()
        flash("Occupation updated.", "success")
        return redirect(url_for('profile'))

    return render_template('professional.html', user=user, professional=professional)


@app.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    user = current_user
    professional = ProfessionalDetails.query.filter_by(user_id=user.id).first()

    if not professional:
        professional = ProfessionalDetails(user_id=user.id)
        db.session.add(professional)

    if request.method == 'POST':
        company_name = request.form.get('company_name')
        experience = request.form.get('years_of_experience')
        package = request.form.get('package')
        turnover = request.form.get('turn_over')
        location = request.form.get('location')

        if company_name:
            professional.company_name = company_name
        if experience:
            professional.years_of_experience = experience
        if package:
            professional.package = package
        if turnover:
            professional.turn_over = turnover
        if location:
            professional.location = location

        db.session.commit()
        flash("Company details updated.", "success")
        return redirect(url_for('profile'))

    return render_template('company.html', user=user, professional=professional)


@app.route('/designation', methods=['GET', 'POST'])
@login_required
def designation():
    user = current_user
    professional = ProfessionalDetails.query.filter_by(user_id=user.id).first()

    if not professional:
        professional = ProfessionalDetails(user_id=user.id)
        db.session.add(professional)

    if request.method == 'POST':
        designation_input = request.form.get('designation')
        if designation_input:
            professional.designation = designation_input

        db.session.commit()
        flash("Designation updated.", "success")
        return redirect(url_for('profile'))

    return render_template('designation.html', user=user, professional=professional)

@app.route('/education', methods=['GET', 'POST'])
@login_required
def education():
    user = current_user
    education = Education.query.filter_by(user_id=user.id).first()

    if request.method == 'POST':
        degree = request.form.get('degree')
        specialization = request.form.get('specialization')
        university = request.form.get('university')
        institution = request.form.get('institution')
        year_of_passing = request.form.get('year_of_passing')
        grade = request.form.get('grade')

        if not education:
            education = Education(user_id=user.id)

        education.degree = degree
        education.specialization = specialization
        education.university = university
        education.institution = institution
        education.year_of_passing = int(year_of_passing) if year_of_passing else None
        education.grade = grade

        db.session.add(education)  # Only add after full data
        db.session.commit()
        flash("Education details updated.", "success")
        return redirect(url_for('profile'))

    return render_template('education.html', user=user, education=education)


@app.route('/university', methods=['GET', 'POST'])
@login_required
def university():
    user = current_user
    education = Education.query.filter_by(user_id=user.id).first()

    if not education:
        education = Education(user_id=user.id)
        db.session.add(education)

    if request.method == 'POST':
        university_name = request.form.get('university')
        if university_name:
            education.university = university_name
            db.session.commit()
            flash("University information updated successfully.", "success")
            return redirect(url_for('profile'))

    return render_template('university.html', user=user, education=education)


@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    file = request.files.get('image')
    is_primary = request.form.get('is_primary') in ['true', 'on']

    # Validate file
    if not file or file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('my_profile'))

    if not allowed_file(file.filename):
        flash("Only JPG, JPEG, and PNG are allowed.", "danger")
        return redirect(url_for('my_profile'))

    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_FILE_SIZE:
        flash("File too large (max 2MB).", "danger")
        return redirect(url_for('my_profile'))
    file.seek(0)  # reset pointer for upload

    # ✅ Auto-set primary if user has none
    if ProfileImage.query.filter_by(user_id=current_user.id, is_primary=True).count() == 0:
        is_primary = True

    # ✅ Limit additional images to 5
    if not is_primary:
        count = ProfileImage.query.filter_by(user_id=current_user.id, is_primary=False).count()
        if count >= 5:
            flash("You can only upload up to 5 additional images.", "warning")
            return redirect(url_for('my_profile'))

    # ✅ Upload to S3
    filename = f"profile_images/{uuid4()}_{secure_filename(file.filename)}"
    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={"ContentType": file.content_type}
        )
    except Exception as e:
        app.logger.error(f"S3 Upload failed: {e}")
        flash("Image upload failed. Please try again.", "danger")
        return redirect(url_for('my_profile'))

    # Public URL
    image_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{filename}"

    # ✅ If new primary, delete old primary
    if is_primary:
        old_primary = ProfileImage.query.filter_by(user_id=current_user.id, is_primary=True).first()
        if old_primary:
            try:
                old_key = old_primary.image_url.split(f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/")[-1]
                s3.delete_object(Bucket=BUCKET_NAME, Key=old_key)
            except Exception as e:
                app.logger.warning(f"Failed to delete old primary from S3: {e}")
            db.session.delete(old_primary)

    # ✅ Save record in DB
    new_image = ProfileImage(
        user_id=current_user.id,
        image_url=image_url,
        is_primary=is_primary
    )
    db.session.add(new_image)
    db.session.commit()

    flash("Image uploaded successfully!", "success")
    return redirect(url_for('my_profile'))


@app.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    image = ProfileImage.query.get_or_404(image_id)

    # Ensure the image belongs to the current user
    if image.user_id != current_user.id:
        abort(403)

    # Try to delete from S3
    try:
        if image.image_url and f"{BUCKET_NAME}.s3.{REGION}.amazonaws.com" in image.image_url:
            key = image.image_url.split(f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/")[-1]
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
    except Exception as e:
        app.logger.warning(f"[S3 Delete Failed] key={key} error={e}")
        flash("Could not delete image from S3, but removed from profile.", "warning")

    # Delete from DB
    db.session.delete(image)
    db.session.commit()

    flash("Image deleted successfully.", "info")
    return redirect(url_for('my_profile'))


@app.route('/set_primary_image/<int:image_id>')
@login_required
def set_primary_image(image_id):
    image = ProfileImage.query.get_or_404(image_id)

    if image.user_id != current_user.id:
        abort(403)

    # Reset all images to not primary
    ProfileImage.query.filter_by(user_id=current_user.id).update({"is_primary": False})

    # Set selected image to primary
    image.is_primary = True
    db.session.commit()

    flash("Primary image set successfully.", "success")
    return redirect(url_for('profile'))


'''
@app.route('/my_profile')
@login_required
def my_profile():
    user=current_user
    return render_template('my_profile.html', user=user)
'''

def calculate_profile_completeness(user):
    total_score = 0
    max_score = 100

    # Basic info: Name, Username, Email, Phone
    if user.first_name: total_score += 2
    if user.last_name: total_score += 2
    if user.username: total_score += 2
    if user.email: total_score += 2
    if user.phone: total_score += 2

    # Profile info: DOB, Gender, Looking for, Height, Bio, LinkedIn
    profile = user.profile
    if profile:
        if profile.date_of_birth: total_score += 2
        if profile.birth_time: total_score += 1
        if profile.gender: total_score += 1
        if profile.looking_for: total_score += 1
        if profile.height: total_score += 1
        if profile.bio: total_score += 1
        if profile.linkedin_url: total_score += 1
        if profile.birth_city or profile.birth_state or profile.birth_country: total_score += 2

    # Address: At least 1 complete address (tagged)
    if user.addresses:
        for addr in user.addresses:
            if addr.address1 and addr.city_id and addr.state_id and addr.country_id and addr.zipcode:
                total_score += 4
                break

    # Profile Images: Primary + additional
    images = user.profile_images
    if images:
        if any(img.is_primary for img in images): total_score += 4
        additional = [img for img in images if not img.is_primary]
        if len(additional) >= 1: total_score += 2
        if len(additional) >= 2: total_score += 1
        if len(additional) >= 3: total_score += 1

    # Family Details
    if user.family_details and len(user.family_details) >= 1:
        total_score += min(len(user.family_details), 3) * 2  # max 6 points

    # Education: At least one entry
    if user.educations:
        for edu in user.educations:
            if edu.degree and edu.specialization and edu.university and edu.institution:
                total_score += 5
                break

    # Occupation (Professional Details)
    if user.professional_details:
        for job in user.professional_details:
            if job.occupation and job.company_name:
                total_score += 5
                break

    # Alternate Phone
    if user.phone_alternates and len(user.phone_alternates) >= 1:
        total_score += 2

    # Languages
    if user.languages and len(user.languages) >= 1:
        total_score += min(len(user.languages), 3)  # Max 3 points

    # Janmkundali (Assumed as a document or URL stored in `profile.profile_picture` or a future field)
    if profile and profile.profile_picture:
        total_score += 4

    # Cap score to max
    return min(int((total_score / max_score) * 100), 100)


# Redirect /my_profile to /<username>
@app.route('/my_profile')
@login_required
def my_profile_redirect():
    return redirect(url_for('user_profile', username=current_user.username))


# Dynamic profile route using username in the URL
@app.route('/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_own_profile = user.id == current_user.id
    
    profile = user.profile

    # ✅ Track profile view if not self
    if not is_own_profile:
        views = (
            ProfileView.query
            .filter_by(viewer_id=current_user.id, viewed_id=user.id)
            .order_by(ProfileView.timestamp.asc())
            .all()
        )

        if len(views) < 3:
            new_view = ProfileView(
                viewer_id=current_user.id,
                viewed_id=user.id,
                timestamp=datetime.utcnow()
            )
            db.session.add(new_view)
        else:
            # Replace oldest view
            oldest_view = views[0]
            oldest_view.timestamp = datetime.utcnow()

        db.session.commit()

    # ✅ Recent visitors of *current_user* (not the profile being viewed)
    recent_views = (
        ProfileView.query
        .filter_by(viewed_id=current_user.id)
        .order_by(ProfileView.timestamp.desc())
        .limit(3)
        .all()
    )

    # ✅ Parse date_of_birth for viewed_by_users
    viewed_by_users = []
    seen_ids = set()

    for view in recent_views:
        viewer = view.viewer
        if viewer.id in seen_ids:
            continue  # skip duplicates

        seen_ids.add(viewer.id)

        # Convert dob if it's a string
        dob = getattr(viewer.profile, 'date_of_birth', None)
        if dob and not isinstance(profile.date_of_birth, str):
            try:
                viewer.profile.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                viewer.profile.date_of_birth = None
        viewed_by_users.append(viewer)

    # ✅ Common profile data
    
    profile_images = user.profile_images.all() if hasattr(user.profile_images, 'all') else user.profile_images
    addresses = user.addresses
    educations = user.educations
    professional_details = user.professional_details
    family_members = user.family_details
    alternate_phones = user.phone_alternates

    # ✅ Suggested matches based on current user
    current_gender = current_user.profile.gender
    current_city = current_user.addresses[0].city.name if current_user.addresses and current_user.addresses[0].city else None

    other_users = (
        User.query
        .join(Profile)
        .join(Address)
        .join(City)
        .filter(
            User.id != current_user.id,
            Profile.gender != current_gender,
            City.name == current_city
        )
        .all()
    )

    # ✅ Use the correct profile_score function (pass user being viewed)
    profile_score = calculate_profile_completeness(user)

    return render_template(
        'my_profile.html',  # Use SAME template for all profiles
        user=user,
        profile=profile,
        profile_score=profile_score,
        profile_images=profile_images,
        addresses=addresses,
        educations=educations,
        professional_details=professional_details,
        family_members=family_members,
        alternate_phones=alternate_phones,
        other_users=other_users,
        viewed_by_users=viewed_by_users,
        is_own_profile=is_own_profile
    )


@app.route("/family")
@login_required
def family():
    categorized = {}
    no_brother = getattr(current_user.profile, 'no_brother', False)
    no_sister = getattr(current_user.profile, 'no_sister', False)

    # Get current user's FamilyDetails
    person = FamilyDetails.query.filter_by(user_id=current_user.id).first()

    # Load all categories and their relation types
    categories = RelationCategory.query.order_by(RelationCategory.name).all()

    for category in categories:
        categorized[category.name] = {}
        # Get relation types for this category
        rel_types = RelationType.query.filter_by(category_id=category.id).order_by(RelationType.name).all()
        for rel_type in rel_types:
            rel_name = rel_type.name
            if rel_name == "Brother" and no_brother:
                continue
            if rel_name == "Sister" and no_sister:
                continue

            relation_entry = None
            if person:
                # Find FamilyRelation for current user and this relation type
                relation_entry = (
                    FamilyRelation.query
                    .filter_by(person_id=person.id, relation_type=rel_name)
                    .join(FamilyDetails, FamilyRelation.related_person_id == FamilyDetails.id)
                    .filter(FamilyDetails.user_id == current_user.id)
                    .first()
                )

            if relation_entry:
                categorized[category.name][rel_name] = {"member": relation_entry.related_person, "relation": rel_name}
            else:
                categorized[category.name][rel_name] = {"member": None, "relation": rel_name}

    return render_template("family.html", user=current_user, categorized=categorized)


@app.route("/family/edit", methods=["GET", "POST"])
@login_required
def edit_or_add_family():
    member_id = request.args.get("member_id")
    # Use "relation" from GET query param or "relation_type" from POST form
    relation_type = request.form.get("relation_type") if request.method == "POST" else request.args.get("relation")

    member = None
    address = None
    member_relation = None

    if member_id:
        member = FamilyDetails.query.get_or_404(member_id)
        if member.address_id:
            address = Address.query.get(member.address_id)

        # Fetch the FamilyRelation linking current user's FamilyDetails to this member
        person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
        if person:
            member_relation = FamilyRelation.query.filter_by(
                person_id=person.id,
                related_person_id=member.id
            ).first()
            if member_relation and request.method == "GET":
                # Prefill relation_type from DB only on GET request
                relation_type = member_relation.relation_type

    profile = current_user.profile

    # Fetch cities, states, countries for dropdowns
    cities = City.query.all()
    states = State.query.all()
    countries = Country.query.all()

    if request.method == "POST":
        # Handle no brother/sister flags explicitly
        if "no_brother" in request.form:
            profile.no_brother = True
            person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
            if person:
                FamilyRelation.query.filter_by(person_id=person.id, relation_type="Brother").delete()
            db.session.commit()
            flash("Marked as having no brothers.", "success")
            return redirect(url_for("family"))

        if "no_sister" in request.form:
            profile.no_sister = True
            person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
            if person:
                FamilyRelation.query.filter_by(person_id=person.id, relation_type="Sister").delete()
            db.session.commit()
            flash("Marked as having no sisters.", "success")
            return redirect(url_for("family"))

        # Validate relation_type presence
        relation_type = request.form.get("relation_type")
        if not relation_type:
            flash("Relation type is required.", "danger")
            return redirect(request.url)

        # Extract address data safely
        try:
            addr_data = {
                "user_id": current_user.id,
                "address1": request.form.get("address") or "",
                "address2": request.form.get("address2") or "",
                "address3": request.form.get("address3") or "",
                "city_id": int(request.form.get("city_id")),
                "state_id": int(request.form.get("state_id")),
                "country_id": int(request.form.get("country_id")),
                "zipcode": request.form.get("zipcode") or "",
                "tag": "family_member"
            }
        except (ValueError, TypeError):
            flash("Please select valid city, state, and country.", "danger")
            return redirect(request.url)

        if member:
            # Update existing member fields
            member.first_name = request.form.get("first_name")
            member.last_name = request.form.get("last_name")
            member.contact_number = request.form.get("contact_number")
            member.email = request.form.get("email")
            member.age = request.form.get("age")
            member.occupation = request.form.get("occupation")
            member.marital_status = request.form.get("marital_status")

            # Update or create Address
            if member.address_id and address:
                for key, value in addr_data.items():
                    setattr(address, key, value)
            else:
                new_address = Address(**addr_data)
                db.session.add(new_address)
                db.session.flush()
                member.address_id = new_address.id

            db.session.commit()
            flash("Family member updated successfully!", "success")

        else:
            # Create new member
            new_member = FamilyDetails(
                user_id=current_user.id,
                first_name=request.form.get("first_name"),
                last_name=request.form.get("last_name"),
                contact_number=request.form.get("contact_number"),
                email=request.form.get("email"),
                age=request.form.get("age"),
                occupation=request.form.get("occupation"),
                marital_status=request.form.get("marital_status"),
            )

            new_address = Address(**addr_data)
            db.session.add(new_address)
            db.session.flush()
            new_member.address_id = new_address.id

            db.session.add(new_member)
            db.session.commit()

            # Link FamilyRelation
            person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
            if person:
                relation = FamilyRelation(
                    person_id=person.id,
                    related_person_id=new_member.id,
                    relation_type=relation_type
                )
                db.session.add(relation)
                db.session.commit()

            flash("Family member added successfully!", "success")

        return redirect(url_for("family"))

    # Query relation types for dropdown
    relation_types = RelationType.query.all()

    # GET request falls here to render form
    return render_template(
        "family_form.html",
        user=current_user,
        member=member,
        address=address,
        relation_type=relation_type,
        relation_types=relation_types,  # <--- add this
        cities=cities,
        states=states,
        member_relation=member_relation,
        countries=countries,
    )


@app.route("/family/delete/<int:member_id>", methods=["POST"])
@login_required
def delete_family(member_id):
    member = FamilyDetails.query.get_or_404(member_id)

    if member.user_id != current_user.id:
        flash("Unauthorized attempt to delete family member.", "danger")
        return redirect(url_for("family"))

    try:
        # Delete FamilyRelation entries where this member is person or related_person
        FamilyRelation.query.filter(
            (FamilyRelation.person_id == member.id) | (FamilyRelation.related_person_id == member.id)
        ).delete(synchronize_session=False)

        db.session.delete(member)
        db.session.commit()
        flash("Family member deleted successfully!", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while deleting the member.", "danger")

    return redirect(url_for("family"))


@app.route('/language', methods=['GET', 'POST'])
@login_required
def language():
    user = current_user
    user_languages = Language.query.filter_by(user_id=user.id).all()

    if request.method == 'POST':
        action = request.form.get('action')
        lang_id = request.form.get('language_id', type=int)

        # ADD Language
        if action == 'add':
            name = request.form.get('name', '').strip()
            proficiency = request.form.get('proficiency', '').strip()
            certification = request.form.get('certification', '').strip()
            notes = request.form.get('notes', '').strip()

            if not name:
                flash('Language name is required.', 'danger')
                return redirect(url_for('language'))

            new_lang = Language(
                user_id=user.id,
                name=name,
                proficiency=proficiency if proficiency else None,
                certification=certification if certification else None,
                notes=notes if notes else None
            )
            db.session.add(new_lang)
            db.session.commit()
            flash('Language added successfully.', 'success')
            return redirect(url_for('language'))

        # EDIT Language
        elif action == 'edit' and lang_id:
            language = Language.query.filter_by(id=lang_id, user_id=user.id).first()
            if language:
                language.name = request.form.get('name', '').strip()
                language.proficiency = request.form.get('proficiency', '').strip()
                language.certification = request.form.get('certification', '').strip()
                language.notes = request.form.get('notes', '').strip()
                db.session.commit()
                flash('Language updated.', 'success')
            else:
                flash('Language not found.', 'danger')
            return redirect(url_for('language'))

        # DELETE Language
        elif action == 'delete' and lang_id:
            language = Language.query.filter_by(id=lang_id, user_id=user.id).first()
            if language:
                db.session.delete(language)
                db.session.commit()
                flash('Language deleted.', 'success')
            else:
                flash('Language not found.', 'danger')
            return redirect(url_for('language'))

    return render_template(
        'language.html',
        user=user,
        user_languages=user_languages
    )

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_profiles():
    form = ProfileSearchForm(request.args)

    # Current user’s profile for same caste filter
    current_profile = Profile.query.filter_by(user_id=current_user.id).first()

    # Base query joining required tables
    query = User.query \
        .join(Profile) \
        .outerjoin(Address) \
        .outerjoin(City, Address.city_id == City.id) \
        .outerjoin(ProfessionalDetails) \
        .outerjoin(Education)

    # 🔍 Keyword filter: name, city, company, etc.
    if form.keyword.data:
        keyword = f"%{form.keyword.data}%"
        query = query.filter(or_(
            User.first_name.ilike(keyword),
            User.last_name.ilike(keyword),
            City.name.ilike(keyword),
            ProfessionalDetails.company_name.ilike(keyword),
            ProfessionalDetails.occupation.ilike(keyword),
            Profile.birth_city.ilike(keyword)
        ))

    # 🧑 Gender
    if form.gender.data:
        query = query.filter(Profile.gender == form.gender.data)

    # 🎂 Age filter from DOB string
    def calculate_birth_year(age):
        return date.today().year - age

    if form.min_age.data:
        min_year = calculate_birth_year(form.min_age.data)
        query = query.filter(Profile.date_of_birth <= f"{min_year}-12-31")

    if form.max_age.data:
        max_year = calculate_birth_year(form.max_age.data)
        query = query.filter(Profile.date_of_birth >= f"{max_year}-01-01")

    # 🧬 Caste
    if form.caste.data:
        query = query.filter(Profile.bio.ilike(f"%{form.caste.data}%"))

    if form.same_caste_only.data and current_profile:
        query = query.filter(Profile.bio.ilike(f"%{current_profile.bio}%"))

    # 🛐 Religion — assuming it's stored in bio or a similar field
    if form.religion.data:
        query = query.filter(Profile.bio.ilike(f"%{form.religion.data}%"))

    # 🎓 Education (degree or institution or specialization match)
    if form.education.data:
        edu_kw = f"%{form.education.data}%"
        query = query.filter(or_(
            Education.degree.ilike(edu_kw),
            Education.institution.ilike(edu_kw),
            Education.specialization.ilike(edu_kw)
        ))

    # 💍 Marital status (from FamilyDetails model, or if in Profile.bio)
    if form.marital_status.data:
        query = query.filter(Profile.bio.ilike(f"%{form.marital_status.data}%"))

    # 🌆 City
    if form.city.data:
        query = query.filter(City.name.ilike(f"%{form.city.data}%"))

    # ❌ Exclude current user
    query = query.filter(User.id != current_user.id)

    # Execute query
    results = query.all()

    return render_template("search_results.html", form=form, results=results, user=current_user, show_filters=True)



#Logout
@app.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have logged off successfully! Visit again...")
    return redirect(url_for('login'))



if __name__ == "__main__":
    with app.app_context():
      db.create_all()
    app.run(debug=True)