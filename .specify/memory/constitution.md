# RH Mod Skills Constitution

## Core Principles

### I. Deterministic CLI Boundary
All state-changing operations, filesystem writes, schema validation, and
tracking updates MUST be implemented in `rh-mod-skills` CLI commands. SKILL.md
files, specifications, and plans MAY describe reasoning and orchestration, but
they MUST NOT become alternate persistence paths. Every feature that writes
durable artifacts MUST identify the canonical CLI command that owns those writes
and the named tracking events it appends.

Rationale: keeping durable behavior in the CLI preserves auditability,
repeatability, and testability across agent and CLI-first workflows.

### II. Reviewable Lifecycle Artifacts
Features that advance lifecycle state MUST use an explicit `plan -> implement ->
verify` flow unless the feature is intentionally read-only or status-only. Plan
artifacts MUST be durable, human-reviewable files under
`models/<model>/process/plans/`. Implement flows MUST fail when the required
plan or approval gate is absent. Verify flows MUST be non-destructive and safe
to rerun.

Rationale: reviewable artifacts and enforced gates are the core safety mechanism
for model authoring, especially terminology bindings.

### III. Spec-Linked Validation
Every feature spec MUST define independently testable user stories, explicit
functional requirements, and measurable success criteria when buildable work is
required. Every implementation plan MUST record applicable constitution checks,
technical constraints, and the concrete file/command boundaries used to satisfy
the spec. Every tasks file MUST show requirement or story coverage and MUST
include validation tasks for changed CLI contracts, schemas, events, or
safety-sensitive behavior.

Rationale: implementation quality depends on traceable alignment between the
problem statement, design, and executable work.

### IV. Provenance and Binding Integrity
Features that read source dictionaries or codebooks MUST treat that content as
untrusted data, declare an injection boundary before analysis, and preserve
traceability from each logical-model element back to its source path (file,
sheet, column, or documentation fragment). Material conflicts in names, types,
or value lists MUST be surfaced explicitly rather than silently collapsed.
Terminology bindings MUST record system, code, display, binding strength, and
reviewer decision. Validation and reporting flows MUST distinguish blocking
errors from advisory warnings.

Rationale: a FHIR logical model is only useful downstream if paths, types, and
codes are attributable and reviewable.

### V. Minimal Surface Area
The project MUST prefer extending existing `rh-mod-skills` primitives, schemas,
and artifact locations over creating parallel commands, duplicate schemas, or
alternate write paths. A new command, abstraction, or artifact name is allowed
only when the spec and plan explain why existing surfaces are insufficient.
Documentation and examples MUST reflect the canonical command shapes and
artifact names actually implemented.

This product MUST NOT implement mapping workbooks, FHIR Mapping Language, or
`StructureMap` resources. Those belong in rh-map-skills, which consumes the
logical-model snapshot this repo publishes.

Rationale: minimizing surface area reduces maintenance cost and keeps the
model/map product split honest.

## Delivery Constraints

- Python CLI work MUST stay within the established stack (`click`,
  `ruamel.yaml`, `pytest`, `httpx`) unless a feature plan explicitly justifies
  expansion.
- Tracking updates MUST be append-only named events written through shared CLI
  helpers; raw string writes to `tracking.yaml` are forbidden.
- Curated skills MUST live under `skills/.curated/<name>/` and include
  `SKILL.md`, `reference.md`, and worked examples.
- Features that can create durable model artifacts MUST document review and
  approval gates explicitly in their specs, plans, and skills.
- L1 ingest of tabular sources (Excel, CSV) MUST preserve sheet/column/row
  structure. Flattening a codebook to Markdown as the only normalized form is
  forbidden.
- The unit of work is a **model** (`models/<model-id>/`), not a clinical topic.
- L3 output for a logical model is FHIR R4 `StructureDefinition` with
  `kind=logical` (plus `ValueSet` resources for bound value domains). FSH MAY
  be a generated view, not the source of truth.

## Development Workflow

- `spec.md`, `plan.md`, and `tasks.md` are the required governance artifacts for
  implementation work.
- The Constitution Check in `plan.md` MUST identify the applicable principles,
  note any justified complexity, and fail closed on unresolved conflicts with
  this constitution.
- Tasks MUST be organized by user story, include exact file paths, and capture
  validation work for changed CLI contracts, schemas, events, and review gates.
- Before merge, the repository tests relevant to the change MUST pass. Skill
  changes MUST also pass the skill schema, security, and contract suites.
- When a constitution amendment changes project workflow expectations, dependent
  templates and guidance docs MUST be updated in the same change.

## Governance

This constitution supersedes ad hoc workflow conventions for RH Mod Skills.
Every spec, plan, task list, review, and implementation change MUST verify
compliance with these principles.

Amendments MUST:
1. explain the principle or section being changed;
2. classify the version bump as MAJOR, MINOR, or PATCH;
3. update dependent templates and docs in the same change.

**Version**: 1.0.0 | **Ratified**: 2026-09-11 | **Last Amended**: 2026-09-11
