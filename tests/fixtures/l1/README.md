# L1 trial corpus

Proving sources for rh-mod-skills ingest. Originals are untrusted dictionary content.

| Model id | Files | Format | Origin |
|----------|-------|--------|--------|
| `nkr-breast` | `nkr-breast/IKNL_Data_dictionary.xlsx` | Excel (1 sheet `Variabelen`, 153 variables) | [NKR-datacatalogus](https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus) — Breast Cancer export |
| `encr-standard-dataset` | `encr-standard-dataset/*.pdf` (22 English PDFs) | PDF | [ENCR Recommendations](https://www.encr.eu/ENCR-Recommendations) |

The ENCR set is indexed by the 2023 standard dataset. Companion recommendations cited from that PDF (incidence date, basis of diagnosis, treatment, recurrence, multiple primaries, CNS, haematological, condensed TNM) plus the other English PDFs on the same page are listed in [`encr-standard-dataset/README.md`](encr-standard-dataset/README.md).

Structured L1 projection applies to Excel, CSV, and PDF tables ([004](../../../specs/004-rh-mod-ingest-pdf/)). ENCR proving file is `ENCR-Recommendation-standard-dataset_Mar2023.pdf` (Table 1 + Table 2). Companion PDFs may still skip when no reconstructable tables exist. Markdown is never the only L1 form.
