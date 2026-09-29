# Quickstart: specify ENCR

From the annotate-complete consumer:

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr          # Next: specify
rh-mod-skills specify plan encr
# Edit models/encr/process/plans/specify-plan.yaml datatypes/cardinality where honest
rh-mod-skills specify approve encr
rh-mod-skills specify implement encr
rh-mod-skills specify verify encr
rh-mod-skills status encr          # Next: formalize
```

Expect `models/encr/structured/logical-model.yaml` covering all 124 paths. Inventory and bindings unchanged. No `computable/` files.
