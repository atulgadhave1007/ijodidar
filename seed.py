"""
seed.py — Run once after flask db upgrade to populate:
  - India states & cities (35 states/UTs, 300+ cities)
  - Relation categories & types (10 categories, 42 types)
  - Default membership plans (Free / Silver / Gold / Platinum)
  - First admin user (optional — only if ADMIN_EMAIL env var set)

Usage:
    source venv/bin/activate          # Mac/Linux
    venv\\Scripts\\activate             # Windows
    python seed.py

    # To also create admin user:
    ADMIN_EMAIL=you@email.com ADMIN_PASSWORD=yourpass python seed.py
"""
import os
os.environ.setdefault('FLASK_ENV', 'development')

from wsgi import app
from app import db
from app.models import (Country, State, City, RelationCategory, RelationType,
                        MembershipPlan, User, UserSubscription)


# ── Location ──────────────────────────────────────────────────────────────
def seed_location():
    print("Seeding location data...")
    if Country.query.count() > 0:
        print("  Location data already seeded. Skipping.")
        return

    india = Country(name='India')
    db.session.add(india)
    db.session.flush()

    states_cities = {
        'Maharashtra':      ['Mumbai','Pune','Nagpur','Nashik','Aurangabad','Solapur',
                             'Kolhapur','Thane','Navi Mumbai','Amravati','Latur',
                             'Jalgaon','Ahmednagar','Akola','Chandrapur'],
        'Delhi':            ['New Delhi','Delhi','Dwarka','Rohini','Noida',
                             'Greater Noida','Gurugram','Faridabad'],
        'Karnataka':        ['Bengaluru','Mysuru','Mangaluru','Hubballi','Belagavi',
                             'Tumakuru','Davanagere','Ballari','Vijayapura','Shivamogga'],
        'Tamil Nadu':       ['Chennai','Coimbatore','Madurai','Tiruchirappalli','Salem',
                             'Tirunelveli','Vellore','Erode','Tiruppur','Dindigul','Thanjavur'],
        'Gujarat':          ['Ahmedabad','Surat','Vadodara','Rajkot','Bhavnagar',
                             'Jamnagar','Gandhinagar','Junagadh','Anand','Mehsana'],
        'Rajasthan':        ['Jaipur','Jodhpur','Udaipur','Kota','Ajmer','Bikaner',
                             'Alwar','Sikar','Bharatpur','Sri Ganganagar'],
        'Uttar Pradesh':    ['Lucknow','Kanpur','Agra','Varanasi','Prayagraj','Ghaziabad',
                             'Meerut','Noida','Bareilly','Aligarh','Moradabad','Gorakhpur','Mathura'],
        'West Bengal':      ['Kolkata','Howrah','Durgapur','Asansol','Siliguri',
                             'Bardhaman','Malda','Kharagpur','Haldia'],
        'Andhra Pradesh':   ['Visakhapatnam','Vijayawada','Guntur','Nellore','Kurnool',
                             'Tirupati','Rajahmundry','Kakinada','Anantapur'],
        'Telangana':        ['Hyderabad','Warangal','Nizamabad','Karimnagar',
                             'Khammam','Ramagundam','Secunderabad'],
        'Kerala':           ['Thiruvananthapuram','Kochi','Kozhikode','Thrissur',
                             'Kollam','Palakkad','Alappuzha','Kannur','Kottayam'],
        'Madhya Pradesh':   ['Bhopal','Indore','Gwalior','Jabalpur','Ujjain',
                             'Sagar','Dewas','Satna','Ratlam','Rewa'],
        'Bihar':            ['Patna','Gaya','Bhagalpur','Muzaffarpur','Purnia',
                             'Darbhanga','Bihar Sharif','Arrah','Begusarai'],
        'Odisha':           ['Bhubaneswar','Cuttack','Rourkela','Brahmapur','Sambalpur','Puri','Balasore'],
        'Punjab':           ['Ludhiana','Amritsar','Jalandhar','Patiala','Bathinda','Mohali','Hoshiarpur'],
        'Haryana':          ['Gurugram','Faridabad','Panipat','Ambala','Yamunanagar','Rohtak','Hisar','Karnal'],
        'Himachal Pradesh': ['Shimla','Dharamshala','Solan','Mandi','Kullu','Manali','Baddi'],
        'Uttarakhand':      ['Dehradun','Haridwar','Roorkee','Haldwani','Rishikesh','Kashipur','Rudrapur'],
        'Jharkhand':        ['Ranchi','Jamshedpur','Dhanbad','Bokaro','Deoghar','Hazaribagh'],
        'Chhattisgarh':     ['Raipur','Bhilai','Durg','Bilaspur','Korba','Raigarh','Jagdalpur'],
        'Assam':            ['Guwahati','Silchar','Dibrugarh','Jorhat','Nagaon','Tinsukia','Tezpur'],
        'Goa':              ['Panaji','Margao','Vasco da Gama','Mapusa','Ponda'],
        'Jammu & Kashmir':  ['Srinagar','Jammu','Anantnag','Baramulla','Sopore','Kathua'],
        'Sikkim':           ['Gangtok','Namchi','Gyalshing','Mangan'],
        'Meghalaya':        ['Shillong','Tura','Nongstoin'],
        'Nagaland':         ['Kohima','Dimapur','Mokokchung'],
        'Manipur':          ['Imphal','Thoubal','Kakching'],
        'Tripura':          ['Agartala','Dharmanagar','Udaipur'],
        'Mizoram':          ['Aizawl','Lunglei','Champhai'],
        'Arunachal Pradesh':['Itanagar','Naharlagun','Tawang','Pasighat'],
        'Andaman & Nicobar':['Port Blair'],
        'Chandigarh':       ['Chandigarh'],
        'Puducherry':       ['Puducherry','Karaikal','Mahe'],
        'Ladakh':           ['Leh','Kargil'],
        'Dadra & Nagar Haveli': ['Silvassa'],
        'Daman & Diu':      ['Daman','Diu'],
        'Lakshadweep':      ['Kavaratti'],
    }

    for state_name, cities in states_cities.items():
        s = State(name=state_name, country_id=india.id)
        db.session.add(s)
        db.session.flush()
        for city_name in cities:
            db.session.add(City(name=city_name, state_id=s.id, country_id=india.id))

    db.session.commit()
    total = sum(len(v) for v in states_cities.values())
    print(f"  ✓ India + {len(states_cities)} states + {total} cities")


