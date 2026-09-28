# Feature Specification: annotate review (HTML export / picks import)

**Feature Branch**: `008-annotate-review`  
**Created**: 2026-09-28  
**Status**: Implemented  
**Depends On**: [005 — rh-mod-annotate](../005-rh-mod-annotate/)  
**Input**: Give reviewers a readable HTML view of an enriched annotate plan so they can pick a terminology candidate (or unbound / skip / replace) without editing YAML. The CLI generates the page from the plan. The page downloads a small picks file. Import writes those choices back onto the plan by path. The plan stays canonical. Import does not write bindings. Approve then implement remain the gate. HTML-first; Excel is out of this slice. No local web server.

## Clarifications

### Session 2026-09-28

- Q: HTML or Excel first? → A: HTML first. Excel is a later exporter of the same internal row model, not this spec.
- Q: What is imported? → A: A picks file (path + decision + pick rank + reason, plus override fields only for replace). Not a re-parse of candidate codes from the HTML.
- Q: Does import write bindings? → A: No. It updates the annotate plan only. If the plan was approved, import sets it back to draft. Then existing approve → implement.
- Q: Whole inventory or current plan? → A: Current plan only. A `gesl` slice stays one element. `--all-undecided` is whatever the plan already listed.
- Q: Local web server? → A: No. Static HTML written by the CLI. The reviewer opens the file and downloads picks.
- Q: May the reviewer edit candidate codes in the page? → A: No. Pick is by rank (1–5) against the plan’s candidate list. A typed override is `replace` with explicit chosen system/code/display.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export a review page for a planned slice (Priority: P1)

An informaticist has enriched `gesl` on `nkr-breast` (three SNOMED candidates). They run annotate export. The CLI writes a single HTML file from the plan. Opening it shows the inventory display, query, and the ranked candidates as a choice list. No bindings file is touched. No ReasonHub call.

**Why this priority**: Without a deterministic projection, the HTML would be a one-off agent page and could not be re-imported.

**Independent Test**: On a consumer with an enriched `gesl` annotate plan, export writes HTML under the model’s process/plans. The page contains the path, display, and each candidate’s code and display. `bindings.yaml` is unchanged. Tracking has no new event type required for a successful export (or a single export event if the plan records one — see FR).

**Acceptance Scenarios**:

1. **Given** an enriched draft annotate plan for `gesl`, **When** annotate export runs, **Then** an HTML review file is written from that plan and lists the same candidates in rank order.
2. **Given** no annotate plan, **When** export runs, **Then** it fails closed and writes no HTML.
3. **Given** a plan with empty candidates, **When** export runs, **Then** the page still lists the element and allows unbound/skip (not a fake code).

---

### User Story 2 - Pick a candidate and import onto the plan (Priority: P1)

The reviewer opens the HTML, selects candidate rank 1 (Biological sex), and downloads the picks file. They run annotate import. The plan’s `gesl` row becomes `decision: accept` with `chosen` copied from that candidate (system, code, display). Other planned elements are unchanged. Plan status is `draft`. Bindings are not written until they approve and implement as today.

**Why this priority**: This replaces hand-editing YAML `decision` and is the whole point of the feature.

**Independent Test**: Import a picks file that accepts `patientgegevens.gesl` at pick 1. Plan shows accept + chosen matching candidates[rank 1]. `bindings.yaml` still absent or unchanged. Then existing approve + implement binds that code.

**Acceptance Scenarios**:

1. **Given** a picks file with `decision: accept` and `pick: 1` for a planned path, **When** import runs, **Then** the plan sets accept and copies that ranked candidate into `chosen`.
2. **Given** import succeeded, **When** implement is run without approve, **Then** it still fails closed (plan is draft).
3. **Given** a picks path not on the plan, **When** import runs, **Then** it fails closed and does not add inventory rows.
4. **Given** pick 2 on a three-candidate element, **When** import runs, **Then** chosen is the rank-2 candidate, not rank 1, and the candidate list is not reordered.

---

### User Story 3 - Unbound, skip, replace, and re-import after approve (Priority: P2)

The reviewer marks a date field unbound with a reason, skips a poor match (leave undecided), or types a replace code they already chose. Import records those decisions. If they already approved the plan, import sets status back to draft so implement cannot run on stale approval. Import never writes bindings.

