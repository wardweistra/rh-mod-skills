# Quickstart: formalize ENCR

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr          # Next: formalize
rh-mod-skills formalize plan encr
# Confirm canonical + version on models/encr/process/plans/formalize-plan.yaml
# If unknown_datatype is non-empty, fix types in specify first
rh-mod-skills formalize approve encr
rh-mod-skills formalize implement encr
rh-mod-skills formalize verify encr
rh-mod-skills status encr          # Next: verify
```

Expect `models/encr/computable/StructureDefinition-encr.json` with `kind: logical` and a `snapshot.yaml`. No mapping.xlsx.
