"""Marshmallow serialization schemas for the REST API."""
from marshmallow import Schema, fields, pre_load


class UserSchema(Schema):
    id             = fields.Int(dump_only=True)
    username       = fields.Str(dump_only=True)
    first_name     = fields.Str(dump_only=True)
    last_name      = fields.Str(dump_only=True)
    email          = fields.Email(dump_only=True)
    phone_verified = fields.Bool(dump_only=True)
    plan_name      = fields.Str(dump_only=True)
    created_at     = fields.DateTime(dump_only=True)


class ProfileCardSchema(Schema):
    """Compact schema for feed and search results."""
    id             = fields.Int()
    username       = fields.Str()
    first_name     = fields.Str()
    age            = fields.Method('get_age')
    city           = fields.Method('get_city')
    religion       = fields.Method('get_religion')
    caste          = fields.Method('get_caste')
    occupation     = fields.Method('get_occupation')
    income_range   = fields.Method('get_income_range')
    photo_url      = fields.Method('get_photo_url')
    thumb_url      = fields.Method('get_thumb_url')
    match_score    = fields.Int(load_default=0)
    trust_tier     = fields.Method('get_trust_tier')
    trust_label    = fields.Method('get_trust_label')
    is_spotlight   = fields.Method('get_is_spotlight')
    last_active_at = fields.DateTime()
    plan_name      = fields.Str()

    def get_age(self, obj):
        from datetime import date
        p = obj.profile
        if not p:
            return None
        dob = p.dob or None
        if not dob and p.date_of_birth:
            try:
                from datetime import datetime
                dob = datetime.strptime(p.date_of_birth, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        if not dob:
            return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_city(self, obj):
        if obj.addresses:
            addr = obj.addresses[0]
            if addr.city:
                return addr.city.name
        return None

    def get_religion(self, obj):
        return obj.profile.religion if obj.profile else None

    def get_caste(self, obj):
        return obj.profile.caste if obj.profile else None

    def get_occupation(self, obj):
        if obj.professional_details:
            return obj.professional_details[0].occupation
        return None

    def get_income_range(self, obj):
        if obj.professional_details:
            lpa = obj.professional_details[0].income_lpa
            if lpa is not None:
                if lpa < 3:   return 'Below 3 LPA'
                if lpa < 5:   return '3–5 LPA'
                if lpa < 10:  return '5–10 LPA'
                if lpa < 15:  return '10–15 LPA'
                if lpa < 25:  return '15–25 LPA'
                if lpa < 50:  return '25–50 LPA'
                return '50+ LPA'
        return None

    def get_photo_url(self, obj):
        for img in obj.profile_images:
            if img.is_primary:
                return img.image_url
        return obj.profile_images[0].image_url if obj.profile_images else None

    def get_thumb_url(self, obj):
        for img in obj.profile_images:
            if img.is_primary:
                return img.thumb_url or img.image_url
        return None

    def get_trust_tier(self, obj):
        score = 0
        if obj.is_verified:      score += 1
        if obj.phone_verified:   score += 1
        if obj.profile and obj.profile.id_verified: score += 1
        if score == 0: return 'basic'
        if score == 1: return 'verified'
        if score == 2: return 'trusted'
        return 'elite'

    def get_trust_label(self, obj):
        tier = self.get_trust_tier(obj)
        labels = {'basic': 'Basic', 'verified': 'Verified',
                  'trusted': 'Trusted', 'elite': 'Elite'}
        return labels.get(tier, 'Basic')

    def get_is_spotlight(self, obj):
        from datetime import datetime
        if not obj.profile:
            return False
        if not obj.profile.is_spotlight:
            return False
        exp = obj.profile.spotlight_expires_at
        if exp and exp < datetime.utcnow():
            return False
        return True


class ProfileFullSchema(ProfileCardSchema):
    """Extended schema for profile detail view."""
    last_name      = fields.Str()
    height         = fields.Method('get_height')
    weight         = fields.Int(attribute='profile.weight')
    bio            = fields.Str(attribute='profile.bio')
    sub_caste      = fields.Method('get_sub_caste')
    gotra          = fields.Method('get_gotra')
    marital_status = fields.Method('get_marital_status')
    mother_tongue  = fields.Method('get_mother_tongue')
    diet           = fields.Method('get_diet')
    smoking        = fields.Method('get_smoking')
    drinking       = fields.Method('get_drinking')
    family_type    = fields.Method('get_family_type')
    is_nri         = fields.Method('get_is_nri')
    nri_country    = fields.Method('get_nri_country')
    nakshatra      = fields.Method('get_nakshatra')
    rashi          = fields.Method('get_rashi')
    manglik        = fields.Method('get_manglik')
    hobbies        = fields.Method('get_hobbies')
    photos         = fields.Method('get_photos')
    educations     = fields.Method('get_educations')
    professional   = fields.Method('get_professional')
    email_verified = fields.Bool(attribute='is_verified')

    def _p(self, obj):
        return obj.profile

    def get_height(self, obj):
        return self._p(obj).height if self._p(obj) else None

    def get_sub_caste(self, obj):
        return self._p(obj).sub_caste if self._p(obj) else None

    def get_gotra(self, obj):
        return self._p(obj).gotra if self._p(obj) else None

    def get_marital_status(self, obj):
        return self._p(obj).marital_status if self._p(obj) else None

    def get_mother_tongue(self, obj):
        return self._p(obj).mother_tongue if self._p(obj) else None

    def get_diet(self, obj):
        return self._p(obj).diet if self._p(obj) else None

    def get_smoking(self, obj):
        return self._p(obj).smoking if self._p(obj) else None

    def get_drinking(self, obj):
        return self._p(obj).drinking if self._p(obj) else None

    def get_family_type(self, obj):
        return self._p(obj).family_type if self._p(obj) else None

    def get_is_nri(self, obj):
        return self._p(obj).is_nri if self._p(obj) else False

    def get_nri_country(self, obj):
        return self._p(obj).nri_country if self._p(obj) else None

    def get_nakshatra(self, obj):
        return self._p(obj).birth_nakshatra if self._p(obj) else None

    def get_rashi(self, obj):
        return self._p(obj).birth_rashi if self._p(obj) else None

    def get_manglik(self, obj):
        return self._p(obj).manglik if self._p(obj) else None

    def get_hobbies(self, obj):
        import json
        p = self._p(obj)
        if not p or not p.hobbies:
            return []
        try:
            return json.loads(p.hobbies)
        except (ValueError, TypeError):
            return []

    def get_photos(self, obj):
        return [
            {'id': img.id, 'url': img.image_url,
             'thumb': img.thumb_url, 'is_primary': img.is_primary}
            for img in obj.profile_images
        ]

    def get_educations(self, obj):
        return [
            {'degree': e.degree, 'specialization': e.specialization,
             'university': e.university, 'year': e.year_of_passing}
            for e in obj.educations
        ]

    def get_professional(self, obj):
        if not obj.professional_details:
            return None
        pd = obj.professional_details[0]
        return {
            'occupation': pd.occupation,
            'company': pd.company_name,
            'designation': pd.designation,
            'income_lpa': pd.income_lpa,
            'employment_type': pd.employment_type,
        }


user_schema        = UserSchema()
profile_card_schema = ProfileCardSchema()
profile_cards_schema = ProfileCardSchema(many=True)
profile_full_schema  = ProfileFullSchema()
