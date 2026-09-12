# Example: Output Artifact — `<skill-name> implement`

Structural example of L2 / L3 files this product produces. Clinical
decision-table examples from rh-skills do not apply here.

---

## L2 inventory (illustrative)

**Location**: `models/tumor-registry/structured/inventory.yaml`

```yaml
name: inventory
model: tumor-registry
version: "0.1.0"
entities:
  - id: PatientIdentification
    source:
      file: codebook.xlsx
      sheet: Demographics
    elements:
      - path: PatientIdentification.medicalRecordNumber
        datatype: string
        cardinality: "1..1"
      - path: PatientIdentification.sex
        datatype: code
        cardinality: "0..1"
        value_domain: sex-local
```

---

## L3 logical model (illustrative)

**Location**: `models/tumor-registry/computable/StructureDefinition-tumor-registry.json`

```json
{
  "resourceType": "StructureDefinition",
  "kind": "logical",
  "abstract": false,
  "type": "TumorRegistry",
  "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Base"
}
```

Formalize emits a full differential; this stub only shows the kind that
rh-map-skills will consume.
