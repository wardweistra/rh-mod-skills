# Research: rh-mod-annotate

**Date**: 2026-09-14

## 1. ReasonHub MCP in the skill, CLI only records

**Decision**: Same split as rh-skills extract. The agent calls ReasonHub MCP (`search_snomed`, etc.). `annotate plan` writes a skeleton with empty `candidates`. `annotate enrich --candidate 'system|code|display'` records already-collected hits (cap 5). The CLI does not HTTP-search. Unit tests pass `--candidate` strings; they never hit the network.

**Rationale**: Constitution I — durable plan/bindings writes are CLI-owned; lookup is orchestration. rh-skills: “CLI commands do not perform live MCP lookup on your behalf.” Guessed `GET /search` had no sibling HTTP path to copy.

**Alternatives considered**: CLI httpx client (implemented then withdrawn — no published search route; duplicated MCP). Skill writes YAML itself (forbidden).

## 2. Unavailable vs zero hits

**Decision**: MCP down → skill stops; plan skeleton may already exist. Enrich with no `--candidate` records `candidates: []`. `accept` with empty candidates fails. `unbound` / reviewer `replace` do not need enrich.

**Rationale**: Distinguishes “lookup not done” from “nothing matched.” Do not invent codes from `*dat` labels.

**Alternatives considered**: Plan fails without `RH_REASONHUB_URL` (wrong after MCP split).

## 3. `--element` resolution

**Decision**: `--element` matches inventory `path` exactly, or `id` if that id is unique. Duplicate ids without a path → fail closed. `--element` + `--all-undecided` → fail. Neither → fail.

**Rationale**: Homonyms (FR-003). Unique `gesl` is the P1 proving flag.

## 4. `accept` payload

**Decision**: `decision: accept` binds `chosen` if set, else `candidates[0]`. Accept with empty candidates → implement fails. `replace` requires reviewer `chosen` system/code/display. `unbound` requires `reason`. `reject`/`pending` → no bindings row.

**Rationale**: Spec accept/replace/unbound/reject. Avoid a separate selected-index field.

## 5. Events and status next

**Decision**: Plan appends one `annotate_planned`. Implement appends one batched `element_bound` naming paths and decisions (bound and unbound). `status` next is derived from inventory vs bindings: any undecided path → `annotate`; all decided → `specify`. Stage is `annotating` after `annotate_planned` or `element_bound`.

**Rationale**: Spec FR-009 allows a batched event.

**Alternatives considered**: Per-element tracking events (noisy). New event type `element_unbound` (not in 001 schema).

## 6. `--all-undecided` cost

**Decision**: Allowed. If more than 25 elements would be included, log an advisory warning (skill will MCP-search each). No hard cap (spec permits 153).

**Rationale**: Warn rather than invent a quota.

## 7. Binding identity

**Decision**: Bindings list keyed by inventory `path`. Merge replaces the row with that path.

**Rationale**: Spec homonyms bind independently; id alone is not unique.
