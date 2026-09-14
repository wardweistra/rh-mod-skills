# 005-rh-mod-annotate

Terminology bindings on extracted inventory. Depends on 003 extract. Specify/formalize are later.

| Artifact | Path |
|----------|------|
| Spec | [spec.md](spec.md) |
| Plan | [plan.md](plan.md) |
| Research | [research.md](research.md) |
| Data model | [data-model.md](data-model.md) |
| CLI contract | [contracts/cli-schema.md](contracts/cli-schema.md) |
| Quickstart | [quickstart.md](quickstart.md) |
| Tasks | [tasks.md](tasks.md) |
| Quality checklist | [checklists/requirements.md](checklists/requirements.md) |

**Proving model**: `nkr-breast` `--element gesl` (not all 153). P2: one ENCR Table 1 element.  
**Negative case**: no ReasonHub → no invented codes; unapproved implement writes nothing.

Implemented: `rh-mod-skills annotate plan|enrich|approve|implement|verify`. Skill `rh-mod-annotate` runs ReasonHub MCP and records hits with enrich. Status next stays `annotate` until every inventory path is bound or unbound.
