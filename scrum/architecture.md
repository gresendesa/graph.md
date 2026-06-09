# Architecture - Components, Contracts, and Flows

Document status: active
Owner: gresendesa
Creation date: 2026-06-09
Last updated: 2026-06-09

## Purpose

Record relevant changes to components, contracts, and flows.

## Records

### 2026-06-09 - CLI JSON serialization normalization

- Status: active
- Owner: gresendesa
- Context: `mdb context --json` failed when YAML metadata contained values parsed
  by PyYAML as `date` objects.
- Change: `src/mdbind/cli.py` now routes CLI JSON output through `_json_dumps`,
  which keeps `ensure_ascii=False` as the default and serializes non-JSON-native
  values with `default=str`.
- Contract impact: No output shape change. YAML date metadata is emitted as a
  JSON string, for example `"created_at": "2026-06-08"`.
- Flow impact: CLI JSON rendering is more tolerant of YAML metadata values while
  preserving existing command schemas.
