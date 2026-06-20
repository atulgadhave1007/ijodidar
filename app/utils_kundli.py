"""
utils_kundli.py — Vedic Astrology Guna Milan (Ashtakoot matching) engine.

Implements the 8-koot (factor) matching used in Hindu matrimony:
1. Varna     — caste/spiritual level (max 1)
2. Vashya    — dominance/attraction (max 2)
3. Tara      — birth star compatibility (max 3)
4. Yoni      — nature/instinct (max 4)
5. Graha Maitri — planetary friendship (max 5)
6. Gana      — temperament (max 6)
7. Bhakoot   — emotional/financial compatibility (max 7)
8. Nadi      — health/progeny (max 8)
Total: 36 gunas

Score >= 18 → Acceptable match
Score >= 24 → Good match
Score >= 30 → Excellent match
"""

# ── Nakshatra data ────────────────────────────────────────────────────────
# Each nakshatra: (rashi, gana, nadi, varna, yoni_animal, yoni_gender, vashya)
NAKSHATRAS = [
    # (name, rashi, gana, nadi[CORRECTED], varna, yoni, yoni_m/f)
    # Nadi corrected per Muhurta Chintamani + Brihat Parashara Hora Shastra
    # Standard: Adi=Ashwini,Ardra,Punarvasu,Uttara Phalguni,Hasta,Jyeshtha,
    #                  Uttara Ashadha,Shatabhisha,Purva Bhadrapada
    #           Madhya=Bharani,Mrigashira,Pushya,Purva Phalguni,Chitra,Anuradha,
    #                  Purva Ashadha,Dhanishtha,Uttara Bhadrapada
    #           Antya=Krittika,Rohini,Ashlesha,Magha,Swati,Vishakha,
    #                 Mula,Shravana,Revati
    ("Ashwini",          "Mesha",     "Deva",     "Adi",    "Brahmin",   "Ashwa",    "M"),
    ("Bharani",          "Mesha",     "Manushya", "Madhya", "Mleccha",   "Gaja",     "M"),
    ("Krittika",         "Mesha",     "Rakshasa", "Antya",  "Brahmin",   "Mesha",    "F"),
    ("Rohini",           "Vrishabha", "Manushya", "Antya",  "Shudra",    "Sarpa",    "M"),
    ("Mrigashira",       "Vrishabha", "Deva",     "Madhya", "Vaishya",   "Sarpa",    "F"),
    ("Ardra",            "Mithuna",   "Manushya", "Adi",    "Mleccha",   "Shwana",   "F"),
    ("Punarvasu",        "Mithuna",   "Deva",     "Adi",    "Vaishya",   "Marjara",  "F"),
    ("Pushya",           "Karka",     "Deva",     "Madhya", "Kshatriya", "Mesha",    "M"),
    ("Ashlesha",         "Karka",     "Rakshasa", "Antya",  "Mleccha",   "Marjara",  "M"),
    ("Magha",            "Simha",     "Rakshasa", "Antya",  "Shudra",    "Mushika",  "M"),
    ("Purva Phalguni",   "Simha",     "Manushya", "Madhya", "Brahmin",   "Mushika",  "F"),
    ("Uttara Phalguni",  "Simha",     "Manushya", "Adi",    "Kshatriya", "Go",       "M"),
    ("Hasta",            "Kanya",     "Deva",     "Adi",    "Vaishya",   "Mahisha",  "F"),
    ("Chitra",           "Kanya",     "Rakshasa", "Madhya", "Kshatriya", "Vyaghra",  "F"),
    ("Swati",            "Tula",      "Deva",     "Antya",  "Mleccha",   "Mahisha",  "M"),
    ("Vishakha",         "Tula",      "Rakshasa", "Antya",  "Mleccha",   "Vyaghra",  "M"),
    ("Anuradha",         "Vrischika", "Deva",     "Madhya", "Shudra",    "Mriga",    "F"),
    ("Jyeshtha",         "Vrischika", "Rakshasa", "Adi",    "Vaishya",   "Mriga",    "M"),
    ("Mula",             "Dhanu",     "Rakshasa", "Antya",  "Mleccha",   "Shwana",   "M"),
    ("Purva Ashadha",    "Dhanu",     "Manushya", "Madhya", "Brahmin",   "Vanara",   "M"),
    ("Uttara Ashadha",   "Dhanu",     "Manushya", "Adi",    "Kshatriya", "Nakula",   "M"),
    ("Shravana",         "Makara",    "Deva",     "Antya",  "Mleccha",   "Vanara",   "F"),
    ("Dhanishtha",       "Makara",    "Rakshasa", "Madhya", "Shudra",    "Simha",    "F"),
    ("Shatabhisha",      "Kumbha",    "Rakshasa", "Adi",    "Mleccha",   "Ashwa",    "F"),
    ("Purva Bhadrapada", "Kumbha",    "Manushya", "Adi",    "Brahmin",   "Simha",    "M"),
    ("Uttara Bhadrapada","Meena",     "Manushya", "Madhya", "Kshatriya", "Go",       "F"),
    ("Revati",           "Meena",     "Deva",     "Antya",  "Shudra",    "Gaja",     "F"),
]

