# DECISION_LOG.md — iJodidar v2 Transformation
## Append-only. Never edit or renumber a past entry — supersede it with a new one instead.

---

### DEC-001 — Email-first vs phone-first registration
Date: June 2026 (carried forward from audit Phase B)
Context: `MASTER_PRODUCT_REDESIGN.md`, `IDEAL_USER_FLOW.md`, and `API_FIRST_ARCHITECTURE.md`
all specify phone-first registration; current implementation gates all access behind email
verification, measured at 40–60% drop-off.
Options considered: (A) keep email-first, (B) phone-first as primary with email secondary,
(C) phone-only, remove email entirely.
Decision: (B). Phone OTP becomes the primary registration path. Email is retained as a
secondary channel for notifications/account recovery, not as an access gate.
Consequence: Registration form and onboarding Step 1 are restructured (Sprint 1). Existing
users are unaffected — this only changes the path for new registrations.
Reference: Conflict C1 / `REDESIGN_ALIGNMENT_REPORT.md`.

### DEC-002 — Profile editing: 22–26 routes vs unified editor
Date: June 2026
Context: Profile completeness journey scores 20/100; full-page-reload-per-field editing is
the most-cited UX defect in the corpus (`TD-H01`).
Options considered: (A) leave as-is, (B) build a unified tabbed/AJAX editor and redirect
old routes, (C) delete old routes outright and force a hard cutover.
Decision: (B). New unified editor at `/profile`; every legacy route 301-redirects into the
relevant tab. No hard cutover, no deleted bookmarks.
Consequence: Requires new `/api/profile/<section>` or equivalent AJAX endpoints (Sprint 3).
Reference: Conflict C2.

### DEC-003 — Bootstrap card markup vs `ij-*` design system
Date: June 2026
Context: `my_profile.html` uses Bootstrap (`card shadow-sm rounded-4`) while the rest of the
app uses the custom `ij-*` token system.
Decision: Replace Bootstrap classes with `ij-*` equivalents. Visual-only change; no model
or route impact.
Reference: Conflict C3.

### DEC-004 — Global sidebar vs contextual per-section sidebar
Date: June 2026
Decision: Sidebar becomes a template block, overridden per section, rather than one global
component rendered identically everywhere.
Reference: Conflict C4.

### DEC-005 — Session auth vs JWT auth for SocketIO
Date: June 2026
Context: Mobile app cannot use SocketIO with session-cookie auth.
Decision: Add a JWT auth path in `socket_events.py` alongside the existing session path.
Web clients keep using sessions; mobile clients use JWT. Both paths must be independently
testable and one must never be able to silently break the other.
Reference: Conflict C5.

### DEC-006 — Synchronous email call inside the SocketIO message handler
Date: June 2026
Context: Found blocking the realtime event loop; classified HIGH/CERTAIN risk.
Decision: Replace with `send_message_email_task.delay(...)`. Pre-Sprint 0 item — fix before
any other SocketIO work proceeds.
Reference: Conflict C6.

### DEC-007 — `date_of_birth` (String) vs `dob` (Date)
Date: June 2026
Context: Both columns exist; code is inconsistent about which it reads/writes; age-range
search uses the unreliable String column.
Decision: All code migrates to `dob` (Date) exclusively. `date_of_birth` is deprecated, data
migrated, column dropped once migration is verified safe.
Reference: Conflict C7.

### DEC-008 — `PartnerPreference.min_income` (String) vs Integer LPA columns
Date: June 2026
Decision: Add `min_income_lpa` / `max_income_lpa` (Integer). Migrate existing parseable
string data; null where not parseable. Wire the search filter to the new columns.
Reference: Conflict C8.

### DEC-009 — Income filter UI present but not wired to the query
Date: June 2026
Decision: Two-hour fix — add the `ProfessionalDetails` join and range filter to the search
query. Pre-Sprint 0 item; certain/high revenue-relevant risk if left unresolved.
Reference: Conflict C9.

### DEC-010 — Deprecated `/admin/` blueprint alongside `/console/`
Date: June 2026
Context: 14 routes in `app/admin/routes.py` exist solely to redirect to `/console/`
equivalents; 7 legacy templates maintained alongside.
Decision: Remove `app/admin/routes.py` and `templates/admin/` entirely. Pre-Sprint 0 item.
Reference: Conflict C10.

---

<!--
New entries start at DEC-011. Use this template:

### DEC-<NNN> — <short title>
Date: <date>
Context: <what triggered this decision>
Options considered: <A, B, ...>
Decision: <what was chosen>
Consequence: <what this implies / what it forecloses>
Reference: <which audit doc, conflict ID, or sprint item this relates to>
-->
