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

### DEC-004 — S3 bucket name correction
Date: 2026-06-20
Context: .env had AWS_S3_BUCKET=ijodidar-images; actual bucket name is ijodidar-images-087242257564-ap-south-1-an. IAM policy also referenced the wrong ARN.
Options considered: A) Rename bucket. B) Update .env and IAM policy to match existing bucket.
Decision: Updated .env (local + EC2) and IAM policy resource to use the real bucket name. Bucket rename avoided — no existing data to migrate, renaming adds risk.
Consequence: .env on EC2 must always use the full bucket name. Verified operational via scripts/verify_s3.py — all 8 checks passed.
Reference: Pre-Sprint 0 external Go/No-Go condition; MASTER_PROMPT.md §7.1.

### DEC-005 — Sprint 1: Celery Beat celery binary path (system vs venv)
Date: 2026-06-20
Context: ijodidar-beat.service failed with status=203/EXEC — celery binary not present in venv/bin/. Celery was installed at system level (/home/ubuntu/ijodidar/venv/bin/celery via PATH resolution inside the activated venv, but the actual binary path needed by systemd is the venv python invoking the celery module).
Options considered: A) pip install celery into venv. B) Use `which celery` to find real path and sed-update the service file.
Decision: Used `which celery` to locate the binary and patched the service ExecStart path. Beat now running as a supervised systemd service.
Consequence: ijodidar-beat.service is enabled and active. Celery Beat path = /home/ubuntu/ijodidar/venv/bin/python3 /home/ubuntu/ijodidar/venv/bin/celery.
Reference: Sprint 1 Beat scheduler deliverable.

### DEC-006 — Migration chain: EC2 diverged from Windows (two migration roots)
Date: 2026-06-20
Context: EC2 had original migration 258790d00566 (June 8). Windows had 27c944af2966 as initial. After Pre-Sprint 0 the EC2 chain is: 258790d00566 → a1b2c3d4e5f6 → e5c78df6213f (merge) → d635e7cc9b9c → f1a2b3c4d5e6. The Windows local migrations directory only has 27c944af2966 and a1b2c3d4e5f6.
Options considered: A) Sync all EC2 migration files back to Windows. B) Accept divergence and keep EC2 as the authoritative migration chain.
Decision: EC2 is the authoritative migration chain. Windows local dev uses SQLite (no PostgreSQL) so the extra EC2 migrations don't affect local development. Sprint 1 migration f1a2b3c4d5e6 was written with down_revision=d635e7cc9b9c to target EC2 chain.
Consequence: Windows local `flask db upgrade` will fail on PostgreSQL-specific migrations. Acceptable since local dev uses SQLite. Future sessions must always run migrations on EC2, not locally.
Reference: Pre-Sprint 0 migration remediation; Sprint 1 f1a2b3c4d5e6.

### DEC-003 — Income filter: ProfessionalDetails.income_lpa (Integer) used for range filter
Date: 2026-06-20
Context: Pre-Sprint 0 item 5 — wire income filter. MASTER_PROMPT.md §5.3 notes that Sprint 1 should add `min_income_lpa`/`max_income_lpa` Integer columns to PartnerPreference; separately the search filter needed wiring.
Options considered: A) Filter on `ProfessionalDetails.income_lpa` (existing Integer column). B) Wait for Sprint 1 PartnerPreference columns.
Decision: Wire the search filter against `ProfessionalDetails.income_lpa` now (Pre-Sprint 0 fix). Sprint 1 PartnerPreference income column fix is a separate item.
Consequence: Income search filter is live. PartnerPreference.min_income String column remains to be migrated in Sprint 1 (Conflict C8).
Reference: Pre-Sprint 0 item 5, Conflict C8 (§5.4).
