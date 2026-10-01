# Example: specify ENCR after annotate-complete

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr
# Stage: annotating
# Next: specify

rh-mod-skills specify plan encr
```

Edit `models/encr/process/plans/specify-plan.yaml`: set `date-of-birth` to
`datatype: date` and `cardinality: 0..1` if that is honest; leave codebook
`F`/`A` fields `unknown` unless a real FHIR type is known.

```bash
rh-mod-skills specify approve encr
rh-mod-skills specify implement encr
rh-mod-skills specify verify encr
rh-mod-skills status encr
# Next: formalize
```

Optional regroup on the plan (before approve):

```yaml
logical_models:
  - id: encr-patient
    title: Patient
    root: true
    entities: [...]
  - id: encr-hospital
    title: Hospital
    entities: [...]
```

Every inventory path exactly once via `inventory_path`. Use `datatype: Reference`
with `reference.target: encr-hospital` for cross-LM links.
