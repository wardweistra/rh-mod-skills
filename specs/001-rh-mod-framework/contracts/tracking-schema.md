# Tracking schema contract (001)

Canonical YAML schema will be implemented at `schemas/tracking-schema.yaml` and bundled to `src/rh_mod_skills/schemas/` via `make sync-schemas`.

```yaml
schema_version: "1.0"

# <consumer-root>/tracking.yaml
# models/<id>/sources/ holds L1 files (002). No root-level sources: list.

structure:
  schema_version: string          # "1.0"
  models:
    - name: string
      title: string
      description: string
      author: string
      created_at: string          # UTC ISO-8601
      sources: list               # empty after init
      structured: list            # empty after init
      computable: list            # empty after init
      events:
        - timestamp: string
          type: string
          description: string
  events:                         # root append-only log
    - timestamp: string
      type: string
      description: string

event_types:
  root_events:
    - model_created
  model_events:
    - created                     # init
    - source_added                # reserved (002)
    - extract_planned             # reserved
    - inventory_derived           # reserved
    - annotate_planned            # reserved
    - element_bound               # reserved
    - model_specified             # reserved
    - model_formalized            # reserved
    - validated                   # reserved

forbidden_keys:
  - topics
```

Writers: `rh_mod_skills.common.locked_update_tracking` (or equivalent). Callers MUST NOT `Path.write_text` on `tracking.yaml`.
