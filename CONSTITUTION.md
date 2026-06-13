# CONSTITUTION - graph.md

Version: 1.1
Status: Active
Owner: gresendesa
Official language: English

## 0. Official Language

The official language of this project is **English**.

All documentation, specification, code comments, commit messages, and scrum files
must be written in English. The only exceptions are:
- Conversations with the PO (owner), which may occur in any language.
- Legacy content predating this constitution version, which will be migrated progressively.

## 1. Purpose

Build a CLI tool as specified in specification.md.

## 2. Non-Negotiable Rules

1. No delivery is complete without documented manual testing.
2. No delivery is complete without a regression checklist executed.
3. Automated tests are mandatory in the development process.
4. Sprint commits only occur after explicit PO acceptance.
5. Technical closure must follow one commit per sprint per repository involved.

## 3. Strategic Priority

Current priority order:
1. Implementation and documentation

## 4. Branch and Change Policy

Branch model:
- Simplified Git Flow.

Change approval:
- Only the owner approves changes to the constitution and memory guidelines.

Accepted release risk:
- Medium (post-release adjustments are accepted when necessary).

## 4.1 Naming Convention

Official ID standards:

1. Backlog items
- Format: B-XXX
- Example: B-001

2. Sprints
- Format: SPR-YYYY-NN
- Example: SPR-2026-01

3. Sprint internal tasks
- Format: S{N}-TXX
- Example: S1-T03

Rules:
- IDs cannot be reused.
- Discontinued IDs must be marked as obsolete.
- Any new item must have an ID before entering doing.

## 5. Definition of Done (DoD)

To mark any item as done, the following is mandatory:
1. Documented manual test.
2. Regression checklist executed.
3. Records updated in project memory files under scrum/.
4. Manual validation executed on rebuilt/reinstantiated containers at sprint close.
5. Final commit only after explicit PO acceptance with system running.
6. Automated tests in `tests/` executed successfully (no failures).

## 5.2 Sprint Closure Gate (mandatory)

At sprint closure, the following is mandatory:
1. Rebuild local images with a stable tag (do not create an image per sprint).
2. Tear down previous instance and bring up new instance for validation.
3. Obtain explicit PO acceptance in a running environment.
4. Execute one commit per sprint per repository involved in the scope.

## 5.1 Sprint Planning (mandatory)

Every sprint must go through a formal planning session, conducted by the agent with owner participation.

Planning requirements:
1. Ask the PO for the priority of eligible backlog items.
2. Record/update the PO Priority field in the backlog.
3. Select backlog items for the sprint respecting PO priority.
4. Break items into technical tasks.
5. Calculate risk per task and aggregate sprint risk.
6. Define execution order.
7. Record anticipated blockers and mitigations.

PO Priority scale:
- 1 = critical
- 2 = high
- 3 = medium
- 4 = low

Rule:
- No item enters a sprint without a defined PO Priority.

Task risk scale:
- low = 1
- medium = 2
- high = 3

Sprint risk calculation:
- Simple weighted average of selected task risks.
- Final classification:
  - <= 1.4: low
  - > 1.4 and <= 2.3: medium
  - > 2.3: high

## 6. Agent Memory Management

The scrum/ folder is the operational memory of the project and must follow these rules:

0. Workspace Configuration (.mdb/config.yaml)
- The project workspace configuration must reside in `.mdb/config.yaml` at the root of the repository.
- Placing this configuration in the repository root rather than inside the memory folder itself serves as a project-wide indicator that the workspace is managed by `mdbind`, maps project-wide variables, and enables `mdb` CLI commands to automatically resolve configuration settings (like `--root`). The dedicated `.mdb/` directory keeps the repository root clean while leaving space for future local caches.

1. backlog.md
- Must act as a synthetic backlog consolidator.
- Must contain only ID, title, status, PO priority, risk, and pointer to the detailed file.

2. backlog/B-XXX.md
- Each backlog item must have its own file under scrum/backlog/.
- The detailed file must contain scope, acceptance criteria, dependencies, owner, and update history.

3. sprint.md
- Must act as a synthetic sprint consolidator.
- Must contain only summary status, focus, risk, and pointer to the detailed file.

4. sprint/SPR-YYYY-NN.md
- Each sprint must have its own file under scrum/sprint/.
- The detailed file must contain planning, tasks, risk, execution, blockers, and closure.

6. experience.md
- Must be updated at every relevant retrospective or incident.
- Must record problem, root cause, corrective action, and prevention.

7. decisions.md
- Must maintain a history of decisions about memory architecture and process governance.
- Each decision must record context, choice, impact, and date.

8. History
- History must not be deleted.
- Old content must be marked as obsolete, with date and reason.

## 7. Record Standard

Every record in scrum/ must include:
- status
- owner
- creation date
- last updated date

Default statuses:
- todo
- doing
- blocked
- done
- obsolete

## 8. Validity and Changes

This constitution takes effect immediately.
Any change requires explicit owner approval.
