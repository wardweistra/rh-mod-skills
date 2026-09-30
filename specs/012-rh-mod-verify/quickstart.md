# Quickstart: verify ENCR

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr          # Next: verify
rh-mod-skills verify encr
rh-mod-skills status encr          # still Next: verify
```

Expect coverage with unbound leftover counts, all five stages `pass`, and `validator=not-run`. Tracking.yaml must not change.
