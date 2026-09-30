# Feature Specification: rh-mod-ig

**Feature Branch**: `013-rh-mod-ig`  
**Created**: 2026-09-29  
**Status**: Draft  
**Depends On**: [001 — Framework](../001-rh-mod-framework/), [011 — formalize](../011-rh-mod-formalize/)  
**Input**: Stage a FHIR IG Publisher tree from an existing formalize snapshot so a reviewer can run the [HL7 IG Publisher scripts](https://github.com/HL7/ig-publisher-scripts) locally. `computable/` remains the L3 pin. The CLI must not download `publisher.jar` or invoke Java. Proving consumer: formalized ENCR.

## Clarifications

### Session 2026-09-29

- Q: New lifecycle stage / plan → approve? → A: No. Ungated `ig sync` is a generated view of an already-approved snapshot (same idea as constitution: FSH is not source of truth).
- Q: Run the publisher from this CLI? → A: No. Copy pinned launcher scripts and document `./_build.sh`. Java and `publisher.jar` stay outside rh-mod-skills.
- Q: Resource folders? → A: Logical `StructureDefinition` → `input/models/`; ValueSets → `input/vocabulary/`; `ImplementationGuide` → `input/ImplementationGuide-<id>.json`.
- Q: Overwrite `ig.ini`? → A: Create if missing. Never clobber reviewer edits.
- Q: Package id / IG URL? → A: Sidecar created on first sync with a guess from the snapshot canonical; never overwrite if present.
- Q: `status` next? → A: Stays `verify`. Publishing is optional.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scaffold an IG tree from a snapshot (Priority: P1)

An informaticist has formalized ENCR. They run `ig sync`. The CLI creates `models/encr/ig/` if needed, copies pinned HL7 launcher scripts, writes `ig.ini` if absent, writes a first-time package-id sidecar, creates `input/includes/menu.xml` and `input/pagecontent/index.md` if absent, copies snapshot JSON into the IG input folders, and writes an `ImplementationGuide` with those resources plus Home-only `definition.page`. `computable/` is unchanged. No `publisher.jar`.

**Why this priority**: This is the handoff to the publisher without making Java a product dependency.

**Independent Test**: On a formalized mini model with HTTP downloads stubbed, `ig sync` produces `ig/ig.ini`, the script files, `input/includes/menu.xml`, `input/pagecontent/index.md`, `input/models/StructureDefinition-*.json`, `input/vocabulary/ValueSet-*.json` (bound only), and `input/ImplementationGuide-*.json` with Home `definition.page` (`index.html` / markdown) and no TOC/Artifacts children. Snapshot YAML is not copied. Tracking may record `ig_synced` but must not change `status` next.

**Acceptance Scenarios**:

1. **Given** a formalize snapshot, **When** `ig sync` runs, **Then** `models/<id>/ig/` contains scripts, `ig.ini`, `menu.xml`, `index.md`, managed JSON in the folders above, and a generated ImplementationGuide listing every copied resource with Home-only `definition.page`.
2. **Given** no snapshot, **When** `ig sync` runs, **Then** it fails closed and writes no IG tree.
3. **Given** a successful sync, **When** `publisher.jar` is sought under `ig/`, **Then** it is absent.

---

### User Story 2 - Idempotent sync (update / remove, keep reviewer files) (Priority: P1)

A second sync after formalize changed the ValueSet set updates copies, deletes managed JSON that left the snapshot, and leaves `ig.ini`, the sidecar, and unmanaged extra files alone.

**Why this priority**: ENCR re-formalize must not accumulate stale ValueSets or wipe template edits.

**Independent Test**: After first sync, edit `ig.ini`, `index.md`, and `menu.xml`, add an unmanaged file, remove one ValueSet from the snapshot list (or computable). Second sync refreshes remaining JSON, removes the stale managed ValueSet, keeps `ig.ini` / `index.md` / `menu.xml` text and the extra file. Scripts already at the pin are not re-fetched.

**Acceptance Scenarios**:

1. **Given** an existing `ig.ini` the reviewer changed, **When** sync runs again, **Then** `ig.ini` bytes are unchanged.
2. **Given** a snapshot that no longer lists a ValueSet file, **When** sync runs, **Then** that managed file is deleted from `input/vocabulary/` and dropped from the ImplementationGuide.
3. **Given** an unmanaged file under `ig/input/`, **When** sync runs, **Then** it remains.

---

### User Story 3 - Skill tells the reviewer how to publish (Priority: P2)

The curated skill runs `ig sync` via CLI, then tells the reviewer to `cd` into `ig/` and run `_updatePublisher.sh` then `_genonce.sh` or `_build.sh`. It does not run Java itself. It documents the publisher contract (menu.xml, Home-only page tree, error table) and does not tell the agent to hand-edit ImplementationGuide JSON.

**Why this priority**: Scripts without a skill become unused.

**Independent Test**: Skill pack exists (`SKILL.md`, `reference.md`, example). Formalize/status skills mention optional `rh-mod-ig` without changing `Next: verify`.

**Acceptance Scenarios**:

1. **Given** the skill, **When** an agent follows it, **Then** durable writes go only through `rh-mod-skills ig sync`.
2. **Given** `status` after sync, **When** next is read, **Then** it is still `verify`.

---

### Edge Cases

- Re-download scripts only if missing or pin in the managed manifest differs from the CLI pin.
- Network failure downloading scripts → fail closed; do not leave a half-written script set without recording the pin.
- `snapshot.yaml` is never an IG input.
- Mapping.xlsx / FML / StructureMap / FSH are not written.
- Unix scripts get execute permission; Windows `.bat` copies are included.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Canonical command is `rh-mod-skills ig sync <model>`. Skills MUST NOT write the IG tree. MUST require `computable/snapshot.yaml`. MUST NOT run Java or download `publisher.jar`.
- **FR-002**: MUST write under `models/<model>/ig/` (sibling of `computable/`). MUST copy [ig-publisher-scripts](https://github.com/HL7/ig-publisher-scripts) launcher files from a **pinned commit** via HTTP. MUST create `ig.ini` only if missing (`ig` + `template = fhir.base.template`).
- **FR-003**: MUST copy snapshot JSON: logical StructureDefinition → `input/models/`; ValueSets → `input/vocabulary/`. MUST write `input/ImplementationGuide-<id>.json` every sync with `definition.resource` plus Home-only `definition.page` (`nameUrl: index.html`, `generation: markdown`; no TOC/Artifacts children). MUST NOT copy `snapshot.yaml`.
- **FR-004**: MUST keep a managed-file list. Second sync MUST update managed copies, DELETE managed files no longer in the snapshot, and MUST NOT delete unmanaged files or existing `ig.ini` / package sidecar / `menu.xml` / `index.md`. First sync MUST create `input/includes/menu.xml` and `input/pagecontent/index.md` if missing.
- **FR-005**: First sync MUST guess `package_id` and IG canonical from the snapshot canonical + model id into a sidecar; later syncs MUST reuse those values.
- **FR-006**: MAY append `ig_synced`. MUST NOT change `status` next (still `verify`).
- **FR-007**: Curated skill `rh-mod-ig` MUST instruct: sync via CLI, then run `_updatePublisher.sh` and `_genonce.sh` or `_build.sh` from `ig/` (no-SUSHI). MUST document the publisher contract (menu include, Home-only page tree, error triage). MUST write `ig/.gitignore` if missing (`output/`, `temp/`, `input-cache/`, `*.jar`).
- **FR-008**: Tests MUST NOT hit the live GitHub network (stub HTTP).

### Key Entities

- **IG tree**: Generated publisher root under `models/<id>/ig/`.
- **Managed file list**: Paths the CLI may update or delete.
- **Package sidecar**: Reviewer-owned `package_id` and IG URL after first guess.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One `ig sync` on a formalized model produces a publisher-ready tree (scripts + `ig.ini` + Home page + `menu.xml` + IG resource + snapshot JSON in the correct input folders) without a `publisher.jar`.
- **SC-002**: A second sync after a ValueSet is removed from the snapshot deletes that managed file in 100% of test runs and leaves a customized `ig.ini` unchanged.
- **SC-003**: `status` next remains `verify` after sync in 100% of test runs.
- **SC-004**: 0 mapping/FML/FSH/publisher.jar files are written by the command.

## Assumptions

- Formalized ENCR is the manual proving consumer. Unit tests stub script downloads.
- Template default is `fhir.base.template` (publisher resolves `#current` if unspecified).
- Reviewers have Java installed themselves if they run `_build.sh`.
- 012 verify coordinator is independent; this feature does not add an `ig` stage to `verify`.

## Out of Scope

- Invoking IG Publisher / SUSHI / Jekyll
- Downloading `publisher.jar`
- Changing formalize JSON shape
- Mapping workbooks
- Multi-model IGs
