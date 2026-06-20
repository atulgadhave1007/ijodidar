# Decision Log — iJodidar v2 Transformation
<!-- Append-only. Never delete or renumber entries. Format: DEC-NNN -->

### DEC-001 — Pre-Sprint 0 item 1: Duplicate /ijodidar/ directory
Date: 2026-06-20
Context: MASTER_PROMPT.md §7.1 item 1 — duplicate directory was listed as a blocker.
Options considered: A) Delete it. B) No action needed.
Decision: No action needed — directory does not exist in this working copy (`C:\Users\Admin\ijodidar`). The audit finding may have been based on the EC2 repo state. Verified with `Test-Path`.
Consequence: Item is RESOLVED. Verify on EC2 before next deployment.
Reference: Pre-Sprint 0 item 1, MASTER_PROMPT.md §3.4 finding #1.

### DEC-002 — Pre-Sprint 0 item 6: Duplicate check_gotra_compatibility
Date: 2026-06-20
Context: MASTER_PROMPT.md §7.1 item 6 — duplicate function listed as blocker.
Options considered: A) Remove duplicate. B) No action needed.
Decision: No action needed — `utils_kundli.py` has exactly one definition of `check_gotra_compatibility` (line 244). Duplicate may have existed in an earlier version or on a different branch.
Consequence: Item is RESOLVED. No code change required.
Reference: Pre-Sprint 0 item 6, MASTER_PROMPT.md §3.4 finding #6.

### DEC-003 — Income filter: ProfessionalDetails.income_lpa (Integer) used for range filter
Date: 2026-06-20
Context: Pre-Sprint 0 item 5 — wire income filter. MASTER_PROMPT.md §5.3 notes that Sprint 1 should add `min_income_lpa`/`max_income_lpa` Integer columns to PartnerPreference; separately the search filter needed wiring.
Options considered: A) Filter on `ProfessionalDetails.income_lpa` (existing Integer column). B) Wait for Sprint 1 PartnerPreference columns.
Decision: Wire the search filter against `ProfessionalDetails.income_lpa` now (Pre-Sprint 0 fix). Sprint 1 PartnerPreference income column fix is a separate item.
Consequence: Income search filter is live. PartnerPreference.min_income String column remains to be migrated in Sprint 1 (Conflict C8).
Reference: Pre-Sprint 0 item 5, Conflict C8 (§5.4).
