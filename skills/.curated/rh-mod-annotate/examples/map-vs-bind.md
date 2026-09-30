# Example: multi-system mapping (no ValueSet)

Sex-at-birth may map to both LOINC and SNOMED. That is two `mappings[]` rows —
not a ValueSet.

```bash
rh-mod-skills annotate plan recommendations --element sex-at-birth --system loinc --system snomed
# MCP search both systems; enrich with up to five candidates
rh-mod-skills annotate enrich recommendations --element sex-at-birth \
  --candidate 'http://loinc.org|76689-9|Sex assigned at birth' \
  --candidate 'http://snomed.info/sct|184100006|Patient sex'
rh-mod-skills annotate export recommendations
# Reviewer accepts LOINC (pick 1), re-import; then accepts SNOMED (pick 2)
rh-mod-skills annotate import recommendations --from annotate-picks.yaml
rh-mod-skills annotate approve recommendations
rh-mod-skills annotate implement recommendations
```

Expect `bindings.yaml` with `schema_version: "2.0"`, `status: mapped`, two
mappings, `value_set: null`. Formalize later emits `ElementDefinition.mapping`
only — zero ValueSet files for that path.
