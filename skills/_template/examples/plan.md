# Example: Plan Artifact — `<skill-name> plan`

This is a structural example of a plan artifact produced by
`<skill-name> plan tumor-registry`. Replace the fields with the skill's real schema.

---

## File Location

```
models/tumor-registry/process/plans/<skill-name>-plan.md
```

---

## Full Example

```markdown
---
model: tumor-registry
plan_type: <skill-name>
version: "1.0"
created: "2026-09-11T14:00:00Z"

items:
  - name: patient-identification
    source_file: codebook.xlsx
    source_sheet: Demographics
    description: "Patient identifiers and demographics columns"

  - name: diagnosis-coding
    source_file: codebook.xlsx
    source_sheet: Diagnosis
    description: "Primary diagnosis codes and dates"
---

# Extract plan — tumor-registry

## Intent

Derive an element inventory from the NAACCR-style codebook workbook, keeping
sheet and column provenance so later annotation and FHIR logical-model
formalize can trace every path.

## Proposed entities

| Entity | Source sheet | Notes |
|--------|----------------|-------|
| PatientIdentification | Demographics | MRN, birth date, sex |
| Diagnosis | Diagnosis | Site, histology, behaviour |

## Open questions

- Sex value domain uses local codes M/F/U — bind in annotate, do not guess here.
```
