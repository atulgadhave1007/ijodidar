# iJodidar — Navigation Architecture
## Information Architecture + Navigation System Design
## June 2026

---

## CURRENT NAVIGATION — PROBLEMS IDENTIFIED

### Problem 1: Navigation exists in 3 places simultaneously
1. **Top navbar** — icon buttons (heart, chat, bookmark, bell, avatar)
2. **Left sidebar** — full nav links (home, profile, interests, search, shortlist, family, upgrade)
3. **Bottom nav** — same 5 tabs as partial sidebar

Users see three navigation systems. On desktop they navigate via sidebar AND icons.
On mobile they navigate via bottom nav, losing the sidebar entirely without replacement.

### Problem 2: Sidebar is a global nav masquerading as contextual
The left sidebar in home.html contains: mini profile widget + navigation links.
The left sidebar in profile.html contains: settings links.
These are completely different things with the same visual treatment.

### Problem 3: The avatar dropdown duplicates the sidebar
Avatar dropdown contains: My Profile, Settings, Family, Interests, Messages, Upgrade, Language.
Left sidebar contains: Home, My Profile, Interests, Search, Shortlist, Family, Upgrade.
Users can reach Interests from the top nav (heart icon), avatar dropdown, left sidebar, and bottom nav.
That is 4 paths to the same page — this is confusion, not convenience.

---

## REDESIGNED INFORMATION ARCHITECTURE

### Level 1 — Primary Navigation (5 destinations)
```
🏠 Matches      /home         — Feed + discovery tabs
🔍 Search       /search       — Filter-based profile discovery
❤️  Interests   /interests    — Sent, received, accepted
💬 Messages     /messages     — Conversations
👤 Profile      /profile      — Profile view + settings
```

### Level 2 — Secondary Navigation (within sections)

**Matches:**
```
/home                    → tab: Best Matches (default)
/home?tab=new           → tab: New This Week
/home?tab=mutual        → tab: Mutual Interest
/home?tab=near          → tab: Near Me
```

**Search:**
```
/search                  → results with filter panel
(no sub-navigation)
```

**Interests:**
```
/interests               → tab: Received (default)
/interests?tab=sent      → tab: Sent
/interests?tab=accepted  → tab: Accepted/Connections
/interests?tab=viewers   → tab: Who Viewed Me
```

**Messages:**
```
/messages                → inbox list
/messages/<id>           → conversation view
```

**Profile:**
```
/profile                 → tab: About (default — shows completeness)
/profile?tab=career      → tab: Career & Education
/profile?tab=family      → tab: My Family
/profile?tab=photos      → tab: Photos
/profile?tab=prefs       → tab: Partner Preferences
/profile/privacy         → Privacy & Data
/profile/referral        → Refer & Earn
/membership/plans        → Membership (linked from profile)
```

### Level 3 — Utility Navigation (accessed via avatar/menu)
```
Language toggle (EN/MR)
/kundli/edit              → Kundli / Guna Milan
/auth/logout              → Sign out
/privacy-policy           → Legal
/terms                    → Legal
```

---

## NAVIGATION COMPONENTS — 3 BREAKPOINTS

### Mobile (< 768px)

**Top bar:**
```
[iJodidar logo]    ——————    [🔔 bell + badge]
```
Only 2 elements. No search bar, no icons. Search is accessed via bottom nav.

**Bottom nav (fixed, 64px):**
```
┌─────┬─────┬─────┬─────┬─────┐
│  🏠 │  🔍 │ ❤️  │  💬 │  👤 │
│Match│Srch │Inter│ Msg │Prof │
└─────┴─────┴─────┴─────┴─────┘
```
- Active state: `--brand` red icon + label
- Badge on ❤️ for pending interests
- Badge on 💬 for unread messages

**No sidebar on mobile.** Sidebar content moves:
- Mini profile widget → /profile page header
- Upgrade nudge → persistent banner in feed

---

### Tablet (768px – 1023px)

**Top bar:**
```
[iJodidar] [Search___________] [❤ badge] [💬 badge] [🔔 badge] [Avatar ▾]
```
5 elements. Avatar expands to utility dropdown.

**No sidebar.** Content fills full width.
**No bottom nav.** Top nav is primary.

Sub-navigation (matches, interests, profile sections) appears as horizontal tabs below page header.

---

### Desktop (≥ 1024px)

**Top bar:**
```
[iJodidar] [Search_____________] [❤ 3] [💬 5] [🔔 2] [Avatar ▾]
```

**Contextual left sidebar (240px):**
- Changes per section — not a global navigation
- Matches page: mini profile + discovery tab links + upgrade nudge
- Search: filter panel
- Interests: interest category links + stats
- Profile: section nav (About / Career / Family / Photos / Prefs) + completeness ring
- Messages: conversation list (side panel, messages main area)

---

## AVATAR DROPDOWN — REDESIGNED

### Current: 11 items (overwhelming)
### Redesigned: 5 items + utility

