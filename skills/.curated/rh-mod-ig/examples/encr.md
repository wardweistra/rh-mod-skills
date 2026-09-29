# Example: IG tree for formalized ENCR

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills ig sync encr
```

Confirm `models/encr/ig/rh-mod.yaml` package id. Then:

```bash
cd models/encr/ig
./_updatePublisher.sh -y
./_build.sh
```

`computable/` is unchanged. `rh-mod-skills status encr` still prints `Next: verify`.
Mapping is rh-map-skills, not this tree.
