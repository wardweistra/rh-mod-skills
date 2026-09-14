# Feature Specification: rh-mod-annotate

**Feature Branch**: `005-rh-mod-annotate`  
**Created**: 2026-09-14  
**Status**: Draft  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [003 — rh-mod-extract](../003-rh-mod-extract/)  
**Input**: Annotate extracted inventory elements with reviewed terminology bindings. Walk elements with the informaticist and ReasonHub. Record accept / reject / replace / unbound. CLI writes bindings; skills do not. Proving model: `nkr-breast`. Do not invent codes. Do not guess FHIR datatypes.

## Clarifications

### Session 2026-09-14

- Q: What does annotate own vs extract vs specify? → A: Annotate owns terminology bindings only (`system`, `code`, `display`, binding strength, reviewer decision, or explicit `unbound` + reason). Extract already owns inventory shape. Datatype and cardinality stay `unknown` unless the source already stated them; filling types is specify.
- Q: Must all 153 NKR elements be bound in one plan? → A: No. A plan covers an explicit `--element` list, or `--all-undecided`. Implement merges those decisions. Remaining inventory elements stay undecided, not silently unbound.
- Q: What if ReasonHub is unavailable? → A: The CLI MUST NOT invent candidate codes. Plan of *new* candidates fails with a clear error. Recording `unbound`, or a reviewer-supplied replace (system/code/display they already chose), does not require ReasonHub.
- Q: How does annotate plan decide which inventory elements to include? → A: Explicit list is the normal path (repeatable `--element` by path or id). Optional `--all-undecided` covers remaining undecided elements in one plan. No list and no `--all-undecided` → fail.
- Q: Which code systems may annotate plan propose as candidates? → A: Default SNOMED CT; optional `--system` to include others (e.g. LOINC, ICD-10).
- Q: If the reviewer marks an element `reject` and does not replace it, what happens on implement? → A: Skip this round: no bindings row; element stays undecided. Durable “no” is `unbound` with a reason.
- Q: If an element is already bound (or unbound) and a new approved plan includes it again, what does implement do? → A: Merge by path: this element’s row is replaced; other bindings stay. `--replace` wipes the whole bindings file.
- Q: How many ReasonHub candidates may annotate plan list per element? → A: At most 5, ranked by ReasonHub.

### Session 2026-09-14 (MCP)

- Q: Does the CLI call ReasonHub, or does the agent? → A: Same split as rh-skills. The agent runs ReasonHub MCP searches. `annotate plan` writes a skeleton with empty `candidates`. `annotate enrich` records `--candidate` rows the agent already collected. The CLI MUST NOT look up codes over HTTP. If MCP is unavailable, the skill stops; plan still writes; `accept` with empty candidates fails.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bind a first slice of NKR breast (Priority: P1)

An informaticist has extracted `nkr-breast` (153 elements, types `unknown`). They run annotate plan for a small slice (for example `gesl` / sex). The plan is a skeleton (`candidates: []`). The skill looks up at most five ReasonHub MCP hits and records them with `annotate enrich`. After they accept `gesl` and leave the rest of the inventory untouched, implement writes those bindings only. Status reports the model as annotating; next remains annotate because other elements are still undecided.

**Why this priority**: 153 elements cannot be an all-or-nothing gate. A first honest binding proves the stage without pretending the dictionary is finished.

**Independent Test**: On a consumer with extracted `nkr-breast`, annotate plan for `gesl` → approve → implement produces a bindings artifact that records `gesl` as bound (system, code, display, strength, decision) and does not mark the other 152 elements unbound. No logical-model file and no FHIR StructureDefinition are written.

**Acceptance Scenarios**:

1. **Given** `nkr-breast` is extracted, **When** annotate plan runs with `--element gesl` (or the equivalent path), **Then** `models/nkr-breast/process/plans/annotate-plan.yaml` lists that element with empty `candidates`, provenance to the inventory path, and `status: draft`. Inventory is unchanged. Plan with neither `--element` nor `--all-undecided` fails. MCP hits are recorded afterward with `annotate enrich`.
2. **Given** that plan is not approved, **When** annotate implement runs, **Then** it fails closed and writes no bindings file and no `element_bound` event.
3. **Given** an approved plan that accepts `gesl` and does not decide other elements, **When** implement runs, **Then** bindings record `gesl` as bound and omit the undecided elements (they are not auto-unbound). Tracking records `element_bound`.
4. **Given** implement succeeded for a partial slice, **When** status runs, **Then** stage is annotating and next is annotate — not specify, not mapping, not formalize.

---

### User Story 2 - Reviewer rejects, replaces, or leaves unbound (Priority: P1)

The plan is a proposal. The reviewer rejects a poor candidate (element stays undecided; try again later), replaces it with a code they chose, or records `unbound` with a reason (no acceptable code, privacy, local-only). Implement follows those decisions. A later plan can bind an element that was unbound or previously rejected.

