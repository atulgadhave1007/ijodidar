# iJodidar — Mobile-First Design System
## Component Specifications + Responsive Breakpoints
## June 2026

---

## PHILOSOPHY

"Mobile-first" does not mean "desktop-minus". It means:
1. Design the mobile experience completely, independently
2. Enhance progressively for larger screens
3. Never hide important features — reshape them

Indian matrimony users: **73% mobile, 27% desktop** (industry average 2025).
The mobile experience IS the product. Desktop is the enhancement.

---

## BREAKPOINT SYSTEM

```css
/* Mobile-first breakpoints */
/* xs: 0 - 479px    → small phones */
/* sm: 480-639px    → standard phones */
/* md: 640-767px    → large phones, small tablets */
/* lg: 768-1023px   → tablets */
/* xl: 1024-1279px  → small desktop */
/* 2xl: 1280px+     → large desktop */

:root {
  --screen-sm:  480px;
  --screen-md:  640px;
  --screen-lg:  768px;
  --screen-xl:  1024px;
  --screen-2xl: 1280px;
}

/* Usage */
@media (min-width: 768px)  { /* tablet and up */ }
@media (min-width: 1024px) { /* desktop and up */ }
@media (max-width: 767px)  { /* mobile only — use sparingly */ }
```

---

## SPACING SYSTEM

All spacing uses 4px base unit.

```css
/* Spacing tokens */
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;

/* Safe areas — iPhone notch + Android navigation */
.safe-top    { padding-top:    env(safe-area-inset-top);    }
.safe-bottom { padding-bottom: env(safe-area-inset-bottom); }
.safe-left   { padding-left:   env(safe-area-inset-left);   }
.safe-right  { padding-right:  env(safe-area-inset-right);  }
```

---

## TOUCH INTERACTION SYSTEM

```css
/* Minimum touch target */
.touch-target {
  min-width:  44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Remove all hover effects on touch screens */
@media (hover: none) {
  .btn-ij-primary:hover  { transform: none; background: var(--brand); }
  .ij-profile-card:hover { transform: none; box-shadow: none; }
}

/* Active/pressed state for mobile */
.btn-ij-primary:active {
  transform: scale(0.97);
  transition: transform 0.08s ease;
}

/* Remove tap highlight */
* {
  -webkit-tap-highlight-color: transparent;
}
```

---

## MOBILE LAYOUT PATTERNS

### Pattern 1: Full-width stack (cards, forms)
```
┌─────────────────┐
│  Header / Nav   │  56px fixed
├─────────────────┤
│                 │
│   Content       │  fills viewport
│                 │
├─────────────────┤
│  Bottom Nav     │  64px fixed
└─────────────────┘
```

### Pattern 2: Scrollable sections with sticky subheader
```
┌─────────────────┐
│  Top Nav        │  56px fixed, z:600
├─────────────────┤
│  Section Header │  sticky, z:200
│  [Tab1] [Tab2]  │
├─────────────────┤
│                 │
│   Scrollable    │
│   Content       │
│                 │
├─────────────────┤
│  Bottom Nav     │  64px fixed, z:600
└─────────────────┘
```

### Pattern 3: Split view (messages — becomes full-screen on mobile)
```
Mobile:                    Desktop:
┌─────────────────┐        ┌──────┬──────────────┐
│  Inbox list     │   →    │ List │ Conversation │
│  (full screen)  │        │      │              │
│  Tap → conv     │        └──────┴──────────────┘
└─────────────────┘
```

---

## MOBILE-SPECIFIC COMPONENTS

### Mobile Search Bar (full-width, no sidebar)

```html
<!-- Mobile search — appears on /search page, not in navbar -->
<div class="mobile-search-bar">
  <div class="search-input-wrap">
    <i class="bi bi-search"></i>
    <input type="search" placeholder="Religion, city, occupation…" 
           name="keyword" autocomplete="off">
  </div>
  <button class="filter-trigger" id="openFilters">
    <i class="bi bi-sliders"></i>
    <span>Filters</span>
    {% if active_filters > 0 %}
    <span class="filter-count">{{ active_filters }}</span>
    {% endif %}
  </button>
</div>
```

```css
.mobile-search-bar {
  display: flex;
  gap: 8px;
  padding: 10px var(--space-4);
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  position: sticky;
  top: 56px;  /* below navbar */
  z-index: var(--z-sticky);
}
.search-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface-2);
  border-radius: 24px;
  padding: 8px 16px;
}
.search-input-wrap input {
  border: none;
  background: transparent;
  flex: 1;
  font-size: 14px;
  outline: none;
}
.filter-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border: 1.5px solid var(--border);
  border-radius: 24px;
  background: var(--surface);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.filter-count {
  background: var(--brand);
  color: #fff;
  border-radius: 10px;
  padding: 0 6px;
  font-size: 10px;
  font-weight: 700;
  min-width: 18px;
  text-align: center;
}
```

### Mobile Profile Card — 2-column grid

