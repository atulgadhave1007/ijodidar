# iJodidar — Complete UI/UX Redesign
## Design System + Component Library + Interaction Patterns
## June 2026

---

## SECTION 1 — DESIGN TOKEN AUDIT

### Current tokens — what stays
```css
/* These are correct — do not change */
--brand:        #d63031;    /* iJodidar red — distinctive, matrimonial */
--brand-dark:   #b71c1c;
--brand-alpha:  rgba(214,48,49,.08);
--bg:           #f3f2ef;    /* warm grey — correct for content-heavy app */
--surface:      #ffffff;
--text:         #191919;
--green:        #057642;    /* trust/success */
--blue:         #0a66c2;    /* action/link */
```

### Tokens to ADD
```css
:root {
  /* Spacing scale — consistent rhythm */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Typography scale */
  --text-xs:   11px;
  --text-sm:   12px;
  --text-base: 14px;
  --text-md:   15px;
  --text-lg:   16px;
  --text-xl:   18px;
  --text-2xl:  20px;
  --text-3xl:  24px;
  --text-4xl:  30px;
  --text-5xl:  36px;

  /* Z-index scale */
  --z-base:    1;
  --z-dropdown: 100;
  --z-sticky:   200;
  --z-overlay:  300;
  --z-modal:    400;
  --z-toast:    500;
  --z-nav:      600;

  /* Trust colors */
  --trust-registered: #6b7280;
  --trust-phone:      #d97706;
  --trust-id:         #ea580c;
  --trust-full:       #057642;

  /* Match score colors */
  --score-low:    #ef4444;  /* < 50% */
  --score-mid:    #f59e0b;  /* 50-74% */
  --score-high:   #057642;  /* 75%+ */
}
```

---

## SECTION 2 — TYPOGRAPHY SYSTEM

### Font stack (current is correct, optimize weight loading)
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
               Inter, 'DM Sans', Roboto, sans-serif;
  font-size: var(--text-base);
  line-height: 1.6;
  font-feature-settings: 'kern' 1, 'liga' 1;
}

/* Heading hierarchy */
.ij-h1 { font-size: var(--text-5xl); font-weight: 800; letter-spacing: -0.025em; }
.ij-h2 { font-size: var(--text-4xl); font-weight: 700; letter-spacing: -0.02em; }
.ij-h3 { font-size: var(--text-3xl); font-weight: 700; letter-spacing: -0.015em; }
.ij-h4 { font-size: var(--text-xl);  font-weight: 700; }
.ij-h5 { font-size: var(--text-lg);  font-weight: 600; }
.ij-h6 { font-size: var(--text-md);  font-weight: 600; }

/* Label styles */
.ij-label {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-3);
}
```

---

## SECTION 3 — COMPONENT LIBRARY (Complete)

### 3.1 Buttons

```css
/* PRIMARY — main CTA */
.btn-ij-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px 20px;
  background: var(--brand);
  color: #fff;
  border: none;
  border-radius: 24px;    /* pill shape — matrimony standard */
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--t-fast);
  white-space: nowrap;
  text-decoration: none;
  -webkit-tap-highlight-color: transparent;
}
.btn-ij-primary:hover  { background: var(--brand-dark); transform: translateY(-1px); }
.btn-ij-primary:active { transform: translateY(0); opacity: .9; }

/* GHOST — secondary CTA */
.btn-ij-ghost {
  /* same as primary but background: transparent, border: 1.5px solid var(--border) */
}

/* OUTLINE — danger/alert actions */
.btn-ij-outline {
  background: transparent;
  border: 1.5px solid var(--brand);
  color: var(--brand);
  /* otherwise same as primary */
}

/* ICON BUTTON — nav + cards */
.btn-ij-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-2);
  transition: background var(--t-fast);
}
.btn-ij-icon:hover { background: var(--surface-2); }

/* Sizes */
.btn-sm { padding: 6px 14px; font-size: var(--text-sm); }
.btn-lg { padding: 13px 28px; font-size: var(--text-md); }

/* INTEREST button — special green */
.btn-interest {
  background: #dcfce7;
  color: var(--green);
  border: 1.5px solid #86efac;
  /* pill shape, same sizing */
}
.btn-interest:hover { background: var(--green); color: #fff; border-color: var(--green); }
.btn-interest.sent  { background: var(--green); color: #fff; border-color: var(--green); }
```

### 3.2 Profile Card (REDESIGNED — replaces current)

```css
/* Card container */
.ij-profile-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--r-lg);   /* 16px */
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--t-mid), box-shadow var(--t-mid);
  position: relative;
  display: flex;
  flex-direction: column;
}
.ij-profile-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.ij-profile-card:active { transform: translateY(-1px); }