NAK_MAP = {n[0]: n for n in NAKSHATRAS}


def _nak(name):
    """Get nakshatra data or None."""
    if not name:
        return None
    # Fuzzy match
    for nak in NAKSHATRAS:
        if name.lower().strip() in nak[0].lower():
            return nak
    return None


def calculate_guna_milan(nak1_name, nak2_name):
    """
    Calculate Ashtakoot Guna Milan between two nakshatras.
    Returns dict: {score: int(0-36), koots: {koot: (got, max)}, interpretation: str}
    """
    n1 = _nak(nak1_name)
    n2 = _nak(nak2_name)

    if not n1 or not n2:
        return {
            'score': None,
            'koots': {},
            'interpretation': 'Birth nakshatra not available for one or both profiles.',
            'available': False,
        }

    score = 0
    koots = {}

    # 1. Varna (max 1) — groom varna >= bride varna
    varna_order = ['Brahmin', 'Kshatriya', 'Vaishya', 'Shudra', 'Mleccha']
    v1 = varna_order.index(n1[4]) if n1[4] in varna_order else 4
    v2 = varna_order.index(n2[4]) if n2[4] in varna_order else 4
    varna_pts = 1 if v1 <= v2 else 0
    score += varna_pts
    koots['Varna'] = (varna_pts, 1)

    # 2. Vashya (max 2) — dominance/attraction by zodiac nature group
    # Standard Vedic Vashya groups by Rashi
    VASHYA_GROUPS = {
        'Mesha': 'Chatushpada', 'Vrishabha': 'Chatushpada',
        'Mithuna': 'Manava',    'Karka': 'Jalachar',
        'Simha': 'Vanchar',     'Kanya': 'Manava',
        'Tula': 'Manava',       'Vrischika': 'Vanchar',
        'Dhanu': 'Chatushpada', 'Makara': 'Jalachar',
        'Kumbha': 'Manava',     'Meena': 'Jalachar',
    }
    VASHYA_CONTROL = {   # (controller, controlled) pairs
        ('Chatushpada', 'Jalachar'), ('Manava', 'Chatushpada'),
        ('Vanchar', 'Manava'),       ('Jalachar', 'Vanchar'),
    }
    vg1 = VASHYA_GROUPS.get(n1[1], 'Other')
    vg2 = VASHYA_GROUPS.get(n2[1], 'Other')
    if vg1 == vg2:
        vashya_pts = 2
    elif (vg1, vg2) in VASHYA_CONTROL or (vg2, vg1) in VASHYA_CONTROL:
        vashya_pts = 1
    else:
        vashya_pts = 0
    score += vashya_pts
    koots['Vashya'] = (vashya_pts, 2)

    # 3. Tara (max 3) — count from bride's nakshatra to groom's and divide by 9
    i1 = NAKSHATRAS.index(n1)
    i2 = NAKSHATRAS.index(n2)
    tara_diff = ((i2 - i1) % 27) + 1
    tara_koot  = tara_diff % 9
    favorable  = tara_koot in (1, 3, 5, 7)  # odd = favorable
    tara_pts   = 3 if favorable else 0
    score += tara_pts
    koots['Tara'] = (tara_pts, 3)

    # 4. Yoni (max 4) — animal instinct compatibility
    yoni_pairs_hostile = {
        ('Ashwa', 'Mahisha'), ('Gaja', 'Simha'), ('Mesha', 'Vanara'),
        ('Sarpa', 'Nakula'),  ('Shwana', 'Mriga'), ('Marjara', 'Mushika'),
        ('Go', 'Vyaghra'),    ('Vanara', 'Ashwa'), ('Nakula', 'Sarpa'),
    }
    y1, y2 = n1[5], n2[5]
    if y1 == y2:
        yoni_pts = 4
    elif (y1, y2) in yoni_pairs_hostile or (y2, y1) in yoni_pairs_hostile:
        yoni_pts = 0
    else:
        yoni_pts = 2
    score += yoni_pts
    koots['Yoni'] = (yoni_pts, 4)

    # 5. Graha Maitri (max 5) — planetary friendship (simplified by rashi lords)
    rashi_lords = {
        'Mesha': 'Mars', 'Vrishabha': 'Venus', 'Mithuna': 'Mercury',
        'Karka': 'Moon', 'Simha': 'Sun', 'Kanya': 'Mercury',
        'Tula': 'Venus', 'Vrischika': 'Mars', 'Dhanu': 'Jupiter',
        'Makara': 'Saturn', 'Kumbha': 'Saturn', 'Meena': 'Jupiter',
    }
    friendly = {
        'Sun': ['Moon', 'Mars', 'Jupiter'],
        'Moon': ['Sun', 'Mercury'],
        'Mars': ['Sun', 'Moon', 'Jupiter'],
        'Mercury': ['Sun', 'Venus'],
        'Jupiter': ['Sun', 'Moon', 'Mars'],
        'Venus': ['Mercury', 'Saturn'],
        'Saturn': ['Mercury', 'Venus'],
    }
    l1 = rashi_lords.get(n1[1], '')
    l2 = rashi_lords.get(n2[1], '')
    enemy = {
        'Sun': ['Venus', 'Saturn'], 'Moon': [],
        'Mars': ['Mercury'], 'Mercury': ['Moon'],
        'Jupiter': ['Mercury', 'Venus'], 'Venus': ['Sun', 'Moon'],
        'Saturn': ['Sun', 'Moon', 'Mars'],
    }
    if l1 == l2:
        gm_pts = 5
    elif l1 in friendly.get(l2, []) and l2 in friendly.get(l1, []):
        gm_pts = 5   # mutual friends
    elif l1 in friendly.get(l2, []) or l2 in friendly.get(l1, []):
        gm_pts = 4   # one-way friend
    elif l1 in enemy.get(l2, []) or l2 in enemy.get(l1, []):
        gm_pts = 1   # one enemy (was 0 — now correctly 1)
    else:
        gm_pts = 3   # neutral (was 0 — now correctly 3)
    score += gm_pts
    koots['Graha Maitri'] = (gm_pts, 5)

    # 6. Gana (max 6) — temperament
    g1, g2 = n1[2], n2[2]
    if g1 == g2:
        gana_pts = 6
    elif (g1 == 'Deva' and g2 == 'Manushya') or (g1 == 'Manushya' and g2 == 'Deva'):
        gana_pts = 5
    elif g1 == 'Rakshasa' or g2 == 'Rakshasa':
        gana_pts = 0
    else:
        gana_pts = 3
    score += gana_pts
    koots['Gana'] = (gana_pts, 6)

    # 7. Bhakoot (max 7) — moon sign distance
    rashis = ['Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya',
              'Tula','Vrischika','Dhanu','Makara','Kumbha','Meena']
    r1 = rashis.index(n1[1]) if n1[1] in rashis else 0
    r2 = rashis.index(n2[1]) if n2[1] in rashis else 0
    diff = abs(r1 - r2)
    inauspicious = diff in (6, 8, 9, 5, 12)
    bhakoot_pts = 0 if inauspicious else 7
    score += bhakoot_pts
    koots['Bhakoot'] = (bhakoot_pts, 7)

    # 8. Nadi (max 8) — most critical, same nadi = 0 points
    nd1, nd2 = n1[3], n2[3]
    nadi_pts = 0 if nd1 == nd2 else 8
    score += nadi_pts
    koots['Nadi'] = (nadi_pts, 8)

    # Interpretation
    if score >= 30:
        interpretation = 'Excellent match (30+ gunas). Highly compatible.'
    elif score >= 24:
        interpretation = 'Good match (24+ gunas). Compatible with minor differences.'
    elif score >= 18:
        interpretation = 'Acceptable match (18+ gunas). Manageable compatibility.'
    else:
        interpretation = f'Low compatibility ({score} gunas). Consider family consultation before proceeding.'

    # Nadi dosha warning (same nadi = serious issue in many traditions)
    if nadi_pts == 0:
        interpretation += ' ⚠️ Nadi Dosha present — same nadi. Many astrologers advise caution.'

    return {
        'score':          score,
        'out_of':         36,
        'koots':          koots,
        'interpretation': interpretation,
        'available':      True,
        'nadi_dosha':     nadi_pts == 0,
    }


