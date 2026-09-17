# Feature Specification: ingest and status skills

**Feature Branch**: `007-ingest-status-skills`  
**Created**: 2026-09-17  
**Status**: Draft  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [002 — Ingest](../002-rh-mod-ingest/), [004 — PDF tables](../004-rh-mod-ingest-pdf/)  
**Input**: Author curated skills `rh-mod-ingest` and `rh-mod-status` for CLIs that already exist. One spec, two skills. Ingest reasons about sources, origin URLs, and PDF table include/exclude; never flattens to Markdown. Status is read-only and maps the CLI next-step to the next skill. Full skill pack (`SKILL.md`, `reference.md`, examples). Do not change ingest/status CLI unless a hole is found. Do not backfill extract/annotate companion files. `init` stays out of ingest.

## Clarifications

### Session 2026-09-17

- Q: One spec or two? → A: One spec covering both skills.
- Q: Does ingest also own `init`? → A: No. If there is no model, status tells the user to run `init`. Ingest starts only after a model exists.
- Q: Backfill extract/annotate `reference.md` and examples in this slice? → A: No.
- Q: New CLI commands? → A: No, unless a skill walkthrough finds a real hole. Status not printing projection skip reasons is not a hole — the ingest skill sends the reviewer to ingest verify.
- Q: How does this differ from rh-skills ingest? → A: Opposite L1 rule. rh-skills normalizes sources to Markdown. This product keeps Excel/CSV/PDF table structure. Markdown-only L1 is forbidden.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest the IKNL Excel via the skill (Priority: P1)

An informaticist has initialized `nkr-breast` and has the IKNL data dictionary. They invoke the ingest skill in plan mode. The skill selects the Excel file, records the public origin, and runs ingest plan. After they approve, the skill runs implement and verify. Original bytes and a table projection exist. Status next is extract. The skill never writes the projection or tracking itself.

**Why this priority**: First proving L1 path. The skill must not reintroduce Markdown flattening or bypass the ingest gate.

**Independent Test**: Follow `rh-mod-ingest` on a consumer with initialized `nkr-breast` and the IKNL fixture. After plan → approve → implement → verify, the workbook is in `sources/raw/`, a table projection has 153 data rows, and `source_added` is in tracking. No Markdown-only L1 file is required.

**Acceptance Scenarios**:

1. **Given** `nkr-breast` is initialized and the IKNL Excel path is known, **When** the ingest skill runs plan, **Then** it invokes ingest plan (not a hand-written plan file) and the draft plan lists type excel and projection tables.
2. **Given** that plan is not approved, **When** the skill is asked to implement, **Then** it does not copy sources or write projections itself; it tells the reviewer to approve first (implement still fails closed without approval).
3. **Given** an approved plan, **When** the skill runs implement then verify, **Then** the original is stored, checksummed, and verify reports a matching table projection.

---

### User Story 2 - Ingest an ENCR PDF with table include/exclude (Priority: P1)

The same informaticist initializes `encr-standard-dataset` and points the ingest skill at the 2023 standard-dataset PDF plus companion PDFs. The skill runs ingest plan, reviews detected tables, keeps Table 1 and Table 2, excludes junk detections with a reason, and leaves companions that have no reconstructable tables as register-only with an explicit skip reason. After approve and implement, extract can run on the projected tables. Page prose is not turned into rows. OCR is not attempted.

**Why this priority**: PDF table review is the ingest skill’s main judgment. Silent include of every detected grid would poison extract.

**Independent Test**: Follow the skill on the ENCR fixture set. Plan lists detected tables on the standard-dataset PDF. After reviewer include of Table 1 and Table 2 only, implement writes that projection. A companion PDF with no tables is registered skipped. No Markdown dump.

**Acceptance Scenarios**:

1. **Given** ingest plan on the ENCR 2023 standard-dataset PDF, **When** the skill reviews the plan, **Then** it treats table `decision` include/exclude as a reviewer gate and does not invent rows for excluded or undetected tables.
2. **Given** a PDF with skip reason no-text-layer, no-tables-detected, or no-tables-approved, **When** implement runs, **Then** the skill accepts register-only and does not flatten the PDF to Markdown as the only L1 form.
3. **Given** the skill is asked to “just OCR it” or “convert to Markdown”, **When** it proceeds, **Then** it refuses those as out of scope.

---

### User Story 3 - Status orients the next skill (Priority: P1)

A reviewer opens a consumer with several models and asks where things stand. The status skill runs status (all models or one). It presents the CLI output unchanged and may add one sentence that names the next curated skill (`rh-mod-ingest`, `rh-mod-extract`, `rh-mod-annotate`). When next is specify or formalize, it says those skills are not built yet. It never writes tracking. It never invents a next step the CLI did not emit.

**Why this priority**: Status is how an agent chooses which stage skill to run. A second, conflicting recommendation would split the contract.