/* Photo area */
.card-photo {
  position: relative;
  aspect-ratio: 3/4;    /* portrait — shows face better than 4:3 */
  background: linear-gradient(135deg, var(--brand-alpha), var(--surface-2));
  overflow: hidden;
}
.card-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;  /* faces appear at top */
}
.card-photo .photo-blur {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(10px);
  transform: scale(1.05);  /* hide blur edges */
}
.card-photo-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.38);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
}

/* Match score badge — top right */
.card-score-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0,0,0,.65);
  backdrop-filter: blur(8px);
  color: #fff;
  padding: 3px 9px;
  border-radius: 20px;
  font-size: var(--text-xs);
  font-weight: 700;
}
.card-score-badge.high { background: rgba(5,118,66,.85); }
.card-score-badge.mid  { background: rgba(217,119,6,.85); }

/* Spotlight badge */
.card-spotlight-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  padding: 3px 9px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 700;
}

/* Info area */
.card-info {
  padding: 12px 14px;
  flex: 1;
}
.card-name {
  font-size: var(--text-md);
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 3px;
}
.card-meta {
  font-size: var(--text-sm);
  color: var(--text-2);
  line-height: 1.5;
}
.card-trust {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: var(--text-xs);
  font-weight: 600;
}

/* Action row */
.card-actions {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid var(--border-light);
}
.card-actions .btn-interest { flex: 1; justify-content: center; font-size: 13px; }
.card-actions .btn-save     { width: 38px; height: 38px; flex-shrink: 0; }
```

### 3.3 Trust Badge System

```css
.trust-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 700;
}
.trust-badge.registered { color: var(--trust-registered); background: #f3f4f6; }
.trust-badge.phone      { color: var(--trust-phone);      background: #fef3c7; }
.trust-badge.id         { color: var(--trust-id);         background: #fff7ed; }
.trust-badge.full       { color: var(--trust-full);       background: var(--green-bg); }
```

### 3.4 Completeness Ring

```css
.completeness-ring-wrap {
  position: relative;
  width: 44px;
  height: 44px;
}
.completeness-ring-wrap svg {
  transform: rotate(-90deg);
}
.completeness-pct {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  color: var(--brand);
}
```

### 3.5 Bottom Navigation (IMPROVED)

```css
#ij-bottom-nav {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 64px;              /* increased from 56px — larger touch targets */
  background: rgba(255,255,255,.97);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--border-light);
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  z-index: var(--z-nav);
  /* Only visible on mobile */
  display: none;
}
@media (max-width: 767px) {
  #ij-bottom-nav { display: grid; }
  .page-wrap { padding-bottom: 64px; }  /* prevent content hidden behind nav */
}

.bn-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 10px;
  font-weight: 500;
  color: var(--text-3);
  text-decoration: none;
  position: relative;
  min-height: 44px;         /* accessibility: min tap target */
  -webkit-tap-highlight-color: transparent;
  transition: color var(--t-fast);
}
.bn-item i {
  font-size: 22px;           /* larger icons */
  transition: transform var(--t-fast);
}
.bn-item.active {
  color: var(--brand);
}
.bn-item.active i {
  transform: scale(1.1);
}
.bn-item:active i { transform: scale(0.95); }
```

### 3.6 Forms and Inputs

```css
/* Base input — consistent across all forms */
.ij-input {
  width: 100%;
  padding: 11px 14px;
  border: 1.5px solid var(--border);
  border-radius: var(--r-sm);   /* 8px */
  font-size: var(--text-base);
  font-family: inherit;
  color: var(--text);
  background: var(--surface);
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
  -webkit-appearance: none;      /* removes iOS styling */
  appearance: none;
}
.ij-input:focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-alpha);
}
.ij-input.error { border-color: #ef4444; }
.ij-input::placeholder { color: var(--text-3); }

/* Select — custom arrow */
.ij-select {
  /* same as ij-input */
  padding-right: 36px;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 10px center;
  background-repeat: no-repeat;
  background-size: 16px;
  cursor: pointer;
}

/* Field group — label + input + error */
.ij-field {
  margin-bottom: var(--space-4);
}
.ij-field label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: var(--space-1);
}
.ij-field-error {
  font-size: var(--text-xs);
  color: #ef4444;
  margin-top: var(--space-1);
}
.ij-field-hint {
  font-size: var(--text-xs);
  color: var(--text-3);
  margin-top: var(--space-1);
}
```

### 3.7 Cards and Surfaces

```css
.ij-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.ij-card-header {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ij-card-body {
  padding: var(--space-4) var(--space-5);
}

/* Elevated card — for important content */
.ij-card-elevated {
  box-shadow: var(--shadow-sm);
  border: none;
}

/* Section card — profile sections */
.ij-section-card {
  /* same as ij-card */
  margin-bottom: var(--space-4);
}
.ij-section-card .section-title {
  font-size: var(--text-lg);
  font-weight: 700;
  padding: var(--space-4) var(--space-5) var(--space-3);
  border-bottom: 1px solid var(--border-light);
}
```

### 3.8 Avatar System

```css
.ij-avatar {
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand), #ff6b6b);
  color: #fff;
  flex-shrink: 0;
  position: relative;
}
/* Sizes */
.ij-avatar.xs { width: 28px;  height: 28px;  font-size: 11px; }
.ij-avatar.sm { width: 36px;  height: 36px;  font-size: 13px; }
.ij-avatar.md { width: 48px;  height: 48px;  font-size: 16px; }
.ij-avatar.lg { width: 64px;  height: 64px;  font-size: 20px; }
.ij-avatar.xl { width: 88px;  height: 88px;  font-size: 28px; }
.ij-avatar img { width: 100%; height: 100%; object-fit: cover; }
```

### 3.9 Bottom Sheet (mobile modals)

```css
/* Bottom sheet — replaces modal for filter panels on mobile */
.ij-bottom-sheet {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: none;
}
.ij-bottom-sheet.open { display: block; }
.ij-sheet-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.4);
}
.ij-sheet-panel {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: var(--surface);
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  padding-bottom: env(safe-area-inset-bottom);
  max-height: 90vh;
  overflow-y: auto;
  transform: translateY(100%);
  transition: transform .35s cubic-bezier(.32,.72,0,1);
}
.ij-bottom-sheet.open .ij-sheet-panel {
  transform: translateY(0);
}
.ij-sheet-handle {
  width: 36px;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  margin: 12px auto 4px;
}
```

---

## SECTION 4 — LAYOUT SYSTEM

### Container
```css
.ij-container {
  max-width: 1180px;
  margin: 0 auto;
  padding: var(--space-4);
  padding-top: calc(56px + var(--space-4));  /* navbar height */
}
@media (min-width: 768px) {
  .ij-container { padding: var(--space-5) var(--space-6); }
  .ij-container { padding-top: calc(56px + var(--space-5)); }
}
```

### Two-column layout (desktop)
```css
.ij-two-col {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: var(--space-4);
  align-items: start;
}
@media (max-width: 1023px) {
  .ij-two-col { grid-template-columns: 1fr; }
  .ij-two-col .ij-sidebar { display: none; }
}
```

### Profile card grid
```css
.card-grid {
  display: grid;
  gap: var(--space-3);
  /* Mobile: 2 columns */
  grid-template-columns: repeat(2, 1fr);
}
@media (min-width: 640px)  { .card-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .card-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 1280px) { .card-grid { grid-template-columns: repeat(4, 1fr); } }
```

---

## SECTION 5 — INTERACTION PATTERNS

### Interest button state machine
```
[Initial]          → tap     → [Sending...] → success → [Interest Sent ✓]
[Interest Sent ✓]  → tap     → [Withdraw?]  → confirm → [Initial]
```
All transitions via JavaScript with optimistic UI (update UI before API response).

### Profile photo unlock
```
[Blurred photo]
  Free user: "Silver+ to view · ₹499/mo" overlay with tap → /plans
  Silver user: clear photo — no interaction needed
