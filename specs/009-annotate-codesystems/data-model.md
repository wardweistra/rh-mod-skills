# Data model: annotate code systems

Annotate plan and bindings schemas are unchanged ([005](../005-rh-mod-annotate/data-model.md)).

## Plan `systems`

List of lowercase aliases (and optional `all`), e.g.:

```yaml
systems: [rxnorm]
# or
systems: [snomed, loinc]
# or
systems: [all]
```

Default: `[snomed]`.

## Candidate `system` after enrich

Always a FHIR URI from the table in research.md (or an `http…` value passed through). Never `all`.