**Independent Test**: On `example-project`, status skill for `nkr-breast` (annotating, next annotate) shows CLI stage/next and names `rh-mod-annotate`. For a model with no sources, next ingest names `rh-mod-ingest`. Empty consumer: advise `init`. Drift is not diagnosed here — ingest verify owns that.

**Acceptance Scenarios**:

1. **Given** a consumer with models, **When** the status skill runs with no model id, **Then** it shows the CLI portfolio listing and does not append a lettered menu of alternate next steps.
2. **Given** a named model, **When** the skill runs, **Then** CLI stage and next are shown as-is, plus at most one sentence mapping next to a skill name (or “not built yet”).
3. **Given** no `tracking.yaml`, **When** the skill runs, **Then** it tells the user to `init` a model and writes nothing.
4. **Given** the user asks status to check source drift, **When** the skill responds, **Then** it points at ingest verify, not a new status mode.

---

### Edge Cases

- Ingest skill invoked before `init`: stop; tell user to initialize (status/init), do not invent a model id.
- Ingest skill with no `--source` files: stop; ask which L1 files to register.
- Re-ingest with L2 present and checksum drift: skill must not silently overwrite; CLI fail-closed unless the reviewer acknowledges drift.
- Status for an unknown model id: report CLI error; do not create the model.
- Extract/annotate skills remain SKILL.md-only; this spec does not add their companion files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST provide curated skill `rh-mod-ingest` under `skills/.curated/rh-mod-ingest/` with `SKILL.md`, `reference.md`, and worked examples.
- **FR-002**: The repository MUST provide curated skill `rh-mod-status` under `skills/.curated/rh-mod-status/` with `SKILL.md`, `reference.md`, and worked examples.
- **FR-003**: `rh-mod-ingest` MUST instruct the agent to perform all durable writes through `rh-mod-skills ingest plan|approve|implement|verify`. The skill MUST NOT write `sources/`, projections, `tracking.yaml`, or the ingest plan as a persistence bypass. Reviewer edits of table `decision` on the existing plan YAML remain the 002/004 gate.
- **FR-004**: `rh-mod-ingest` MUST forbid Markdown-only L1 and OCR. Register-only with an explicit skip reason is the allowed outcome when tables cannot be reconstructed.
- **FR-005**: `rh-mod-ingest` MUST tell the agent to reason about origin URL, file type (excel / csv / pdf), and PDF table include/exclude; it MUST NOT guess extract column roles or FHIR datatypes.
- **FR-006**: `rh-mod-status` MUST be read-only. It MUST run `rh-mod-skills status` (optional model id) and MUST NOT append tracking events or a second recommendation list that disagrees with CLI `Next`.
- **FR-007**: `rh-mod-status` MAY add one sentence mapping CLI next (`ingest` / `extract` / `annotate` / `specify` / `formalize` / `init`) to the matching curated skill, or state that specify/formalize are not built yet.
- **FR-008**: `init` remains a separate command. Neither skill is an alternate `init` path.
- **FR-009**: Ingest and status CLI contracts MUST stay unchanged unless a skill walkthrough proves a blocking hole. Documentation (README, Getting Started) MUST describe these skills as present.
- **FR-010**: Canonical events remain `source_added` (ingest implement) only. Status emits none.

### Key Entities

- **Ingest skill pack**: Instructions + reference (plan fields, skip reasons, projection shape) + examples (Excel tables, PDF tables include/exclude, skipped PDF).
- **Status skill pack**: Instructions + reference (stage/next vocabulary) + example CLI output.
- **Ingest plan / sources / projections**: Unchanged from 002 and 004; skills describe them, CLI owns them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An agent following only `rh-mod-ingest` can ingest the IKNL Excel fixture into an initialized model without writing projection YAML by hand.
- **SC-002**: An agent following only `rh-mod-ingest` can ingest the ENCR standard-dataset PDF with Table 1 and Table 2 included and at least one companion left skipped, without producing a Markdown-only L1 file.
- **SC-003**: An agent following only `rh-mod-status` on `example-project` reports the same `Next` as the CLI and names the corresponding skill in at most one extra sentence.
- **SC-004**: 100% of source copies, checksums, projections, and tracking events still go through ingest CLI; status writes 0 files.

## Assumptions

- Ingest CLI (002 + 004) and status CLI (001, next-step rules from 005) already exist.
- Consumer cwd is `example-project/` (or `RH_REPO_ROOT` set); the tool repo itself refuses `init`.
- Extract, annotate, and specify/formalize skills are out of scope except as names status may mention.
- Mapping (FML, StructureMap, mapping.xlsx) remains out of scope.

## Out of Scope

- New ingest or status subcommands
- `rh-mod-ingest` calling extract
- Backfilling `rh-mod-extract` / `rh-mod-annotate` companion files
- OCR, Markdown L1, datatype guessing
- `rh-mod-specify` / `rh-mod-formalize` skill authoring
