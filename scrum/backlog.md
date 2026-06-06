# Backlog - Consolidator

Document status: active
Owner: gresendesa
Creation date: 2026-04-08
Last updated: 2026-06-06

## Purpose

This file is a synthetic consolidator of backlog items.

Full details for each item are in dedicated files under scrum/backlog/.

## Convention

- Backlog item: B-XXX
- Detailed file: scrum/backlog/B-XXX.md

## Summary

### Completed

| ID    | Title                                        | Sprint      |
|-------|----------------------------------------------|-------------|
| B-001 | Project setup and data models                | SPR-2026-01 |
| B-002 | Markdown parser and section discovery        | SPR-2026-01 |
| B-003 | Directive tokenization (@ref, @include)      | SPR-2026-01 |
| B-004 | Repository indexing and graph                | SPR-2026-01 |
| B-005 | CLI - mdgraph get command                    | SPR-2026-01 |
| B-006 | CLI - mdgraph tree command                   | SPR-2026-01 |
| B-007 | CLI - mdgraph compose command                | SPR-2026-01 |
| B-008 | Cycle detection and resolution               | SPR-2026-01 |
| B-009 | Persistent index cache                       | SPR-2026-01 |
| B-010 | README and examples directory                | SPR-2026-01 |
| B-011 | Directive syntax renderable as MD link       | SPR-2026-02 |
| B-012 | Configurable depth in tree command           | SPR-2026-03 |
| B-013 | YAML syntax for section metadata block       | SPR-2026-04 |
| B-014 | Translate docs + expand specification.md §1–§11 | SPR-2026-05 (partial) |
| B-015 | mdgraph validate                             | SPR-2026-05 |
| B-025 | --json flag for get and tree                 | SPR-2026-05 |

### Pending

| ID    | Title                                               | PO Priority   | Risk  | Tier       | Deps         |
|-------|-----------------------------------------------------|---------------|-------|------------|--------------|
| B-016 | mdgraph context: structured node context for agents | 1 (critical)  | 2     | IA v1      | B-004        |
| B-017 | mdgraph backlinks: dedicated backlinks command      | 2 (high)      | 1     | IA v1      | B-004        |
| B-018 | mdgraph search: metadata-based graph search         | 1 (critical)  | 2     | IA v1      | B-004,B-013  |
| B-019 | mdgraph impact: reverse BFS affected nodes          | 1 (critical)  | 2     | IA v1      | B-004        |
| B-020 | mdgraph neighbors: graph neighborhood exploration   | 2 (high)      | 1     | IA v2      | B-004        |
| B-021 | mdgraph explain: find paths between nodes           | 2 (high)      | 2     | IA v2      | B-004        |
| B-022 | mdgraph diff: structural diff against git history   | 2 (high)      | 3     | IA v2      | B-004        |
| B-023 | mdgraph query: advanced metadata query language     | 2 (high)      | 3     | IA v2      | B-018        |
| B-024 | mdgraph context-compose: LLM context materialization| 1 (critical)  | 2     | IA v2      | B-007,B-016  |

### Planned

(none — all items concluded or pending)

## Template for new items
