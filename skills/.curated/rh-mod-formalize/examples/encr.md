# Example: formalize multi-LM ENCR recommendations

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status recommendations
# Stage: specified
# Next: formalize

rh-mod-skills formalize plan recommendations
```

Open `models/recommendations/process/plans/formalize-plan.yaml`. Set:

```yaml
canonical_base: https://encr.eu/fhir/recommendations
version: "0.1.0"
```

Expect derived URLs for `encr-patient`, `encr-diagnosis`, `encr-hospital` (lm-ids
from specify regroup). If `unknown_datatype` lists paths, return to specify first.

```bash
rh-mod-skills formalize approve recommendations
rh-mod-skills formalize implement recommendations
rh-mod-skills formalize verify recommendations
```

Expect three `StructureDefinition-*.json` files, ValueSets only for authored
`value_set` elements, `snapshot.yaml` listing all files + `canonical_base`, and
**zero** ConceptMap resources.