**Why this priority**: Same decision vocabulary as 005; the HTML must not lose unbound/skip/replace.

**Independent Test**: Picks with unbound+reason, skip/reject, and replace+chosen all update the matching plan rows. Import on an approved plan returns it to draft. Implement still requires a new approve.

**Acceptance Scenarios**:

1. **Given** picks `decision: unbound` with a reason, **When** import runs, **Then** the plan row is unbound with that reason and no chosen code is required.
2. **Given** picks `decision: reject` or skip (no pick), **When** import runs, **Then** the plan row is reject/pending so implement will skip it (element stays undecided).
3. **Given** picks `decision: replace` with chosen system/code/display, **When** import runs, **Then** the plan stores that chosen triple (not a candidate rank).
4. **Given** the plan is `approved`, **When** import runs, **Then** choices are applied and `status` becomes `draft`.
5. **Given** unbound without a reason, **When** import runs, **Then** it fails closed for that file (or that row, fail-closed overall).

---

### Edge Cases

- Export with no enrich (all `candidates: []`): page is still valid; accept with a pick fails on import (no rank to copy).
- Pick rank out of range: import fails closed.
- Picks `model` field disagrees with the CLI model argument: fail closed.
- HTML is not an import format; only the downloaded picks file is.
- Skill must not write the HTML or picks file; CLI owns those bytes.
- Mapping workbooks and Excel review files are out of scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `rh-mod-skills annotate export <model>` MUST write a static HTML review page derived only from `annotate-plan.yaml` (copy display strings and candidate fields; no ReasonHub).
- **FR-002**: The HTML MUST list each planned element (path, display, query) and its ranked candidates as a single-choice control, plus unbound and skip. Replace MAY be a distinct choice that reveals chosen system/code/display fields.
- **FR-003**: The HTML MUST offer a download of a picks YAML whose rows are path, decision, pick (rank or null), reason, and optional chosen override. Candidate codes in the page MUST NOT be the import source.
- **FR-004**: `rh-mod-skills annotate import <model> --from FILE` MUST apply picks by `path` onto the existing plan: accept+pick copies that candidate into `chosen`; unbound requires reason; replace requires chosen; reject/skip leaves the element unimplemented. MUST NOT write `bindings.yaml`.
- **FR-005**: Import MUST fail if the plan is missing, a path is unknown to the plan, pick rank is invalid, model id mismatches, or unbound lacks a reason. MUST NOT invent new plan elements.
- **FR-006**: After a successful import, plan `status` MUST be `draft` (including when it was `approved`).
- **FR-007**: Export and import MUST NOT call ReasonHub. Enrich remains the skill/MCP path.
- **FR-008**: Canonical writes remain annotate CLI. Events: keep `annotate_planned` / `element_bound` as 005; export/import MAY omit new events or append a single named event if needed for audit — they MUST NOT treat import as `element_bound`.
- **FR-009**: The annotate skill MUST tell the agent to export after enrich, let the reviewer pick, then import; the skill MUST NOT write HTML or picks YAML itself.
- **FR-010**: Excel / mapping.xlsx MUST NOT be added in this feature.

### Key Entities

- **Review page**: Static HTML generated from the annotate plan; not stored as L2.
- **Picks file**: Small YAML of reviewer choices keyed by inventory `path`.
- **Annotate plan / bindings**: Unchanged 005 schemas, except `chosen` is filled from a picked rank on accept.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can accept one of three `gesl` candidates from the HTML without editing annotate-plan YAML, then implement binds that exact code.
- **SC-002**: Import never creates or updates `bindings.yaml` in the same command.
- **SC-003**: Re-running export after import shows the previous pick as the selected choice (plan round-trip).
- **SC-004**: 100% of HTML and picks-file bytes are written by `annotate export` / downloaded from that page; skills do not persist them.

## Assumptions

- 005 annotate CLI and skill already exist. Enrich has already recorded candidates.
- Consumer cwd is `example-project/` (or `RH_REPO_ROOT`).
- Default binding strength stays `example` unless the picks file or plan already set another strength (this slice need not add a strength picker).
- Specify/formalize and extract-role review are out of scope.

## Out of Scope

- Excel review workbook
- Local HTTP server
- Importing HTML as a document
- Changing ReasonHub / enrich
- Extract plan / column-role UI
- Mapping workbooks, FML, StructureMap
