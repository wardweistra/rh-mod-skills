"""Detect and project PDF tables into the Excel/CSV L1 shape.

Injection boundary: copy cell strings only. Do not interpret labels as codes.
OCR is out of scope; image-only pages skip with no-text-layer.
"""

from __future__ import annotations

import re
from pathlib import Path

CAPTION_RE = re.compile(r"^Table\s+(\d+)\s*$", re.IGNORECASE)
SKIP_NO_TEXT = "no-text-layer"
SKIP_NO_TABLES = "no-tables-detected"
SKIP_NONE_APPROVED = "no-tables-approved"
SKIP_ERROR = "extractor-error"


def _cell(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", "\n")
    text = " ".join(text.split())
    return text.strip()


def _row(values) -> list[str]:
    return [_cell(c) for c in (values or [])]


def _nonempty_rows(table: list) -> list[list[str]]:
    rows = []
    for raw in table or []:
        row = _row(raw)
        if any(row):
            rows.append(row)
    return rows


def _page_caption(page) -> str | None:
    text = page.extract_text() or ""
    for line in text.splitlines():
        match = CAPTION_RE.match(line.strip())
        if match:
            return f"Table {match.group(1)}"
    return None


def _has_text_layer(pdf) -> bool:
    return any(page.chars for page in pdf.pages)


def detect_pdf_tables(path: Path) -> dict:
    """Return plan fields for a PDF: projection, skip_reason, tables.

    Never raises for unreadable PDFs; those become extractor-error.
    """
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        return {
            "projection": "skipped",
            "skip_reason": SKIP_ERROR,
            "tables": [],
            "warnings": [str(exc)],
        }

    try:
        with pdfplumber.open(path) as pdf:
            if not _has_text_layer(pdf):
                return {
                    "projection": "skipped",
                    "skip_reason": SKIP_NO_TEXT,
                    "tables": [],
                }
            groups = _merge_page_tables(pdf)
    except Exception as exc:  # noqa: BLE001 — untrusted files
        return {
            "projection": "skipped",
            "skip_reason": SKIP_ERROR,
            "tables": [],
            "warnings": [str(exc)],
        }

    tables = []
    used_names: dict[str, int] = {}
    for index, group in enumerate(groups, start=1):
        columns = group["columns"]
        rows = group["rows"]
        name = group.get("name") or f"page-{group['pages'][0]}-table-{index}"
        used_names[name] = used_names.get(name, 0) + 1
        if used_names[name] > 1:
            name = f"{name} (p.{group['pages'][0]})"
        decision, reason = _default_decision(columns, rows)
        tables.append(
            {
                "id": f"t{index}",
                "name": name,
                "pages": group["pages"],
                "columns": columns,
                "row_count": len(rows),
                "warnings": group.get("warnings") or [],
                "decision": decision,
                "reason": reason,
            }
        )

    included = any(t["decision"] == "include" for t in tables)
    if not tables:
        return {
            "projection": "skipped",
            "skip_reason": SKIP_NO_TABLES,
            "tables": [],
        }
    return {
        "projection": "tables" if included else "skipped",
        "skip_reason": None if included else SKIP_NONE_APPROVED,
        "tables": tables,
    }


def _default_decision(columns: list[str], rows: list[list[str]]) -> tuple[str, str]:
    if len(columns) >= 2 and len(rows) >= 2:
        return "include", ""
    return "exclude", "too-small"


def _merge_page_tables(pdf) -> list[dict]:
    raw: list[dict] = []
    for page_no, page in enumerate(pdf.pages, start=1):
        caption = _page_caption(page)
        for table in page.extract_tables() or []:
            rows = _nonempty_rows(table)
            if not rows:
                continue
            raw.append(
                {
                    "page": page_no,
                    "caption": caption,
                    "rows": rows,
                }
            )

    groups: list[dict] = []
    for item in raw:
        rows = item["rows"]
        header = rows[0]
        page = item["page"]
        if groups and len(header) == len(groups[-1]["columns"]):
            prev = groups[-1]
            if header == prev["columns"]:
                prev["pages"].append(page)
                prev["rows"].extend(rows[1:])
                prev["warnings"].append("continued-header")
                continue
            if page == prev["pages"][-1] + 1:
                prev["pages"].append(page)
                prev["rows"].extend(rows)
                prev["warnings"].append("continued-without-header")
                continue
        groups.append(
            {
                "name": item["caption"],
                "pages": [page],
                "columns": header,
                "rows": rows[1:],
                "warnings": [],
            }
        )
    return groups


def table_key(table: dict) -> tuple:
    return (tuple(table.get("pages") or []), tuple(table.get("columns") or []))


def project_pdf_tables(path: Path, included: list[dict]) -> list[dict]:
    """Re-detect and return sheets for included plan tables only."""
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            groups = _merge_page_tables(pdf)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"PDF table projection failed: {exc}") from exc

    by_key = {}
    for group in groups:
        by_key[(tuple(group["pages"]), tuple(group["columns"]))] = group

    sheets = []
    for spec in included:
        key = table_key(spec)
        group = by_key.get(key)
        if group is None:
            # Fall back to id order match against current detection
            continue
        sheets.append(
            {
                "name": spec.get("name") or group.get("name") or "table",
                "columns": group["columns"],
                "rows": [
                    (row + [""] * len(group["columns"]))[: len(group["columns"])]
                    for row in group["rows"]
                ],
            }
        )
    return sheets
