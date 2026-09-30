# Example: formalize specified ENCR

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr
# Stage: specified
# Next: formalize

rh-mod-skills formalize plan encr
```

Open `models/encr/process/plans/formalize-plan.yaml`. Set `canonical` so the
**last path segment is `encr`** (e.g. `https://encr.eu/fhir/StructureDefinition/encr`,
not `…/recommendations`) and confirm `version`. If `unknown_datatype` lists
paths, return to `rh-mod-specify` and type those elements first — implement
will fail closed. Re-extract if a path name portion exceeds 64 characters.

```bash
rh-mod-skills formalize approve encr
rh-mod-skills formalize implement encr
rh-mod-skills formalize verify encr
rh-mod-skills status encr
# Next: verify
```

Expect `models/encr/computable/StructureDefinition-encr.json` with `kind: logical`,
one ValueSet per bound element, and `snapshot.yaml`. No `mapping.xlsx`.
