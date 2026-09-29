# Data model: formalize

## Formalize plan

**Path**: `models/<id>/process/plans/formalize-plan.yaml`

```yaml
model: encr
status: draft
canonical: http://example.org/fhir/StructureDefinition/encr
version: "0.1.0"
name: Encr
unknown_datatype: []          # paths; implement fails if non-empty
unknown_cardinality: 112      # count defaulted to 0..1
bound: 119
unbound: 5
```

## Computable outputs

- `computable/StructureDefinition-<model>.json`
- `computable/ValueSet-<model>-<path-slug>.json` (bound only)
- `computable/snapshot.yaml`

```yaml
model: encr
canonical: http://example.org/fhir/StructureDefinition/encr
version: "0.1.0"
kind: logical
files:
  - path: models/encr/computable/StructureDefinition-encr.json
    checksum: <sha256 hex>
```