# ── Relation types ─────────────────────────────────────────────────────────
def seed_relation_types():
    print("Seeding relation types...")
    if RelationCategory.query.count() > 0:
        print("  Relation types already seeded. Skipping.")
        return

    data = {
        'Self':                    ['Self'],
        'Parents':                 ['Father', 'Mother'],
        'Siblings':                ['Brother', 'Sister'],
        'Grandparents':            ['Paternal Grandfather', 'Paternal Grandmother',
                                    'Maternal Grandfather', 'Maternal Grandmother'],
        'Paternal Uncles & Aunts': ['Paternal Uncle (Kaka)', 'Paternal Aunt (Kaki)',
                                    'Paternal Uncle (Mama)', 'Paternal Aunt (Mami)'],
        'Maternal Uncles & Aunts': ['Maternal Uncle (Mama)', 'Maternal Aunt (Mami)',
                                    'Maternal Uncle (Kaka)', 'Maternal Aunt (Kaki)'],
        'Cousins':                 ['Cousin Brother (Paternal)', 'Cousin Sister (Paternal)',
                                    'Cousin Brother (Maternal)', 'Cousin Sister (Maternal)'],
        'In-Laws':                 ['Father-in-law', 'Mother-in-law', 'Brother-in-law',
                                    'Sister-in-law', 'Son-in-law', 'Daughter-in-law'],
        'Children':                ['Son', 'Daughter'],
        'Other':                   ['Other Relative', 'Family Friend'],
    }

    for cat_name, types in data.items():
        cat = RelationCategory(name=cat_name)
        db.session.add(cat)
        db.session.flush()
        for t in types:
            db.session.add(RelationType(name=t, category_id=cat.id))

    db.session.commit()
    total = sum(len(v) for v in data.values())
    print(f"  ✓ {len(data)} categories + {total} relation types")


