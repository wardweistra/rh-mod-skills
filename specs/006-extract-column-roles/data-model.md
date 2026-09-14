# Data model: extract column roles (006)

Extends [003 data-model](../003-rh-mod-extract/data-model.md). Inventory and value-domains files are unchanged.

## Extract plan (`sheets` added)

**Path**: `models/<id>/process/plans/extract-plan.yaml`

```yaml
model: nkr-breast
status: draft
allow_empty: false
sheets:
  - source: iknl-data-dictionary
    name: Variabelen
    kind: elements          # elements | value-domain
    columns:
      - header: variabele_name
        role: id            # id | category | label | datatype | cardinality |
                            # unused | domain_var | domain_code | domain_display
        origin: hint        # hint | reviewer
      - header: variabele_categorie
        role: category
        origin: hint
      - header: variabele_label
        role: label
        origin: hint
entities: []   # as 003, derived from roles
elements: []   # as 003, derived from roles
conflicts: []  # includes type: duplicate-role
value_domains: []
```

### Column roles

| Role | Meaning | Exclusive |
|------|---------|-----------|
| `id` | Element identifier cell | yes |
| `category` | Entity grouping cell | yes |
| `label` | Display cell | yes |
| `datatype` | Source-stated type | yes |
| `cardinality` | Source-stated cardinality | yes |
| `unused` | Copied into `notes` if non-empty | no |
| `domain_var` | Code-list variable id | yes |
| `domain_code` | Code-list code | yes |
| `domain_display` | Code-list display | yes |

`kind: value-domain` when `domain_var`, `domain_code`, and `domain_display` are all assigned.

`origin: hint` on first proposal. Saved roles keep `origin` from the file; missing origin is treated as `reviewer` so re-plan will not overwrite them with hints.

## Conflicts

```yaml
- type: duplicate-role
  source: odd-sheet
  sheet: odd
  role: id
  headers: [foo, baz]
```
