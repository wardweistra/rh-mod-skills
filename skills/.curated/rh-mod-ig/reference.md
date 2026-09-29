# rh-mod-ig reference

## Commands

```
rh-mod-skills ig sync <model>
```

Requires `computable/snapshot.yaml`. Writes `models/<model>/ig/`. Appends
`ig_synced`. Does not run Java. Does not download `publisher.jar`.

## Files

| File | Who writes it | Overwrite? |
|------|----------------|------------|
| `ig/_build.sh` (and sibling scripts) | `ig sync` from pinned HL7 commit | only if missing or pin changed |
| `ig/ig.ini` | `ig sync` | create if missing |
| `ig/rh-mod.yaml` | `ig sync` | create if missing (reviewer-owned after that) |
| `ig/.gitignore` | `ig sync` | create if missing |
| `ig/input/models/*.json` | `ig sync` from snapshot SD | managed |
| `ig/input/vocabulary/*.json` | `ig sync` from snapshot ValueSets | managed |
| `ig/input/ImplementationGuide-*.json` | `ig sync` every time | managed (rewritten) |
| `ig/managed-files.yaml` | `ig sync` every time | rewritten |

Unmanaged files under `ig/` (pages, extra examples) are left alone. Managed JSON
that leaves the snapshot is deleted.

## After sync

From `models/<model>/ig/`, run the HL7 launchers (see
[ig-publisher-scripts](https://github.com/HL7/ig-publisher-scripts)). Use the
no-SUSHI build path: this product already emits JSON, not FSH.

`rh-mod-skills status` next remains `verify`.
