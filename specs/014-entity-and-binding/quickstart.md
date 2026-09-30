# Quickstart: mappings then multi-LM (014)

Design-only until tasks/implement land. Intended reviewer flow after CLI ships.

## Epic A — multi-system mappings (no fake ValueSet)

```bash
cd /path/to/consumer   # e.g. ENCR recommendations tracking model
rh-mod-skills annotate plan <model> --element sex-at-birth --system loinc --system snomed
# skill: ReasonHub search → annotate enrich candidates for both systems
# plan YAML: accept one candidate per system into mappings[]
rh-mod-skills annotate approve <model>
rh-mod-skills annotate implement <model>
rh-mod-skills annotate verify <model>    # mapped / unbound counts

rh-mod-skills specify plan <model>
# types/cardinality as today; binding snapshot shows mappings[]
rh-mod-skills specify approve <model> && rh-mod-skills specify implement <model>

rh-mod-skills formalize plan <model>
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
# Expect ElementDefinition.mapping for LOINC + SNOMED on sex-at-birth
# Expect NO ValueSet for that path unless value_set was authored (phase 2)
rh-mod-skills formalize verify <model>
```

Legacy 1.0 `bindings.yaml` with root `system`/`code`/`strength`: commands fail closed — re-run annotate into 2.0. No migrate flag.

## Epic A phase 2 — optional ValueSet

Author `value_set.strength` + concepts on the annotate (or specify) plan for coded domains; re-implement annotate/specify; formalize emits ValueSet + binding only for those paths.

## Epic B — Patient / Diagnosis / Hospital split

```bash
rh-mod-skills specify plan <model>
# skill: regroup into logical_models encr-patient / encr-diagnosis / encr-hospital
# set Reference + reference.target where needed; ensure every inventory_path appears once
rh-mod-skills specify approve <model>
rh-mod-skills specify implement <model>
rh-mod-skills specify verify <model>

rh-mod-skills formalize plan <model>
# set canonical_base: https://encr.eu/fhir/recommendations
# derived: …/StructureDefinition/encr-patient (etc.)
rh-mod-skills formalize approve <model>
rh-mod-skills formalize implement <model>
# Expect StructureDefinition-encr-patient.json (and siblings) under computable/

rh-mod-skills ig sync <model>
# One IG lists all logical SDs
```

Proving canonicals:

- `https://encr.eu/fhir/recommendations/StructureDefinition/encr-patient`
- `https://encr.eu/fhir/recommendations/StructureDefinition/encr-diagnosis`
- `https://encr.eu/fhir/recommendations/StructureDefinition/encr-hospital`
