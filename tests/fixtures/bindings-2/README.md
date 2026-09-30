# bindings-2 fixtures (014 US1)

Synthetic mini consumers for bindings schema 2.0.

- `sample-mapped-bindings.yaml` — one path with two system mappings and `value_set: null`
  (formalize must emit `ElementDefinition.mapping` only; no ValueSet for that path).

Legacy 1.0 singleton `system`/`code`/`strength` rows are intentionally absent here;
tests that need fail-closed 1.0 shape write inline YAML.