```css
/* 2 columns on mobile, smaller cards */
@media (max-width: 767px) {
  .card-grid { grid-template-columns: repeat(2, 1fr); gap: var(--space-2); }
  
  .ij-profile-card .card-photo { aspect-ratio: 3/4; }
  .ij-profile-card .card-info  { padding: 8px 10px; }
  .ij-profile-card .card-name  { font-size: 13px; }
  .ij-profile-card .card-meta  { font-size: 11px; }
  .ij-profile-card .card-actions { padding: 8px 10px; gap: 6px; }
  .ij-profile-card .card-actions .btn-interest { font-size: 12px; padding: 6px 8px; }
}
```

### Mobile Onboarding — Full screen steps

```css
/* Onboarding is full-screen on mobile, centered card on desktop */
.onboarding-wrap {
  min-height: 100dvh;  /* dvh = dynamic viewport height, handles mobile browser bars */
  display: flex;
  flex-direction: column;
  padding: var(--space-5) var(--space-4);
  /* No bottom nav during onboarding */
}
.onboarding-content { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.onboarding-cta     { padding-bottom: env(safe-area-inset-bottom); }

@media (min-width: 640px) {
  .onboarding-wrap {
    align-items: center;
    justify-content: center;
    background: var(--bg);
  }
  .onboarding-card {
    max-width: 480px;
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: var(--r-xl);
    padding: var(--space-8) var(--space-8);
  }
}
```

### Mobile Interest Action — Sticky bottom on profile view

```css
/* When viewing a profile on mobile, CTAs stick to bottom */
@media (max-width: 767px) {
  .profile-view-ctas {
    position: fixed;
    bottom: 0;
    left: 0; right: 0;
    padding: var(--space-3) var(--space-4);
    padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom));
    background: rgba(255,255,255,.97);
    backdrop-filter: blur(12px);
    border-top: 1px solid var(--border-light);
    display: flex;
    gap: var(--space-2);
    z-index: var(--z-sticky);
  }
  .profile-view-ctas .btn-interest { flex: 1; justify-content: center; }
  .profile-view-ctas .btn-save     { width: 44px; height: 44px; flex-shrink: 0; }
}
```

---

## PROGRESSIVE WEB APP (PWA) CHECKLIST

### Current status: PWA exists but needs improvements

```
✅ manifest.json present
✅ service worker registered
✅ HTTPS
✅ theme-color meta tag
✅ apple-touch-icon
⚠️ icons: need 192px and 512px PNG (maskable)
⚠️ offline page: needs /offline.html
⚠️ install prompt: needs custom "Install App" nudge UI
❌ push notifications: FCM not integrated
❌ background sync: not implemented
```

### Required manifest.json improvements

```json
{
  "name": "iJodidar — Find Your Match",
  "short_name": "iJodidar",
  "description": "India's trusted matrimony platform",
  "start_url": "/home",
  "display": "standalone",
  "background_color": "#f3f2ef",
  "theme_color": "#d63031",
  "orientation": "portrait",
  "icons": [
    { "src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
    { "src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ],
  "screenshots": [
    { "src": "/static/screenshots/home.jpg", "sizes": "390x844", "type": "image/jpeg" }
  ],
  "categories": ["lifestyle", "social"],
  "lang": "en-IN"
}
```

### Service worker: offline page

```javascript
// static/sw.js — add offline fallback
const OFFLINE_URL = '/offline.html';
const CACHE_NAME = 'ijodidar-v1';

// Cache static assets on install
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => 
      cache.addAll([OFFLINE_URL, '/static/css/style.css', '/static/icons/icon-192.png'])
    )
  );
});

// Serve cached offline page when network fails
self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
  }
});
```

---

## ANDROID / IOS APP READINESS CHECKLIST

### What works today in a React Native app:
```
✅ /kundli/api/calculate     — JSON, no auth required
✅ /kundli/api/match         — JSON, no auth required  
✅ /kundli/api/cities        — JSON, no auth required
✅ /notifications/unread-count — JSON (needs JWT auth)
⚠️ /notifications/list       — JSON (needs JWT auth)
⚠️ /messages/<id>/poll       — JSON (needs JWT auth)
❌ Everything else           — returns HTML, unusable
```

### What needs building for mobile app:
```
Priority 1 (auth + feed):
  POST /api/v1/auth/send-otp
  POST /api/v1/auth/verify-otp  → { access_token, refresh_token }
  POST /api/v1/auth/refresh
  GET  /api/v1/profiles/feed    → JSON array
  GET  /api/v1/profiles/@username

Priority 2 (connect):
  POST /api/v1/interests
  GET  /api/v1/interests/received
  PATCH /api/v1/interests/<id>

Priority 3 (messaging):
  GET  /api/v1/conversations
  GET  /api/v1/conversations/<id>/messages
  POST /api/v1/conversations/<id>/messages

Priority 4 (profile):
  GET  /api/v1/profile/me
  PATCH /api/v1/profile/about
  POST /api/v1/profile/photos

Priority 5 (notifications):
  GET  /api/v1/notifications
  POST /api/v1/devices   → register FCM token
```

---

*Mobile-First Design System | iJodidar | June 2026*
