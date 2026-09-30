# CLI: ig (013)

```
rh-mod-skills ig sync <model>
```

### sync

Requires `computable/snapshot.yaml`. Writes `models/<model>/ig/`. Downloads pinned launcher scripts if missing or pin changed. Creates `ig.ini`, `rh-mod.yaml`, `ig/.gitignore`, `input/includes/menu.xml`, and `input/pagecontent/index.md` only if absent. Mirrors snapshot JSON into `input/models` and `input/vocabulary`. Rewrites ImplementationGuide (resources + Home `definition.page`) and `managed-files.yaml`. Deletes managed files no longer in the snapshot. Appends `ig_synced`. Does not write `publisher.jar`. Does not invoke Java.
