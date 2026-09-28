# CLI: annotate `--system` / `--candidate` (009)

Extends [005 cli-schema](../005-rh-mod-annotate/contracts/cli-schema.md).

`--system` values: `snomed` (default if omitted), `loinc`, `icd-10`, `icd-10-cm`, `rxnorm`, `ucum`, `all`. Repeatable. HTTP URIs still allowed. Unknown names fail. Recorded on the plan; plan does not search.

`--candidate` system field: same aliases except `all` (fails), or an `http…` URI. Stored as canonical FHIR URI.

No new subcommands. Export/import/approve/implement/verify unchanged.
