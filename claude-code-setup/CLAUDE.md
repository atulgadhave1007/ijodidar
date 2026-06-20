# CLAUDE.md — iJodidar v2 Project Memory

> Claude Code loads this file automatically at session start. Keep it short — it exists to
> point to the real operating documents, not to duplicate them.

## Read this first, in order
1. `MASTER_PROMPT.md` — the full governing charter for this engagement. Read it in full
   before doing anything else. It contains ground truth, target architecture, the sprint
   roadmap, governance rules, and the agent roster summary.
2. `PROJECT_STATUS.md` → section `## v2 TRANSFORMATION STATUS` — current sprint, current
   maturity scores, open blockers.
3. The most recent `docs/phases/SPRINT_<N>_HANDOFF.md`.
4. `docs/decisions/DECISION_LOG.md` for anything relevant to the task at hand.

## What this project is
iJodidar — a live Flask-based matrimonial platform for the Marathi/Maharashtra community.
Currently at Overall Readiness 52/100 (see `MASTER_PROMPT.md` §3). Undergoing a structured
transformation to production-ready, mobile-capable v2. 23 audit/design documents already
exist — **do not re-audit or re-design from scratch; build forward from them** (index in
`MASTER_PROMPT.md` §4, files live under `docs/audits/`).

## Hard rules for this repository
- Delete `/ijodidar/` (duplicate directory) before any other work, if it still exists.
- The REST API (`app/api/`) is additive — never remove or break the existing HTML routes
  or session-based auth.
- Every migration needs a verified downgrade path.
- No endpoint touching auth, payments, or PII merges without a `security-auditor` pass.
- Do not start a sprint whose prerequisite sprint (`MASTER_PROMPT.md` §7) isn't done.
- `app/models.py` stays a single file until the test suite exists — the domain split is
  deliberately the last item in Sprint 6, not earlier.

## Subagents available (`.claude/agents/`)
| Agent | Use for |
|---|---|
| `product-architect` | Feature scoping, prioritization, competitive positioning |
| `solution-architect` | Cross-cutting technical decisions, conflict resolution, sprint-entry review |
| `ui-ux-architect` | Templates, navigation, design system, wireframes |
| `database-architect` | Schema, migrations, indexing, query performance |
| `backend-engineer` | Flask routes, Celery tasks, REST API implementation |
| `frontend-engineer` | Templates, JS, CSS, mobile-responsive UI, mobile app screens |
| `security-auditor` | Mandatory review before merging anything touching auth/payments/PII/new endpoints |
| `qa-lead` | Test strategy and suite build-out |
| `devops-engineer` | CI/CD, AWS infra, deployment, monitoring, rollback |
| `technical-documentation-specialist` | Keeps `PROJECT_STATUS.md`, decision log, sprint handoffs current |

Full role definitions and handoff protocol: `MASTER_PROMPT.md` §11.

## End of every session
Update `PROJECT_STATUS.md`'s v2 status section, log any decisions, and if a sprint closed,
write its handoff doc. Full protocol: `MASTER_PROMPT.md` §12.
