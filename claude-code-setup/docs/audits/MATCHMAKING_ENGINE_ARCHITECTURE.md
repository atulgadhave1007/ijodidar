# MATCHMAKING_ENGINE_ARCHITECTURE.md
## iJodidar v2 — Matchmaking Engine Architecture
## June 2026

---

## ENGINE OVERVIEW

The iJodidar matchmaking engine consists of three integrated layers:
1. **Preference Filter** — hard elimination based on partner preferences
2. **Weighted Score** — 11-factor compatibility score (0-100)
3. **Signal Adjustment** — behavioral boost/suppress (±10 pts)
4. **Guna Milan Integration** — Vedic astrological compatibility (±5 pts)

This architecture is correct and more sophisticated than most competitors
at this scale. The primary gap is caching — the engine runs synchronously
per request rather than pre-computing scores.

---

## LAYER 1 — PREFERENCE FILTER (Hard Elimination)

Runs as SQL WHERE clauses before any Python scoring.

**Current filters applied in home feed query:**
- Looking for (gender match) — correctly filters opposite gender
- is_active_acc = True
- is_hidden = False
- is_staff = False
- BlockList exclusion (via subquery)
- Spotlight profiles fetched first for position slots

**Gap:** Religion preference is a hard filter but PartnerPreference.religion is
a single String. If user accepts Hindu OR Jain, only one can be filtered.
Resolution: `religion_list` JSON column (v2 Sprint 1).

---

## LAYER 2 — WEIGHTED SCORING

`calculate_match_score()` in `app/utils.py` — 145 lines, pure Python.

### Current 11 Scoring Factors

| Factor | Max Points | Weight Rationale |
|--------|-----------|-----------------|
| Religion | 20 | Highest matrimonial priority in India |
| Age range | 15 | Strong preference; ±2yr partial score |
| Caste | 12 | Critical for many families; partial match for sub-caste |
| Location | 10 | Proximity matters for family meetings |
| Height | 8 | Common preference; ±5cm partial |
| Mother tongue | 8 | Language compatibility, cultural alignment |
| Education | 7 | Qualification matching |
| Diet | 5 | Lifestyle compatibility |
| Marital status | 5 | Strong preference (Never Married) |
| Profile photo | 5 | Completeness signal |
| Hobbies overlap | 5 | Personality compatibility |
| **Total MAX** | **100** | |

### Gaps in Current Scoring

| Missing Factor | Business Justification | v2 Action |
|---------------|----------------------|-----------|
| Income compatibility | Top 3 matrimony preference | Add income_lpa range scoring Sprint 2 |
| `last_active_at` recency | Recently active = more likely to respond | Add +5 boost for active in last 7 days Sprint 2 |
| Multi-religion preference | Single String limits religion matching | `religion_list` JSON Sprint 1 |
| Verification level | Trust signals should boost visible profiles | Add +3 for ID Verified profiles |
| Profile completeness | Complete profiles get better matches | Already partially handled by photo bonus |

### Scoring Architecture — Current vs Target

```
CURRENT (synchronous, per-request):
  HTTP Request
      ↓
  Fetch 80 candidates from DB (1 query + eager loads)
      ↓
  For each candidate (×80):
    calculate_match_score() — Python calculation
    get_signal_boost() — 1 DB query per candidate
    calculate_guna_milan() — 1 DB query per candidate (if kundli exists)
      ↓
  Sort by score → take top 24
      ↓
  Render template
  
  Total: 1 + (80 × 2) = ~161 DB queries per home feed load
  Time: ~400ms at low concurrency

TARGET (cached, near-instant):
  HTTP Request
      ↓
  Fetch user's pre-computed score cache from MatchScoreCache
  (1 DB query, 24 rows max)
      ↓
  Fetch those 24 candidate profiles (1 query with joinedload)
      ↓
  Render template
  
  Total: 2 DB queries per home feed load
  Time: <50ms
  
  Cache refresh: Celery task, triggered on profile save or pref change
```

