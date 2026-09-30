# Example: IG tree for formalized ENCR

Canonical on the formalize plan must end with the model id (`…/encr`), not
`…/recommendations`. Path segments over 64 characters fail formalize; re-extract
if the publisher log says that.

```bash
cd ~/fhir-specs/r4/ENCR
rh-mod-skills ig sync encr
```

Confirm `models/encr/ig/rh-mod.yaml` package id. First successful layout:

```text
models/encr/ig/
  ig.ini                         # template = fhir.base.template
  rh-mod.yaml                    # reviewer-owned package_id / url
  _genonce.sh / _build.sh / _updatePublisher.sh
  input/
    includes/menu.xml            # Home, TOC, Artifacts links (unmanaged after first sync)
    pagecontent/index.md         # Home markdown (unmanaged after first sync)
    models/StructureDefinition-encr.json
    vocabulary/ValueSet-*.json
    ImplementationGuide-encr.json   # resources + definition.page Home only
```

Then:

```bash
cd models/encr/ig
./_updatePublisher.sh -y
./_genonce.sh
```

Do not add `toc.html` / `artifacts.html` under `definition.page`. Do not
hand-edit the ImplementationGuide JSON — the next `ig sync` rewrites it.

`computable/` is unchanged. `rh-mod-skills status encr` still prints `Next: verify`.
Mapping is rh-map-skills, not this tree.
