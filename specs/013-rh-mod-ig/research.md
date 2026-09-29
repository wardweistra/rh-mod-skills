# Research: rh-mod-ig

**Date**: 2026-09-29

## 1. Scripts pin

**Decision**: Copy files from `HL7/ig-publisher-scripts` commit `9e6c7de21624e99dfd6739657a7895dfbe7d1357` (main as of 2026-09-15). Raw URL:
`https://raw.githubusercontent.com/HL7/ig-publisher-scripts/<pin>/<filename>`

**Rationale**: Reproducible; tests stub HTTP so CI never depends on GitHub.

**Files**: `_build.sh`, `_build.bat`, `_genonce.sh`, `_genonce.bat`, `_gencontinuous.sh`, `_gencontinuous.bat`, `_updatePublisher.sh`, `_updatePublisher.bat`.

## 2. Input folders

**Decision**: Logical SD → `input/models/`; ValueSets → `input/vocabulary/`; IG resource → `input/ImplementationGuide-<id>.json`.

**Rationale**: [IG template guidance](https://build.fhir.org/ig/FHIR/ig-guidance/using-templates.html) names `models` for logical models and vocabulary folders for ValueSets.

## 3. ig.ini

**Decision**: Create if missing:

```
[IG]
ig = input/ImplementationGuide-<id>.json
template = fhir.base.template
```

Never overwrite.

## 4. Package sidecar

**Decision**: `ig/rh-mod.yaml` with `package_id` and `url`. Guess once from snapshot canonical + model id (`{netloc}.fhir.{model}` and `{base}/ImplementationGuide/{model}`).

## 5. No Java

**Decision**: CLI never shells to `java` or downloads `publisher.jar`. Skill points at `_build.sh` (no-SUSHI).