---

## LAYER 3 — BEHAVIORAL SIGNAL ADJUSTMENT

`get_signal_boost()` in `app/utils.py` — returns float that is multiplied by 5.

### Signal Types and Values (verified in UserSignal model)

| Signal Type | Value | Effect |
|-------------|-------|--------|
| interest_sent | +1.0 | Mild positive — shown similar profiles |
| interest_accepted | +2.0 | Strong positive — show more like accepted |
| interest_declined | -1.0 | Mild negative — show fewer similar |
| profile_viewed | +0.3 | Weak positive — watched but not acted |
| shortlisted | +0.5 | Positive — saved for consideration |
| blocked | -2.0 | Strong negative — never show similar |
| reported | -3.0 | Strongest negative — filter out similar |

### Signal Integration

```python
boost = get_signal_boost(user_id, candidate_id)
signal_pts = int(boost * 5)
score = max(0, min(base_score + signal_pts, 100))
```

Maximum signal effect: +10 pts (accepted, value=2 × 5) or -15 pts (reported, value=-3 × 5).

---

## LAYER 4 — GUNA MILAN INTEGRATION

`calculate_guna_milan()` from `app/utils_kundli.py`

**Score adjustments:**
- 28+ gunas → +5 pts (high compatibility)
- 18-27 gunas → +2 pts (acceptable)
- < 18 gunas → -3 pts (concern)

**Only fires when both users have KundliDetail records.**
At current user scale, this affects a minority of pairs.

**Performance issue:** Per-candidate DB query inside scoring loop.
Resolution: Pre-join KundliDetail in initial candidate fetch (Sprint 2).

---

## GUNA MILAN ENGINE (iJodidar's Primary Differentiator)

### What Competitors Have

| Competitor | Guna Milan | Accuracy |
|------------|-----------|---------|
| Shaadi.com | Basic form entry | Manual nakshatra input; no verification |
| BharatMatrimony | Kundli upload | PDF upload; no auto-calculation |
| Jeevansathi | Basic | Manual entry |
| **iJodidar** | **Auto-calculation** | **Meeus algorithm; ±0.3° accuracy** |

### Engine Specifications (verified in Phase A)

| Component | Specification |
|-----------|--------------|
| Algorithm | Jean Meeus "Astronomical Algorithms" Chapter 47 |
| Ayanamsa | Lahiri (Chandra Rashtriya) — standard for Indian Vedic |
| Moon accuracy | ±0.3° — sufficient for Nakshatra (each spans 13.33°) |
| Performance | 0.025ms per calculation (1,000 calcs in 25ms) |
| External deps | None — pure Python, works offline |
| City database | 100+ Indian cities built-in; Nominatim fallback |
| Nadi assignments | All 27 corrected per Muhurta Chintamani + BPHS |
| Vashya method | Zodiac groups (corrected from Varna comparison) |
| Graha Maitri | 5-level scoring with neutral + enemy tiers (corrected) |
| 8 Ashta Koota | Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi |
| Nadi distribution | Verified 9-9-9 (Adi:9, Madhya:9, Antya:9) |

---

## v2 ENGINE IMPROVEMENTS

### Sprint 1
- Add income range scoring factor
- Add `last_active_at` recency boost (+5 pts for active < 7 days)
- Add trust tier boost (+3 pts for ID Verified profiles)
- Fix: use `dob` Date column for age calculation (not `date_of_birth` String)

### Sprint 2
- Pre-join KundliDetail in candidate fetch (eliminates per-candidate DB query)
- Add `religion_list` multi-value preference support

### Sprint 4
- Implement `MatchScoreCache` table
- Celery task: `refresh_match_scores_for_user(user_id)` on profile save
- Home feed reads from cache; falls back to real-time if cache miss
- Cache TTL: 24 hours; invalidate on profile update or preference change

---

*MATCHMAKING_ENGINE_ARCHITECTURE.md | iJodidar v2 | June 2026*
