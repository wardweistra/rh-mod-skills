# Example: optional ValueSet binding with strength

After mappings exist (or instead of them), a reviewer may author a ValueSet on
the annotate plan YAML:

```yaml
# in process/plans/annotate-plan.yaml element:
decision: accept
mappings:
  - system: http://loinc.org
    code: "76689-9"
    display: Sex assigned at birth
    decision: accept
value_set:
  strength: preferred
  concepts:
    - system: http://loinc.org
      code: "LA15170-6"
      display: Male
    - system: http://loinc.org
      code: "LA15171-4"
      display: Female
```

```bash
rh-mod-skills annotate approve recommendations
rh-mod-skills annotate implement recommendations
rh-mod-skills annotate verify recommendations
# expect mapped=… vs_bound=1 …
```

Formalize emits one ValueSet + `ElementDefinition.binding` for that path.
Mappings-only paths still produce **zero** ValueSets.
