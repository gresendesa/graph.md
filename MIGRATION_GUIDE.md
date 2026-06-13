# MDBind Migration Guide: Template-Based Initialization & Workflow Validation

This document guides the integration of `scrum.md`'s core features directly into a fork of `mdbind` (`mdb`). By generalizing these features, `mdb` becomes not just a markdown knowledge-graph query tool, but a complete **methodology-agnostic workspace orchestrator for AI agents**.

---

## 1. Architectural Changes Overview

We are moving away from having two separate CLI layers (`smd` on top of `mdb`). Instead, `mdb` will directly absorb:
1. **`mdb init` & `mdb pack`**: Template-driven workspace initialization from checksum-signed Zip packages.
2. **Sequential ID Generation**: A regex-based ID auto-increment scanner for new nodes/files.
3. **Workflow Validation (Status Transition Gates)**: A generalized transition checker based on graph metadata diffs.

---

## 2. Feature 1: Template Packing and Signed Initialization

To make `mdb` template-driven, it needs to package folders, calculate integrity checksums, and safely unpack them.

### `mdb pack <directory> --output <filename.zip>`
Combines a source directory of markdown templates and schema files into a deterministic, signed `.zip` package.

* **Manifest File (`manifest.yaml`)**:
  Declares metadata, required variables (to prompt the user/agent during initialization), file mapping from templates to targets, and instruction files for AI consumption.
  
* **Signature File (`SIGNATURE.yaml`)**:
  Created automatically during packaging. Contains deterministic SHA256 hashes of every file in the package (except itself) to guarantee integrity.
  ```yaml
  version: "1"
  policy: "checksum-only"
  algorithm: "sha256"
  scope: "file_contents_relative_paths_deterministic_order"
  files:
    - path: manifest.yaml
      sha256: d8a88cfa...
      size: 2098
    - path: scrum/CONSTITUTION.md.j2
      sha256: 4a3e20bf...
      size: 13152
  digest: 8cbe7a1f...  # A hash of the combined filepath+sha256 list to guarantee no tampered orders or contents.
  ```

* **Deterministic Zip Packing**:
  Files are written to the ZIP archive in alphabetical order, using a fixed epoch date (e.g., `1980-01-01 00:00:00`) to ensure that identical inputs yield byte-for-byte identical `.zip` files.

### `mdb init --template <package.zip>`
Initializes a new directory using a signed template:
1. **Signature Verification**: Verifies `SIGNATURE.yaml` against the unpacked files in memory, raising an error if any file has been modified or added.
2. **Context Resolution**: Prompts or reads key-value variables declared in `manifest.yaml` (e.g. `project_name`, `owner`, `language`).
3. **Strict Rendering**: Renders Jinja2 templates (e.g. `.j2` files) under target names, refusing to overwrite existing files unless `--force` is specified.
4. **Configuration Output**: Writes a `.mdb/config.yaml` tracking the project variables and initialized profile.

---

## 3. Feature 2: Sequential ID Auto-Increment Scanner

AI agents struggle to track the next sequential ID (like `B-001` or `SPR-2026-01`) without hallucinating. `mdb` should expose a command to compute the next valid ID by inspecting the current graph.

### Proposed Command: `mdb next-id --prefix <PREFIX> --pattern <REGEX>`
* Scans the indexed graph sections (including both their URIs and metadata values).
* Collects numbers matched by `<REGEX>`.
* Increments the maximum value found by 1, returning it formatted under the prefix.

**Example Implementation Pattern (Python):**
```python
def next_id(records, pattern=r"\bB-(\d{3})\b", prefix="B"):
    regex = re.compile(pattern)
    values = []
    for record in records:
        # Search both file URIs and YAML metadata dumps
        values.extend(int(match.group(1)) for match in regex.finditer(record.uri))
        values.extend(int(match.group(1)) for match in regex.finditer(str(record.metadata)))
    next_number = max(values, default=0) + 1
    return f"{prefix}-{next_number:03d}"
```

This generalizes sequence generation for backlogs, sprints, decision records, or experience files without hardcoding Scrum concepts.

---

## 4. Feature 3: Generalized State & Transition Validation

Instead of hardcoded Scrum validation, `mdb` can support generic state-transition policies defined in the workspace's configuration file (e.g., `.mdb/config.yaml`).

### Configuration Schema (`.mdb/config.yaml`):
```yaml
workflows:
  - name: backlog_item
    section_pattern: "^backlog\\.item\\.B-\\d{3}$"
    allowed_statuses:
      - todo
      - refined
      - planned
      - doing
      - blocked
      - done
      - obsolete
    transitions:
      - todo -> refined
      - refined -> planned
      - planned -> doing
      - doing -> blocked
      - blocked -> doing
      - doing -> done
      - "*" -> obsolete
```

### Transition Enforcement in `mdb validate`:
1. Renders the graph for the current workspace.
2. If checking against Git (like `mdb diff --since HEAD~1`), extracts changed sections.
3. For each changed section matching a `section_pattern` from the workflow:
   * Inspects the transition from its previous status (from `HEAD~1`) to the new status.
   * If the transition is not in the allowed list, returns a `MDBIND_TRANSITION_VIOLATION` error.
4. Reports standard errors like `INVALID_STATUS` if the status is not in `allowed_statuses`.

---

## 5. Migrating the Scrum Template (Base Memory)

The current `templates/scrum` folder implements the Scrum-specific layout.

### Template Layout:
* `manifest.yaml`: Declares dependencies, inputs, and template targets.
* `scrum/CONSTITUTION.md.j2`: The operational guidelines, DoD, and governance model.
* `scrum/backlog.md.j2` & `scrum/sprints.md.j2`: The synthetic list consolidators.
* `scrum/decisions.md.j2`, `scrum/experience.md.j2`, `scrum/architecture.md.j2`: Structured graph nodes.
* `scrum/schema/*.schema.yaml`: Local schemas for metadata validation of nodes.
* `scrum/instructions/LLM.md`: System-prompt instructions directing how AI agents should interact with this memory model.

### Bootstrapping the Agent in a New Project:
Once initialized, the workspace config points the agent to the base instructions (e.g., `scrum/instructions/LLM.md`). The agent reads this file at startup to understand its role as Scrum Master/Developer and how to query the graph using `mdb`.

## 6. Migration Package Structure

Reference layouts:
* `/templates/scrum/` - The ready-to-use Scrum memory files, schemas, and instructions.
* `/smd/template_packages.py` - Core logic for deterministic zip packing, SHA256 checksum signing, and variable-driven Jinja rendering.
* `/smd/templates.py` - Jinja environment helpers.
* `/smd/memory.py` - Reference scanners for sequentials and validation wrappers.

