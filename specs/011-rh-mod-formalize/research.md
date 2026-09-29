# Research: rh-mod-formalize

**Date**: 2026-09-29

## 1. No FHIR Python library

**Decision**: Build R4 JSON dicts with stdlib `json`. Do not add `fhir.resources`.

**Rationale**: Constitution stack; verify checks kind/paths/checksums, not a validator binary.

## 2. Snapshot location

**Decision**: `models/<id>/computable/snapshot.yaml` next to the JSON.

**Rationale**: One handoff directory for rh-map-skills.

## 3. StructureDefinition shape

**Decision**: `kind=logical`, `derivation=specialization`, `baseDefinition=http://hl7.org/fhir/StructureDefinition/Base`, `type` = canonical URL. Root path = model id. Entities = BackboneElement. Leaves use LM datatype codes.

## 4. ValueSets

**Decision**: One include/concept ValueSet per bound element. Unbound: no VS, no ElementDefinition.binding.

## 5. Cardinality / type

**Decision**: `unknown` card → 0..1. `unknown` type → implement fails listing paths.
