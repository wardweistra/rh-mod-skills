# Example: verify formalized ENCR

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr
# Stage: formalized
# Next: verify

rh-mod-skills verify encr
# coverage: inventory=… bound=… unbound=…
# ingest/extract/annotate/specify/formalize: pass
# advisory: unbound=… validator=not-run

rh-mod-skills status encr
# Next: verify
```

Unbound leftover counts stay visible. Do not treat them as a failed
formalize. Do not run a FHIR validator binary. Mapping is rh-map-skills.
