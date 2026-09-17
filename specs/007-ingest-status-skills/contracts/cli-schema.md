# Contracts: ingest and status skills (007)

No new CLI. Skills MUST call these existing commands only.

## Ingest skill → CLI

```
rh-mod-skills ingest plan <model> --source FILE [--source FILE ...] [--origin-url URL]
rh-mod-skills ingest approve <model>
rh-mod-skills ingest implement <model> [--acknowledge-drift]
rh-mod-skills ingest verify <model>
rh-mod-skills status <model>
```

Durable writes: ingest CLI only. Skill MUST NOT write `ingest-plan.yaml`, `sources/`, or `tracking.yaml` as a bypass. Reviewer may edit `tables[].decision` on the plan, then the skill re-runs CLI.

## Status skill → CLI

```
rh-mod-skills status
rh-mod-skills status <model>
```

Writes: none. MUST NOT invent `Next`. Optional one-sentence skill mapping after the CLI block.

## Skill pack layout (constitution)

```
skills/.curated/rh-mod-ingest/SKILL.md
skills/.curated/rh-mod-ingest/reference.md
skills/.curated/rh-mod-ingest/examples/excel-plan.md
skills/.curated/rh-mod-ingest/examples/pdf-tables.md

skills/.curated/rh-mod-status/SKILL.md
skills/.curated/rh-mod-status/reference.md
skills/.curated/rh-mod-status/examples/output.md
```

Frontmatter MUST include `name` matching the directory, `description`, `compatibility`, `context_files`, `metadata.writes_via_cli` (empty list for status), `reads_from`.

**Forbidden in both skills**: inspect `src/rh_mod_skills/`, flatten to Markdown, OCR, guess FHIR types, call extract/annotate except as “next skill” from status.
