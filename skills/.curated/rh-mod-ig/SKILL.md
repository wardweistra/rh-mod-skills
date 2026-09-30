---
name: "rh-mod-ig"
description: >
  Stage a FHIR IG Publisher tree from a formalized snapshot. CLI writes
  models/<model>/ig/; this skill does not write files or run Java.
  Modes: sync.
compatibility: "rh-mod-skills >= 0.1.0"
context_files:
  - reference.md
  - examples/encr.md
metadata:
  author: "RH Mod Skills"
  version: "1.0.0"
  source: "skills/.curated/rh-mod-ig/SKILL.md"
  lifecycle_stage: "l3-computable"
  reads_from:
    - tracking.yaml
    - models/<model>/computable/snapshot.yaml
  writes_via_cli:
    - "rh-mod-skills ig sync"
    - "rh-mod-skills status"
---

# rh-mod-ig

`computable/` is still the L3 pin for rh-map-skills. This skill stages a **generated
IG tree** so a reviewer can run the [HL7 IG Publisher scripts](https://github.com/HL7/ig-publisher-scripts).

**Never inspect `rh-mod-skills` source code.** Use this skill, [reference.md](reference.md),
and `rh-mod-skills ig --help`. Do not hand-copy JSON into `ig/input/`. Do not
download `publisher.jar` yourself except by running the HL7 `_updatePublisher`
script from `ig/`.

Do not write mapping.xlsx, FML, StructureMap, or FSH.

## User Input

```text
$ARGUMENTS
```

First word is the mode. Typical: `sync encr`.

## Sync

1. Run `rh-mod-skills status <model>`. A snapshot must exist (stage formalized).
   If next is still `formalize`, stop and run `rh-mod-formalize` first.
2. Run `rh-mod-skills ig sync <model>`.
3. Open `models/<model>/ig/rh-mod.yaml`. If `package_id` or `url` is a guess,
   edit them; they will not be overwritten on later syncs.
4. Do not hand-edit `ImplementationGuide-*.json`. The CLI emits Home
   `definition.page`, `input/includes/menu.xml`, and `input/pagecontent/index.md`
   (the last two only if missing). See [reference.md](reference.md) for the
   publisher contract and error table.
5. Then, **on the reviewer machine** (Java required; not this CLI):

```bash
cd models/<model>/ig
./_updatePublisher.sh -y
./_genonce.sh
# ./_build.sh is equivalent
```

`status` next stays `verify`. `validator=not-run` on `rh-mod-skills verify`
does not change unless they run the publisher themselves.
