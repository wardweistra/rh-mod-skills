"""Terminology helpers for annotate enrich. No HTTP — MCP lookup is the agent's job."""

from __future__ import annotations

SYSTEM_URIS = {
    "snomed": "http://snomed.info/sct",
    "loinc": "http://loinc.org",
    "icd-10": "http://hl7.org/fhir/sid/icd-10",
}

ALLOWED_SYSTEMS = tuple(SYSTEM_URIS)


def system_uri(alias: str) -> str:
    key = (alias or "").strip().lower()
    if key in SYSTEM_URIS:
        return SYSTEM_URIS[key]
    if (alias or "").startswith("http"):
        return alias
    raise ValueError(
        f"Unknown code system {alias!r}. Use a FHIR URI or one of: {', '.join(ALLOWED_SYSTEMS)}"
    )


def parse_candidate_flag(value: str) -> dict:
    """Parse 'system|code|display[|distance[|confidence]]'. Copies strings only."""
    parts = value.split("|", 4)
    if len(parts) < 3 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(
            f"--candidate value must be 'system|code|display[|distance[|confidence]]', got: {value!r}"
        )
    raw_system = parts[0].strip()
    try:
        system = system_uri(raw_system)
    except ValueError:
        if raw_system.startswith("http"):
            system = raw_system
        else:
            raise
    entry: dict = {
        "system": system,
        "code": parts[1].strip(),
        "display": parts[2].strip(),
    }
    if len(parts) >= 4 and parts[3].strip():
        try:
            entry["distance"] = float(parts[3].strip())
        except ValueError as exc:
            raise ValueError(f"distance must be a number, got: {parts[3]!r}") from exc
    if len(parts) >= 5 and parts[4].strip():
        entry["confidence"] = parts[4].strip().lower()
    return entry
