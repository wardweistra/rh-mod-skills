# rh-mod-ig reference

## Commands

```
rh-mod-skills ig sync <model>
```

Requires `computable/snapshot.yaml`. Writes `models/<model>/ig/`. Appends
`ig_synced`. Does not run Java. Does not download `publisher.jar`.

Do not hand-edit `input/ImplementationGuide-*.json`. `ig sync` rewrites it
every time (resources + Home `definition.page`). Extra pages belong in
unmanaged markdown, not as `toc.html` / `artifacts.html` children.

## Files

| File | Who writes it | Overwrite? |
|------|----------------|------------|
| `ig/_build.sh`, `_genonce.sh`, `_updatePublisher.sh` (and `.bat`) | `ig sync` from pinned HL7 commit | only if missing or pin changed |
| `ig/ig.ini` | `ig sync` | create if missing |
| `ig/rh-mod.yaml` | `ig sync` | create if missing (reviewer-owned after that) |
| `ig/.gitignore` | `ig sync` | create if missing |
| `ig/input/includes/menu.xml` | `ig sync` | create if missing (reviewer-owned after that) |
| `ig/input/pagecontent/index.md` | `ig sync` | create if missing (reviewer-owned after that) |
| `ig/input/models/*.json` | `ig sync` from snapshot SDs (all LMs) | managed |
| `ig/input/vocabulary/*.json` | `ig sync` from snapshot ValueSets | managed |
| `ig/input/ImplementationGuide-*.json` | `ig sync` every time | managed (rewritten) |
| `ig/managed-files.yaml` | `ig sync` every time | rewritten |

One IG tree per **tracking** model (`models/<tracking-id>/ig/`), even when
formalize emitted N StructureDefinitions. `definition.resource` lists every SD
(+ ValueSets). No ConceptMap directory.

`fhir.base.template` includes `{% include menu.xml %}`. Without
`input/includes/menu.xml`, Jekyll dies after snapshots succeed.

## Page tree vs auto-pages

`definition.page` is **Home only**: `nameUrl: index.html`, `generation: markdown`.
Publisher 2.3.x already generates `toc.html` and `artifacts.html`. Menu links
to those files are required; listing them as `definition.page` children raises
“file …/toc.html is being generated more than once.”

`input/pagecontent/index.md` is not a page until it is on `definition.page`.
The CLI owns that link. Do not add TOC or Artifacts to the page tree.

## After sync

From `models/<model>/ig/` (Java on the reviewer machine):

```bash
./_updatePublisher.sh -y
./_genonce.sh          # or ./_build.sh — same publisher, no SUSHI
```

JSON-only path: do not run SUSHI. `status` next remains `verify`.
`fhir.base.template` “no longer considered secure” (2026-03 npm notice) is
advisory and does not stop the build.

Java 26 sqlite native-access warnings and “not a git repository” are noise.

## Publisher log → fix

| Log | Cause | Where to fix |
|-----|--------|----------------|
| Jekyll Could not locate … `menu.xml` | missing include | unmanaged `input/includes/menu.xml` (re-run `ig sync` if the file was never created) |
| `index.html` / `toc.html` / `artifacts.html` cannot be resolved | no Home `definition.page` | CLI owns IG JSON; re-run `ig sync` — do not hand-edit |
| `toc.html` is being generated more than once | TOC listed on `definition.page` | remove those children; Home only |
| Invalid path 'X' must start with Y | SD `url` last segment ≠ differential root | formalize `canonical_base` + lm-id, then re-formalize |
| path name portion exceeds 64 chars | element id / path segment | extract slug, then specify + formalize |
| `fhir.base.template` no longer considered secure | 2026-03 npm notice | `ig.ini` template choice (advisory) |
