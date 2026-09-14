# Developer Guide

Sibling product of `rh-skills`. Same operating system (CLI / skills / speckit), different artifact catalog.

## Dev setup

```bash
cd /Users/ward/workspace/rh-mod-skills
uv sync
uv run rh-mod-skills --help
make test
```

## Layout

```text
.specify/memory/constitution.md   ← product principles
specs/001-rh-mod-framework/       ← product spec (draft)
src/rh_mod_skills/                ← CLI (stub)
skills/.curated/                  ← empty until skills are specified
skills/_template/                 ← copy this to author a skill
schemas/                          ← empty until 001 is planned
example-project/models/           ← consumer-shaped fixture later
```

## Adding a feature

Use Speckit in this repo (not in rh-skills):

1. `speckit-specify` — new feature spec under `specs/`
2. `speckit-plan` / `speckit-tasks`
3. Implement CLI in `src/rh_mod_skills/commands/`
4. Only then copy `skills/_template` → `skills/.curated/<name>/`

## Do not

- Import or vendor `rh-skills` clinical L2 types (decision-table, measure, …)
- Flatten Excel/CSV/PDF codebooks to Markdown as the only L1 form
- Add StructureMap / FML / mapping.xlsx