# ── Membership plans ───────────────────────────────────────────────────────
def seed_plans():
    print("Seeding membership plans...")
    if MembershipPlan.query.count() > 0:
        print("  Plans already seeded. Skipping.")
        return

    plans = [
        dict(name='Free',     price_inr=0,    duration_days=0,
             max_interests=5,  can_message=False, can_view_phone=False, highlighted=False,
             description='Get started — send up to 5 interests, browse all profiles.'),
        dict(name='Silver',   price_inr=499,  duration_days=30,
             max_interests=20, can_message=True,  can_view_phone=False, highlighted=False,
             description='Send 20 interests/month and chat with accepted connections.'),
        dict(name='Gold',     price_inr=999,  duration_days=90,
             max_interests=50, can_message=True,  can_view_phone=True,  highlighted=True,
             description='Most popular — 50 interests, messaging, and view phone numbers.'),
        dict(name='Platinum', price_inr=1999, duration_days=180,
             max_interests=0,  can_message=True,  can_view_phone=True,  highlighted=False,
             description='Unlimited interests, all features, 6-month validity.'),
    ]
    for p in plans:
        db.session.add(MembershipPlan(**p))
    db.session.commit()
    print(f"  ✓ {len(plans)} membership plans (Free / Silver / Gold / Platinum)")


# ── Admin user (optional) ──────────────────────────────────────────────────
def seed_admin_user():
    """
    Creates the first admin user if ADMIN_EMAIL and ADMIN_PASSWORD are set.
    Set them in your .env or as environment variables before running seed.py.

    Example:
        ADMIN_EMAIL=you@email.com ADMIN_PASSWORD=YourPassword python seed.py
    """
    email    = os.environ.get('ADMIN_EMAIL', '').strip()
    password = os.environ.get('ADMIN_PASSWORD', '').strip()
    uname    = os.environ.get('ADMIN_USERNAME', 'admin').strip()
    first    = os.environ.get('ADMIN_FIRSTNAME', 'Admin').strip()
    last     = os.environ.get('ADMIN_LASTNAME',  'iJodidar').strip()

    if not email or not password:
        print("Skipping admin user (set ADMIN_EMAIL + ADMIN_PASSWORD to create one).")
        return

    print(f"Creating admin user: {email}")
    if User.query.filter_by(email=email).first():
        print("  Admin user already exists. Skipping.")
        return

    free_plan = MembershipPlan.query.filter_by(name='Free').first()
    user      = User(
        username   = uname,
        first_name = first,
        last_name  = last,
        email      = email,
        is_verified = True,      # Admin is pre-verified
        is_active_acc = True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if free_plan:
        db.session.add(UserSubscription(
            user_id    = user.id,
            plan_id    = free_plan.id,
            expires_at = None,
            amount_paid = 0,
        ))
    db.session.commit()
    print(f"  ✓ Admin user created — email: {email}")
    print(f"  ✓ Add {email!r} to ADMIN_EMAILS in your .env to grant admin panel access")


# ── Main ──────────────────────────────────────────────────────────────────
def seed_console_ceo():
    """Create the first console CEO account. Set CONSOLE_CEO_EMAIL + CONSOLE_CEO_PASSWORD."""
    from app.models import AdminUser
    email    = os.environ.get('CONSOLE_CEO_EMAIL', '').strip()
    password = os.environ.get('CONSOLE_CEO_PASSWORD', '').strip()
    name     = os.environ.get('CONSOLE_CEO_NAME', 'Platform CEO').strip()

    if not email or not password:
        print("Skipping console CEO (set CONSOLE_CEO_EMAIL + CONSOLE_CEO_PASSWORD).")
        return

    if AdminUser.query.filter_by(email=email).first():
        print(f"  Console CEO already exists: {email}")
        return

    ceo = AdminUser(name=name, email=email, role='ceo')
    ceo.set_password(password)
    db.session.add(ceo)
    db.session.commit()
    print(f"  ✓ Console CEO created: {email}")
    print(f"  ✓ Login at: http://localhost:5000/console/login")


if __name__ == '__main__':
    with app.app_context():
        seed_location()
        seed_relation_types()
        seed_plans()
        seed_admin_user()
        seed_console_ceo()
        print("\n✅ All seed data inserted successfully!")
        print("\nNext steps:")
        print("  1. python wsgi.py         — start the app")
        print("  2. Open http://localhost:5000")
        print("  3. Register or log in with your admin email")
        print("  4. Admin panel: http://localhost:5000/admin/")