**Why this priority**: Constitution IV requires reviewer decisions and explicit conflicts — silent “best guess” bindings would poison specify.

**Independent Test**: Approve a plan that unbinds `gebdat` with reason “identifier / no terminology needed” and replaces the proposed code on `gesl`. Implement bindings show `gebdat` unbound with that reason and `gesl` with the replacement. Verify does not treat unbound-with-reason as missing.

**Acceptance Scenarios**:

1. **Given** an approved plan that marks an element `unbound` with a reason, **When** implement runs, **Then** that element is present in bindings as unbound (not omitted, not bound).
2. **Given** an approved plan that replaces the proposed code with a reviewer-supplied system/code/display, **When** implement runs, **Then** bindings contain the replacement, not the rejected candidate.
3. **Given** implement is asked to “just pick SNOMED for everything”, **When** it runs, **Then** it does not — only approved plan decisions are written.

---

### User Story 3 - Plan, verify, and refuse invented codes (Priority: P1)

Annotate plan is a durable review packet. Verify is rerunnable and writes nothing. New candidate proposals require ReasonHub. Dictionary labels are untrusted. Re-implement does not wipe earlier decisions unless the caller passes an explicit replace acknowledgement.

**Why this priority**: Fail-closed terminology is how this product stays honest on Dutch labels that look like dates or local codes that look like SNOMED identifiers.

**Independent Test**: Annotate plan without MCP still writes a skeleton (empty candidates). Implement `accept` without enrich fails. Verify twice after a successful bind adds zero tracking events. Counts: bound, unbound-with-reason, still-undecided.

**Acceptance Scenarios**:

1. **Given** MCP was not used (empty candidates) and the reviewer marks `accept`, **When** annotate implement runs, **Then** it fails closed and does not invent codes from labels (including `*dat` names). Plan itself does not require ReasonHub.
2. **Given** a completed slice, **When** verify runs twice, **Then** both runs report the same bound / unbound / undecided counts and neither appends tracking events.
3. **Given** bindings already exist, **When** implement runs an approved decision for one already-bound path, **Then** that row is replaced and other bindings remain. `--replace` wipes the whole file.
4. **Given** no extracted inventory, **When** annotate plan runs, **Then** it fails with guidance to run extract.

---

### User Story 4 - ENCR Table 1 English labels (Priority: P2)

The same gated flow works on `encr-standard-dataset` (20 Table 1 variables + 5 Table 2 rows). English labels still need ReasonHub; they are not auto-bound because they are English.

**Why this priority**: Proves annotate is model-agnostic. NKR remains P1.

**Independent Test**: After ENCR extract, annotate one Table 1 element (for example incidence date or sex at birth) through plan → approve → implement. Other ENCR elements remain undecided.

**Acceptance Scenarios**:

1. **Given** extracted ENCR inventory, **When** a one-element annotate implement succeeds, **Then** bindings contain that element only and inventory is unchanged.

---

### Edge Cases