```
┌──────────────────────────────┐
│  [Avatar] Name               │  ← user info header
│  atulgadhave1007@gmail.com   │
│  ⭐ Free Plan                │
├──────────────────────────────┤
│  ⚙️  Account Settings        │  → /profile
│  🌟 Upgrade Plan             │  → /membership/plans (amber icon = upgrade)
│  📊 Kundli / Guna Milan      │  → /kundli/edit
│  🎁 Refer & Earn             │  → /profile/referral
├──────────────────────────────┤
│  🌐 EN | मराठी               │  ← language toggle (inline)
│  🚪 Sign Out                 │  ← danger style
└──────────────────────────────┘
```

**Removed from dropdown:** My Profile, Family, Interests, Messages, Shortlist
These are all in the primary navigation. Dropdown is for account-level settings only.

---

## TAB NAVIGATION PATTERN

### Used for: Matches feed, Interests, Profile editor

```html
<!-- Tab component — consistent across all sections -->
<div class="ij-tabs">
  <a href="?tab=best"   class="ij-tab {{ 'active' if tab=='best'   }}">Best Matches</a>
  <a href="?tab=new"    class="ij-tab {{ 'active' if tab=='new'    }}">New</a>
  <a href="?tab=mutual" class="ij-tab {{ 'active' if tab=='mutual' }}">Mutual</a>
  <a href="?tab=near"   class="ij-tab {{ 'active' if tab=='near'   }}">Near Me</a>
</div>
```

```css
.ij-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1.5px solid var(--border-light);
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.ij-tabs::-webkit-scrollbar { display: none; }

.ij-tab {
  padding: 10px 16px;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-2);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: color var(--t-fast), border-color var(--t-fast);
  -webkit-tap-highlight-color: transparent;
}
.ij-tab.active {
  color: var(--brand);
  border-bottom-color: var(--brand);
  font-weight: 700;
}
.ij-tab:hover { color: var(--brand); }
```

---

## SEARCH FILTER ARCHITECTURE

### Current: Filter sidebar (hidden on mobile)
### Redesigned: Persistent pill filters + bottom sheet on mobile

**Desktop:** Filter sidebar in left column (already exists, good)

**Mobile:** Filter bar below search input
```
[Religion: Hindu ×] [Age: 24-35 ×] [City: Pune ×] [+ More Filters]
```
Scrollable horizontal pill row. Tap `+ More Filters` → bottom sheet with all filters.

```css
.filter-pills {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 10px 0;
  scrollbar-width: none;
}
.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: 1.5px solid var(--border);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-2);
  white-space: nowrap;
  cursor: pointer;
  background: var(--surface);
}
.filter-pill.active {
  border-color: var(--brand);
  color: var(--brand);
  background: var(--brand-alpha);
}
```

---

## PROFILE SECTION NAVIGATION

### Current: /profile is a settings-list page with 22 link rows
### Redesigned: 5 tabs, inline section nav

**Desktop:** Left sidebar with section links + completeness ring per section

```
┌──────────────────────────┐
│  Profile  72% ○          │  ← section heading + completeness
├──────────────────────────┤
│  📋 About          18/25 │  ← section + points earned
│  💼 Career         12/20 │
│  👨‍👩‍👧 Family         5/15  │
│  📸 Photos         8/10  │
│  ❤️  Preferences   10/10  │  ← 100% complete = green
├──────────────────────────┤
│  🔒 Privacy & Data       │
│  🎁 Refer & Earn         │
│  ⭐ Upgrade Plan         │
└──────────────────────────┘
```

**Mobile:** Horizontal tabs above content (same .ij-tabs pattern)

---

## URL STRUCTURE — CLEAN ROUTES

### Current routes have inconsistencies
```
/profile         → profile settings index
/profile/name    → edit name
/my_profile      → view own profile (public view)
/<username>      → view other's profile
/plans           → membership plans (not /membership/plans in nav)
/interests       → interests (not /connect/interests in nav)
```

### Recommended clean routes

```
# Auth
GET  /login
GET  /register
GET  /verify/<token>
GET  /forgot-password

# Core (5 main sections)
GET  /home           → Matches
GET  /search         → Search
GET  /interests      → Interests
GET  /messages       → Inbox
GET  /messages/<id>  → Conversation
GET  /profile        → My profile editor (tabbed)

# Public profile
GET  /@<username>    → Public profile view (cleaner than /<username>)

# Membership
GET  /plans          → Membership (keep this URL — direct)

# Legal
GET  /privacy-policy
GET  /terms

# Console (staff only)
GET  /console/...

# API (future)
/api/v1/...
```

---

## DEEP LINK SUPPORT (Future — mobile app)

```
ijodidar://home
ijodidar://messages/<conv_id>
ijodidar://profile/@username
ijodidar://interests
ijodidar://plans
```

These become important when React Native app is built.
Deep link intent filters need to match the URL structure above.

---

*Navigation Architecture | iJodidar | June 2026*
