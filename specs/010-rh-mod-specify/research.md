# Research: rh-mod-specify

**Date**: 2026-09-29

## 1. Whole-model gate

**Decision**: Specify plan fails unless every inventory path has a bindings row (`bound` or `unbound`). No `--element` slice.

**Rationale**: FR-008 requires an LM sufficient to formalize without the codebook. ENCR is annotate-complete; nkr-breast is not.

## 2. Types are reviewer-filled

**Decision**: CLI copies inventory datatype only if it matches a recognized FHIR type (case-insensitive). `unknown`, `F`, `A`, and other codebook letters → `unknown`. Skill/reviewer edits the plan YAML.

**Rationale**: Same honesty as extract (`*dat` ≠ date) and annotate (no invented codes).

## 3. Binding snapshot, not a join

**Decision**: Plan/LM store a copy of the bindings row on each element. Implement does not re-read bindings except that plan was built from them.

**Rationale**: LM must stand alone (001 FR-008).

## 4. Events

**Decision**: Implement appends `model_specified` (001 list). Plan writes no new event type.

**Rationale**: Status already flips to `specified` on that event. `specify_planned` is not in the 001 reserved list.

## 5. Recognized types

R4 primitives plus `CodeableConcept`, `Coding`, `Identifier`, `Quantity`, `Period`, `Range`, `Ratio`, `HumanName`, `Address`, `ContactPoint`, `Attachment`, `Reference`. Cardinality copied only if `n..m` or `n..*`.