# ── Sapinda / Gotra check ─────────────────────────────────────────────────
def check_gotra_compatibility(gotra1, gotra2, religion1='Hindu', religion2='Hindu'):
    """
    Returns (compatible: bool, message: str).
    Sapinda rule: same gotra = not compatible for Brahmin/Hindu matches.
    """
    if not gotra1 or not gotra2:
        return True, 'Gotra not available for one or both profiles.'
    if religion1 not in ('Hindu',) or religion2 not in ('Hindu',):
        return True, 'Gotra matching applies primarily to Hindu profiles.'
    if gotra1.strip().lower() == gotra2.strip().lower():
        return False, (
            f'Both profiles have the same Gotra ({gotra1}). '
            'According to Sapinda rules observed in many Brahmin and Hindu communities, '
            'same-Gotra marriages are not recommended. Please consult your family.'
        )
    return True, f'Different Gotras ({gotra1} × {gotra2}). Compatible per Sapinda rules.'


# ── Marathi sub-castes ────────────────────────────────────────────────────
MARATHI_SUB_CASTES = [
    # Major community groups
    ('96 Kuli Maratha',   'Maratha'),
    ('Deshastha Brahmin', 'Brahmin'),
    ('Kokanastha (CKP)',  'Brahmin'),
    ('Karhade Brahmin',   'Brahmin'),
    ('Saraswat Brahmin',  'Brahmin'),
    ('Kunbi Maratha',     'Maratha'),
    ('Koli',              'OBC'),
    ('Mali',              'OBC'),
    ('Dhangar',           'OBC'),
    ('Mahar / Neo-Buddhist', 'SC'),
    ('Chambhar',          'SC'),
    ('Matang',            'SC'),
    ('Teli',              'OBC'),
    ('Agri',              'OBC'),
    ('Bhandari',          'OBC'),
    ('Vanjari',           'OBC'),
    ('Vani / Vaishya',    'Vaishya'),
    ('Jain Digambar',     'Jain'),
    ('Jain Shwetambar',   'Jain'),
    ('Kshatriya Maratha', 'Maratha'),
    ('Sonkoli',           'OBC'),
    ('Pardeshi',          'Other'),
    ('Shimpis',           'OBC'),
    ('Nhavi',             'OBC'),
    ('Sutar',             'OBC'),
    ('Lohar',             'OBC'),
    ('Kumbhar',           'OBC'),
    ('Gavli',             'OBC'),
    ('Gurav',             'OBC'),
    ('Other Marathi',     'Other'),
]


# ── Hobbies list ──────────────────────────────────────────────────────────
HOBBIES = [
    # Outdoor
    'Trekking', 'Cycling', 'Swimming', 'Cricket', 'Badminton',
    'Kabaddi', 'Yoga', 'Gym & Fitness', 'Running',
    # Arts & Culture
    'Classical Music', 'Classical Dance', 'Painting', 'Photography',
    'Reading', 'Writing', 'Poetry',
    # Food & Lifestyle
    'Cooking', 'Baking', 'Gardening', 'Travelling',
    # Entertainment
    'Movies', 'OTT / Web Series', 'Gaming', 'Social Media',
    # Social
    'Volunteering', 'Teaching / Tutoring', 'Community Service',
    # Tech
    'Coding / Tech', 'Startups / Business',
]