```

### Completeness nudge dismissal
Shown for 3 days, then dismissed by user. Reappears when completeness drops below 60%.

### Swipe on profile cards (mobile, Phase 2)
```
Swipe right → Send Interest (with spring animation)
Swipe left  → Skip (dismisses from feed for 7 days)
Tap         → Open profile
```

---

## SECTION 6 — COLOR USAGE GUIDE

| Element | Color | Why |
|---------|-------|-----|
| Primary CTA | `--brand` red | Action, attention |
| Interest sent | green | Positive, success |
| Phone verified badge | amber | Warning, pending |
| ID verified badge | orange | Achievement |
| Fully verified | green | Trust, complete |
| Match score high | green | Positive signal |
| Match score low | red | Caution signal |
| Links | `--blue` | Convention |
| Notification dots | `--brand` | Urgency |
| Spotlight badge | gold gradient | Premium |
| Upgrade CTA | amber | Warm, not alarming |

---

## SECTION 7 — ACCESSIBILITY REQUIREMENTS

- All interactive elements: minimum 44×44px touch target
- Color is never the only differentiator — always pair with icon or text
- Focus states: 3px `--brand-alpha` ring on all interactive elements
- Images: always `alt` attribute (empty for decorative)
- Form labels: always visible (no placeholder-only labels)
- Error messages: above or below field (not inside field)
- Contrast: all text meets WCAG AA (4.5:1 for body, 3:1 for large text)

---

*Complete UI/UX Redesign | iJodidar | June 2026*