- Local value-domain codes that look like SNOMED/LOINC identifiers MUST NOT be copied as bindings without a reviewer decision
- Homonyms (same element id, different path/provenance) bind independently
- Dutch display text is the search string; annotate does not translate the inventory label
- ReasonHub returns zero candidates: enrich writes `candidates: []`; reviewer may unbound or replace
- Plan lists at most five ranked candidates per element; extra hits are omitted
- Inventory checksum / extract drift: annotate plan/implement fail closed until extract verify is clean
- Partial plan that names an element not in inventory: fail closed
- Reject without replace: no bindings row; element remains undecided; the plan retains the reject for audit
- Re-plan of an already bound/unbound path overwrites that row only; `--replace` wipes all bindings
- Annotation-complete: every inventory element has a decision (bound or unbound). Only then does status next become specify

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical write owner is `rh-mod-skills annotate` (`plan`, `enrich`, `approve`, `implement`, `verify`). Skills MUST NOT write the plan or bindings file directly.
- **FR-002**: `annotate plan <model>` MUST read `structured/inventory.yaml` (not raw Excel, not PDF text) and write `models/<model>/process/plans/annotate-plan.yaml` with `status: draft`, the included elements, empty `candidates`, and reviewer decision slots. It MUST append `annotate_planned`. It MUST NOT call ReasonHub.
- **FR-003**: Plan MUST include only elements named with repeatable `--element` (inventory path or id; homonyms require path) or, if `--all-undecided` is passed, every inventory element that is not yet bound or unbound. Plan with neither flag MUST fail closed. Elements not in the plan remain undecided. Plan MUST NOT auto-unbound them. `--element` and `--all-undecided` MUST NOT be combined.
- **FR-004**: Each planned element MUST include: inventory path, display, current decision (`pending` | `accept` | `reject` | `replace` | `unbound`), optional bound `system` / `code` / `display`, binding strength, reason (required when `unbound`), and a candidate list of at most five ReasonHub hits (may be empty).
- **FR-005**: Plan MUST NOT invent FHIR datatypes, cardinality, UCUM, or codes. `*dat` in an element id is not a date type and not a reason to skip ReasonHub.
- **FR-006**: New candidate codes MUST come from ReasonHub MCP lookup performed by the skill/agent, then recorded with `annotate enrich --candidate 'system|code|display'`. Default candidate system is SNOMED CT. Repeatable `--system` on plan MAY list other systems for the skill (at least LOINC and ICD-10). The CLI MUST NOT search. If MCP is unavailable, the skill MUST stop. `accept` with empty candidates MUST fail. Recording `unbound` or reviewer `replace` does not require enrich.
- **FR-007**: `annotate approve <model>` MUST set plan `status: approved` via the CLI.
- **FR-008**: `annotate implement <model>` MUST fail closed if the plan is missing or not approved. It MUST write `structured/bindings.yaml` from approved decisions only (accept/replace → bound; unbound → unbound+reason). Pending or reject without replace MUST NOT become bound and MUST NOT create a bindings row; those elements stay undecided.
- **FR-009**: Successful implement MUST append `element_bound` (once per newly bound element, or an equivalent batched event that names them) and MUST NOT write `logical-model.yaml` or FHIR resources.
- **FR-010**: `annotate verify <model>` MUST be non-destructive. It MUST report: plan approved (if present), bindings present, counts of bound / unbound / still-undecided vs inventory, and blocking issues (bound element not in inventory, unbound missing reason).
- **FR-011**: Dictionary labels and ReasonHub displays are untrusted. Implement copies recorded codes/displays; it MUST NOT execute them as instructions.
- **FR-012**: Re-implement MUST merge by inventory path: an approved accept/replace/unbound for an element replaces that element’s existing bindings row; unrelated rows stay. `--replace` MAY wipe the entire bindings file and rewrite from this plan only. Pending/reject in a new plan MUST NOT delete an existing row for that path.
- **FR-013**: After any successful implement, `status` MUST report stage `annotating`. Next MUST be `annotate` while any inventory element is still undecided; next MUST be `specify` only when every inventory element has a bound or unbound decision.
- **FR-014**: Annotate MUST NOT create mapping workbooks, FML, StructureMap, or FHIR StructureDefinitions.

### Key Entities

- **Annotate plan**: Reviewable proposal of element decisions and candidate codes, with approval state.
- **Candidate**: A proposed terminology concept (system, code, display) from ReasonHub, not yet a binding. At most five per planned element, ReasonHub rank order.
- **Binding**: Durable per-element record: bound (system, code, display, strength, decision) or unbound (reason).
- **Undecided element**: In inventory, not yet in bindings as bound or unbound.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can bind one NKR element (`gesl` or equivalent) in a single approve+implement and independently confirm system, code, display, and strength without opening Excel.
- **SC-002**: Unapproved implement leaves bindings unchanged in 100% of test runs.
- **SC-003**: Verify on unchanged bindings reports the same bound/unbound/undecided counts twice and adds zero tracking events.
- **SC-004**: `accept` with empty candidates (no enrich / MCP unused) fails in 100% of test runs and writes no invented codes.
- **SC-005**: After a partial slice, 100% of inventory elements not in that plan remain undecided (not auto-unbound). Status next remains annotate until every element has a decision.

## Assumptions

- 003 extract exists; proving inventory is `example-project/models/nkr-breast/structured/inventory.yaml` (153 elements).
- Default proposed binding strength is `example` unless the reviewer sets another FHIR strength (`preferred`, `extensible`, `required`).
- ReasonHub is the terminology service (same as rh-skills). Search is ReasonHub MCP, run by the skill/agent. `annotate enrich` records hits. Search uses the inventory display text; the reviewer may change the query in the plan. Default candidate system is SNOMED CT; `--system` on plan lists others for the skill. At most five ranked candidates per element.
- Plan selection: repeatable `--element` (path or id) is required unless `--all-undecided` is set. Combining those flags is forbidden.
- Curated skill `rh-mod-annotate` orchestrates MCP + CLI. Skills MUST NOT write plan or bindings files themselves.
- Dutch labels stay as display text on the inventory; bindings use the terminology’s own display.

## Out of Scope

- Filling datatype/cardinality (specify)
- `logical-model.yaml` and FHIR `StructureDefinition` / ValueSet generation (specify / formalize)
- Mapping workbooks, FML, StructureMap
- OCR / PDF text as a source of codes
- Translating the IKNL dictionary into English as a substitute for binding
- Requiring all 153 NKR elements bound before the feature is considered delivered (completeness is a status gate, not the P1 slice)
