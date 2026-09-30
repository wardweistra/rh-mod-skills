# Quickstart: IG tree for ENCR

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills status encr          # Next: verify
rh-mod-skills ig sync encr
# Edit models/encr/ig/rh-mod.yaml package_id/url if the guess is wrong, then sync again
cd models/encr/ig
./_updatePublisher.sh -y           # downloads publisher.jar (HL7 scripts, not rh-mod-skills)
./_build.sh                        # no SUSHI; Java required on the reviewer machine
```

Expect `input/models/StructureDefinition-encr.json` and ValueSets under `input/vocabulary/`. `computable/` is unchanged. `rh-mod-skills status encr` still prints `Next: verify`.
