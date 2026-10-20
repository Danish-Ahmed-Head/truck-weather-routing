# 01 SDLC Process Description

Basis: ISO/IEC/IEEE 12207 (software life cycle processes). Version 1.0, 2026-10-20.

## 1. Chosen model: iterative-incremental

Decision recorded with the project owner on 2026-10-20 (options offered: iterative-incremental, V-model, waterfall).
Reason: the brief allows 4 days and 16 hours, so the work is cut into small increments, each fully verified
before the next. Documents are written once for the whole project and updated when an iteration changes them.

## 2. Stages, outputs and exit criteria

| Stage | 12207 process | Output | Exit criterion |
|---|---|---|---|
| Plan | Project planning | [02 Plan](02-Project-Management-Plan.md) | Tasks sized, risks listed, open questions asked |
| Requirements | Stakeholder needs, requirements definition | [03 SRS](03-SRS.md) | Every requirement has an ID and a way to verify it |
| Design | Architecture and design definition | [04 SDD](04-SDD.md) | Every requirement maps to a module |
| Implementation | Implementation | Code in `backend/`, `frontend/` | Lint clean, typecheck clean |
| Verification | Verification | [05 Plan](05-Test-Plan.md), [06 Report](06-Test-Report.md), [07 RTM](07-RTM.md) | All tests pass, no open defect above Low |
| Review and audit | Quality assurance | [08](08-Code-Review-Report.md), [09](09-Security-Audit.md), [10](10-Scalability-Performance-Audit.md) | Findings fixed or accepted in writing |
| Transition | Transition | [11 Readiness](11-Production-Readiness-Review.md) | Checklist has no unexplained open item |
| Operation and maintenance | Operation, maintenance | [12 Guide](12-Operations-Maintenance-Guide.md) | Runbook and upgrade steps exist |

## 3. The task loop

Every task from the plan goes through this loop. A task is not done until the loop ends without a finding.

1. **Build** the smallest change that fully meets the requirement (keep changes minimal: no unrequested features).
2. **Check** statically: `ruff`, `tsc --noEmit`, `django check`.
3. **Test**: unit and integration tests; add a test for every new branch.
4. **Run** the real app and use it (browser for UI changes).
5. **Verify** against the requirement and read the code line by line for errors.
6. **Fix** any finding, then repeat from step 2. Record each finding in the defect log in doc 06.

## 4. Definition of done (per task)

Code written; lint and typecheck clean; tests pass; behaviour seen running; finding list empty; documents
touched by the change updated; change committed locally. Pushing, deploying and submitting are never part of
"done" and need the owner's explicit yes.

## 5. Roles and tools

| Role | Who |
|---|---|
| Owner, developer, tester, reviewer, author of docs, submitter | Danish Ahmed |

Tools and exact versions are listed in [02 Plan, section 6](02-Project-Management-Plan.md).

## 6. Configuration management

Git repository `D:\Dev\truck-weather-routing`, commits as Danish Ahmed.
Dependency versions are pinned exactly in `requirements.txt` and `package.json`/`package-lock.json`.
