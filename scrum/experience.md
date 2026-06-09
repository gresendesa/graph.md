# Experience - Retrospective and Process Memory

Document status: active
Owner: gresendesa
Creation date: 2026-04-08
Last updated: 2026-06-09

## Purpose

Record observed problems in the development process, their causes, and how to prevent recurrence.

## Record format

- ID:
- Date:
- Context:
- Problem:
- Impact:
- Root cause:
- Corrective action:
- Preventive action:
- Status: open | mitigated | resolved | obsolete
- Owner:

## Records

---

- ID: EXP-001
- Date: 2026-06-09
- Context: SPR-2026-11 / B-029
- Problem: `mdb context --json` crashed when section metadata contained a
  YAML date value such as `created_at: 2026-06-08`.
- Impact: JSON context output was unavailable for repositories using date-like
  metadata values.
- Root cause: PyYAML parsed the date-like scalar as a Python `date`, and the CLI
  called `json.dumps` without a serializer for non-JSON-native values.
- Corrective action: Added a CLI JSON serialization helper that uses
  `default=str` and routed CLI JSON output through it.
- Preventive action: Added regression tests for `context --json` and
  `context-compose --json` with YAML date metadata.
- Status: resolved
- Owner: gresendesa
