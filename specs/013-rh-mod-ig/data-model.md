# Data model: ig sync

## Snapshot (read)

`computable/snapshot.yaml` — canonical, version, `files[].path` to JSON (not `snapshot.yaml`).

## Sidecar (create if missing)

**Path**: `models/<id>/ig/rh-mod.yaml`

```yaml
package_id: example.org.fhir.spec-demo
url: http://example.org/fhir/ImplementationGuide/spec-demo
```

## Managed list (CLI-owned, rewritten each sync)

**Path**: `models/<id>/ig/managed-files.yaml`

```yaml
pin: 9e6c7de21624e99dfd6739657a7895dfbe7d1357
files:
  - input/models/StructureDefinition-spec-demo.json
  - input/vocabulary/ValueSet-spec-demo-mini-sex.json
  - input/ImplementationGuide-spec-demo.json
```

## ImplementationGuide (rewritten each sync)

R4 JSON: `resourceType=ImplementationGuide`, `fhirVersion=["4.0.1"]`, `packageId` and `url` from sidecar, `version` from snapshot, `definition.resource` references for each copied SD/VS, `definition.page` Home only (`nameUrl: index.html`, `generation: markdown`). Do not add `toc.html` / `artifacts.html` as page children.

## Publisher stub (create if missing)

- `input/includes/menu.xml` — nav links to `index.html`, `toc.html`, `artifacts.html`
- `input/pagecontent/index.md` — reviewer-owned after first write

## ig.ini (create if missing)

```
[IG]
ig = input/ImplementationGuide-<id>.json
template = fhir.base.template
```
