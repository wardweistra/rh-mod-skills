# Research: annotate review

**Date**: 2026-09-28

## 1. HTML is a view; picks YAML is the interchange

**Decision**: Export writes static HTML embedding the plan’s elements and candidates. The page downloads `annotate-picks.yaml`. Import reads only that YAML. HTML is never parsed on import.

**Rationale**: Parsing HTML is brittle. A tiny picks file is the decide API.

**Alternatives considered**: Round-trip Excel (deferred). Import HTML (rejected). Local Flask server (rejected — not needed, not a durable artifact).

## 2. Accept copies candidate into `chosen` by rank

**Decision**: `pick: N` sets `decision: accept` and copies `candidates` entry with `rank == N` (fallback: 1-based index if rank missing) into `chosen`. Do not reorder candidates. Implement already prefers `chosen` over `candidates[0]`.

**Rationale**: Rank is stable even if the reviewer never edits YAML.

**Alternatives considered**: Reorder list so pick becomes `[0]` (rejected — loses MCP ranking). Store only pick on the plan (rejected — implement would need new semantics).

## 3. Import always leaves the plan draft

**Decision**: Successful import sets `status: draft`. An approved plan is un-approved so implement cannot use stale approval.

**Rationale**: Constitution II. Choices changed after approve must be re-reviewed.

**Alternatives considered**: Import+implement in one command (rejected). Keep approved (rejected — silent bind).

## 4. No new tracking event

**Decision**: Export and import do not append tracking events. `element_bound` remains implement-only.

**Rationale**: Avoid implying bindings were written. Plan file mtime + YAML diff is enough for this slice.

**Alternatives considered**: `annotate_exported` / `annotate_imported` (nice for audit; defer).

## 5. Escape untrusted dictionary text in HTML

**Decision**: All plan strings (display, labels, codes, notes) are HTML-escaped when written into the page. Candidates are untrusted codebook/MCP text.

**Rationale**: Constitution IV injection boundary.
