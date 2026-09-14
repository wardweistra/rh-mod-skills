"""rh-mod-skills extract — derive L2 inventory from table projections."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import click
from ruamel.yaml import YAML

from rh_mod_skills.common import (
    append_model_event,
    append_root_event,
    consumer_root,
    locked_update_tracking,
    log_info,
    model_dir,
    require_model,
    require_tracking,
    sha256_file,
    tracking_file,
)

PLAN_NAME = "extract-plan.yaml"
INVENTORY_NAME = "inventory.yaml"
VALUE_DOMAINS_NAME = "value-domains.yaml"

ID_HEADERS = ("variabele_name", "name", "id", "code")
CAT_HEADERS = ("variabele_categorie", "category", "group", "entity")
LABEL_HEADERS = ("variabele_label", "label", "description", "title")
DATATYPE_HEADERS = ("datatype", "data_type")
CARDINALITY_HEADERS = ("cardinality", "card", "multiplicity")
DOMAIN_VAR_HEADERS = ("variable", "variabele", "element")
DOMAIN_CODE_HEADERS = ("code", "waarde")
DOMAIN_DISPLAY_HEADERS = ("display", "omschrijving")


def _yaml() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    return y


def extract_plan_path(name: str) -> Path:
    return model_dir(name) / "process" / "plans" / PLAN_NAME


def inventory_path(name: str) -> Path:
    return model_dir(name) / "structured" / INVENTORY_NAME


def value_domains_path(name: str) -> Path:
    return model_dir(name) / "structured" / VALUE_DOMAINS_NAME


def load_plan(model: str) -> dict:
    path = extract_plan_path(model)
    if not path.exists():
        raise click.ClickException(
            f"No extract plan at {path}. Run `rh-mod-skills extract plan {model}` first."
        )
    with open(path, encoding="utf-8") as f:
        return _yaml().load(f) or {}


def save_plan(model: str, data: dict) -> None:
    path = extract_plan_path(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        _yaml().dump(data, f)


def slug_id(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    ascii_ = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")
    return s or "entity"


def _pick_header(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lower = {c.lower(): c for c in columns if c}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def _col_index(columns: list[str], header: str | None) -> int | None:
    if header is None:
        return None
    try:
        return columns.index(header)
    except ValueError:
        return None


def _cell(row: list, index: int | None) -> str:
    if index is None or index < 0 or index >= len(row):
        return ""
    value = row[index]
    if value is None:
        return ""
    return str(value).strip()


def _consumer_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(consumer_root()))
    except ValueError:
        return str(path)


def _resolve_tracked_path(file_field: str | None) -> Path | None:
    if not file_field:
        return None
    path = Path(file_field)
    if path.is_absolute():
        return path
    return consumer_root() / file_field


def _assert_ingest_clean(tracking: dict, model_name: str) -> None:
    m = require_model(tracking, model_name)
    sources = m.get("sources") or []
    if not sources:
        raise click.ClickException(
            f"Model '{model_name}' has no ingested sources. "
            f"Run `rh-mod-skills ingest` first."
        )
    problems = []
    for src in sources:
        path = _resolve_tracked_path(src.get("file"))
        if path is None or not path.is_file():
            problems.append(f"{src.get('name')}: original missing")
            continue
        expected = src.get("checksum")
        if expected and sha256_file(path) != expected:
            problems.append(f"{src.get('name')}: checksum drift — run ingest verify")
    if problems:
        raise click.ClickException(
            "Extract blocked until ingest is clean:\n  " + "\n  ".join(problems)
        )


def load_table_projections(tracking: dict, model_name: str) -> list[dict]:
    """Load YAML table projections recorded in tracking. Injection boundary: copy cells only."""
    m = require_model(tracking, model_name)
    projections = []
    for src in m.get("sources") or []:
        if src.get("projection") != "tables":
            continue
        ppath = _resolve_tracked_path(src.get("projection_file"))
        if ppath is None or not ppath.is_file():
            raise click.ClickException(
                f"Source '{src.get('name')}' is marked tables but projection file is missing. "
                "Re-run ingest implement."
            )
        with open(ppath, encoding="utf-8") as f:
            data = _yaml().load(f) or {}
        data["_source_name"] = src.get("name")
        projections.append(data)
    return projections


def _row_notes(columns: list[str], row: list, used: set[str]) -> dict:
    notes = {}
    for i, col in enumerate(columns):
        if not col or col in used:
            continue
        val = _cell(row, i)
        if val:
            notes[col] = val
    return notes


def _path_for(entity_id: str, element_id: str, row: int, seen: Counter) -> str:
    key = f"{entity_id}.{element_id}"
    if seen[key] <= 1:
        return key
    return f"{entity_id}.{element_id}__r{row}"


def propose_from_projections(projections: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Return entities, elements, conflicts, domain proposals. Copies cell strings only."""
    entity_order: list[str] = []
    entity_titles: dict[str, str] = {}
    elements: list[dict] = []
    conflicts: list[dict] = []
    id_seen_in_sheet: dict[tuple[str, str, str], int] = {}
    path_seen: Counter = Counter()

    domain_sheets: list[tuple[str, dict]] = []

    for proj in projections:
        source_name = proj.get("_source_name") or slug_id(str(proj.get("source") or "source"))
        for sheet in proj.get("sheets") or []:
            columns = [str(c) if c is not None else "" for c in (sheet.get("columns") or [])]
            sheet_name = sheet.get("name") or "sheet"
            id_h = _pick_header(columns, ID_HEADERS)
            cat_h = _pick_header(columns, CAT_HEADERS)
            label_h = _pick_header(columns, LABEL_HEADERS)
            type_h = _pick_header(columns, DATATYPE_HEADERS)
            card_h = _pick_header(columns, CARDINALITY_HEADERS)
            domain_var = _pick_header(columns, DOMAIN_VAR_HEADERS)
            domain_code = _pick_header(columns, DOMAIN_CODE_HEADERS)
            domain_disp = _pick_header(columns, DOMAIN_DISPLAY_HEADERS)
            is_domain_sheet = bool(domain_var and domain_code and domain_disp)
            if is_domain_sheet:
                domain_sheets.append((source_name, sheet))
                continue

            id_i = _col_index(columns, id_h)
            cat_i = _col_index(columns, cat_h)
            label_i = _col_index(columns, label_h)
            type_i = _col_index(columns, type_h)
            card_i = _col_index(columns, card_h)
            used = {h for h in (id_h, cat_h, label_h, type_h, card_h) if h}

            for idx, raw in enumerate(sheet.get("rows") or [], start=1):
                row = list(raw) if raw is not None else []
                if not any(_cell(row, i) for i in range(len(row))):
                    continue
                category = _cell(row, cat_i) if cat_h else sheet_name
                if not category:
                    category = sheet_name
                entity_id = slug_id(category)
                if entity_id not in entity_titles:
                    entity_titles[entity_id] = category
                    entity_order.append(entity_id)
                raw_id = _cell(row, id_i) if id_h else ""
                element_id = slug_id(raw_id) if raw_id else f"row-{idx}"
                display = _cell(row, label_i) if label_h else (raw_id or element_id)
                datatype = _cell(row, type_i) if type_h else ""
                cardinality = _cell(row, card_i) if card_h else ""
                sheet_key = (source_name, sheet_name, element_id)
                id_seen_in_sheet[sheet_key] = id_seen_in_sheet.get(sheet_key, 0) + 1
                if id_seen_in_sheet[sheet_key] > 1:
                    conflicts.append(
                        {
                            "type": "duplicate-name",
                            "source": source_name,
                            "sheet": sheet_name,
                            "id": element_id,
                            "row": idx,
                        }
                    )
                path_key = f"{entity_id}.{element_id}"
                path_seen[path_key] += 1
                path = _path_for(entity_id, element_id, idx, path_seen)
                notes = _row_notes(columns, row, used)
                elements.append(
                    {
                        "id": element_id,
                        "display": display,
                        "entity": entity_id,
                        "path": path,
                        "datatype": datatype or "unknown",
                        "cardinality": cardinality or "unknown",
                        "value_domain": None,
                        "decision": "include",
                        "reason": "",
                        "notes": notes,
                        "provenance": {
                            "source": source_name,
                            "sheet": sheet_name,
                            "row": idx,
                            "columns": {
                                "id": id_h,
                                "category": cat_h,
                                "label": label_h,
                            },
                        },
                    }
                )

    domains = _domains_from_sheets(domain_sheets)
    domain_ids = {d["id"] for d in domains}
    for el in elements:
        if el["id"] in domain_ids:
            el["value_domain"] = el["id"]

    entities = [
        {
            "id": eid,
            "title": entity_titles[eid],
            "decision": "include",
            "merge_into": None,
            "reason": "",
        }
        for eid in entity_order
    ]
    return entities, elements, conflicts, domains


def _domains_from_sheets(domain_sheets: list[tuple[str, dict]]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for _source, sheet in domain_sheets:
        columns = [str(c) if c is not None else "" for c in (sheet.get("columns") or [])]
        var_h = _pick_header(columns, DOMAIN_VAR_HEADERS)
        code_h = _pick_header(columns, DOMAIN_CODE_HEADERS)
        disp_h = _pick_header(columns, DOMAIN_DISPLAY_HEADERS)
        var_i = _col_index(columns, var_h)
        code_i = _col_index(columns, code_h)
        disp_i = _col_index(columns, disp_h)
        for raw in sheet.get("rows") or []:
            row = list(raw) if raw is not None else []
            var = slug_id(_cell(row, var_i))
            code = _cell(row, code_i)
            if not var or not code:
                continue
            grouped[var].append({"code": code, "display": _cell(row, disp_i) or code})
    return [{"id": vid, "codes": codes} for vid, codes in grouped.items()]


def inventory_from_plan(plan: dict) -> dict:
    entities_meta = {e["id"]: e for e in plan.get("entities") or []}
    included_entities: dict[str, dict] = {}
    order: list[str] = []

    def resolve_entity(eid: str) -> str | None:
        meta = entities_meta.get(eid)
        if not meta:
            return eid
        decision = meta.get("decision") or "include"
        if decision == "drop":
            return None
        if decision == "merge-into":
            target = meta.get("merge_into")
            if not target:
                raise click.ClickException(f"Entity '{eid}' is merge-into but merge_into is empty")
            return resolve_entity(target)
        return eid

    titles = {}
    for meta in plan.get("entities") or []:
        resolved = resolve_entity(meta["id"])
        if resolved is None:
            continue
        if meta.get("decision") == "include":
            titles[meta["id"]] = meta.get("title") or meta["id"]
        titles.setdefault(resolved, meta.get("title") or resolved)

    included_elements = []
    for el in plan.get("elements") or []:
        if (el.get("decision") or "include") == "drop":
            continue
        entity_id = resolve_entity(el.get("entity"))
        if entity_id is None:
            continue
        if entity_id not in included_entities:
            included_entities[entity_id] = {
                "id": entity_id,
                "title": titles.get(entity_id, entity_id),
                "elements": [],
            }
            order.append(entity_id)
        item = {
            "id": el["id"],
            "display": el.get("display") or el["id"],
            "path": el.get("path") or f"{entity_id}.{el['id']}",
            "datatype": el.get("datatype") or "unknown",
            "cardinality": el.get("cardinality") or "unknown",
            "provenance": el.get("provenance") or {},
        }
        if el.get("value_domain"):
            item["value_domain"] = el["value_domain"]
        if el.get("notes"):
            item["notes"] = el["notes"]
        included_entities[entity_id]["elements"].append(item)
        included_elements.append(item)

    if not included_elements and not plan.get("allow_empty"):
        raise click.ClickException(
            "Approved plan includes no elements. Set allow_empty: true if that is intentional."
        )

    return {
        "model": plan.get("model"),
        "entities": [included_entities[eid] for eid in order],
    }


def _record_extract_planned(tracking: dict, model_name: str, n_ent: int, n_el: int) -> None:
    append_model_event(
        tracking,
        model_name,
        "extract_planned",
        f"Extract plan drafted: {n_ent} entities, {n_el} elements",
    )
    append_root_event(tracking, "extract_planned", f"{model_name}: extract plan drafted")


def _record_inventory_derived(tracking: dict, model_name: str, n_ent: int, n_el: int, files: list[str]) -> None:
    m = require_model(tracking, model_name)
    structured = m.setdefault("structured", [])
    for name in files:
        if name not in structured:
            structured.append(name)
    append_model_event(
        tracking,
        model_name,
        "inventory_derived",
        f"Inventory written: {n_ent} entities, {n_el} elements",
    )
    append_root_event(tracking, "inventory_derived", f"{model_name}: inventory derived")


@click.group()
def extract():
    """Derive L2 inventory from ingested table projections."""


@extract.command("plan")
@click.argument("model")
def plan_cmd(model):
    """Write a draft extract plan from table projections. Does not write inventory."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    projections = load_table_projections(tracking, model)
    if not projections:
        raise click.ClickException(
            f"Model '{model}' has no table projection. Extract cannot invent rows from PDF text. "
            "Ingest an Excel/CSV codebook, or project PDF tables (004-rh-mod-ingest-pdf)."
        )

    entities, elements, conflicts, domains = propose_from_projections(projections)
    data = {
        "model": model,
        "status": "draft",
        "allow_empty": False,
        "entities": entities,
        "elements": elements,
        "conflicts": conflicts,
        "value_domains": domains,
    }
    save_plan(model, data)
    locked_update_tracking(
        lambda t, n_ent=len(entities), n_el=len(elements): _record_extract_planned(
            t, model, n_ent, n_el
        )
    )
    log_info(
        f"Wrote extract plan ({len(entities)} entities, {len(elements)} elements, "
        f"{len(conflicts)} conflict(s), status=draft)"
    )
    click.echo(f"  {extract_plan_path(model)}")
    for ent in entities:
        n = sum(1 for el in elements if el["entity"] == ent["id"])
        click.echo(f"  - {ent['title']}  id={ent['id']}  elements={n}")


@extract.command("approve")
@click.argument("model")
def approve_cmd(model):
    """Mark the extract plan approved (human gate)."""
    tracking = require_tracking()
    require_model(tracking, model)
    data = load_plan(model)
    data["status"] = "approved"
    save_plan(model, data)
    log_info(f"Approved extract plan for {model}")


@extract.command("implement")
@click.argument("model")
@click.option(
    "--replace",
    is_flag=True,
    help="Overwrite an existing inventory.yaml",
)
def implement_cmd(model, replace):
    """Write inventory.yaml from the approved plan."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    plan = load_plan(model)
    if plan.get("status") != "approved":
        raise click.ClickException(
            f"Extract plan is not approved (status={plan.get('status')!r}). "
            f"Run `rh-mod-skills extract approve {model}` after review."
        )

    inv_path = inventory_path(model)
    if inv_path.is_file() and not replace:
        raise click.ClickException(
            f"Inventory already exists at {inv_path}. Re-run with --replace to overwrite."
        )

    inventory = inventory_from_plan(plan)
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(inv_path, "w", encoding="utf-8") as f:
        _yaml().dump(inventory, f)

    written = [INVENTORY_NAME]
    domains = plan.get("value_domains") or []
    included_ids = {
        el["id"]
        for ent in inventory["entities"]
        for el in ent.get("elements") or []
        if el.get("value_domain")
    }
    kept = [d for d in domains if d.get("id") in included_ids]
    vd_path = value_domains_path(model)
    if kept:
        with open(vd_path, "w", encoding="utf-8") as f:
            _yaml().dump({"model": model, "domains": kept}, f)
        written.append(VALUE_DOMAINS_NAME)
    elif vd_path.exists() and replace:
        vd_path.unlink()

    n_ent = len(inventory["entities"])
    n_el = sum(len(e.get("elements") or []) for e in inventory["entities"])
    locked_update_tracking(
        lambda t, files=written: _record_inventory_derived(t, model, n_ent, n_el, files)
    )
    log_info(f"Wrote inventory ({n_ent} entities, {n_el} elements)")
    click.echo(f"  {inv_path}")
    if VALUE_DOMAINS_NAME in written:
        click.echo(f"  {vd_path}")


def _prov_key(prov: dict) -> tuple:
    return (prov.get("source"), prov.get("sheet"), prov.get("row"))


@extract.command("verify")
@click.argument("model")
def verify_cmd(model):
    """Non-destructive extract report. Does not write tracking events."""
    tracking = require_tracking()
    require_model(tracking, model)
    before = tracking_file().read_text(encoding="utf-8")
    blocking = 0

    plan_path = extract_plan_path(model)
    if not plan_path.is_file():
        raise click.ClickException(f"No extract plan at {plan_path}")
    plan = load_plan(model)
    approved = plan.get("status") == "approved"
    click.echo(f"plan: {'approved' if approved else plan.get('status')}")
    if not approved:
        click.echo("  blocking: plan is not approved")
        blocking += 1

    inv_path = inventory_path(model)
    if not inv_path.is_file():
        click.echo("inventory: missing")
        blocking += 1
        inventory = {"entities": []}
    else:
        with open(inv_path, encoding="utf-8") as f:
            inventory = _yaml().load(f) or {}
        n_ent = len(inventory.get("entities") or [])
        n_el = sum(len(e.get("elements") or []) for e in inventory.get("entities") or [])
        click.echo(f"inventory: present  entities={n_ent} elements={n_el}")

    inv_keys = set()
    unknown_dt = 0
    unknown_card = 0
    for ent in inventory.get("entities") or []:
        for el in ent.get("elements") or []:
            inv_keys.add(_prov_key(el.get("provenance") or {}))
            if (el.get("datatype") or "unknown") == "unknown":
                unknown_dt += 1
            if (el.get("cardinality") or "unknown") == "unknown":
                unknown_card += 1

    dropped_keys = {
        _prov_key(el.get("provenance") or {})
        for el in plan.get("elements") or []
        if (el.get("decision") or "include") == "drop"
    }
    # Also treat elements whose entity was dropped as excluded
    dropped_entities = {
        e["id"] for e in plan.get("entities") or [] if e.get("decision") == "drop"
    }
    for el in plan.get("elements") or []:
        if el.get("entity") in dropped_entities:
            dropped_keys.add(_prov_key(el.get("provenance") or {}))

    try:
        _assert_ingest_clean(tracking, model)
        projections = load_table_projections(tracking, model)
    except click.ClickException as exc:
        click.echo(f"projections: {exc}")
        blocking += 1
        projections = []

    projected = 0
    missing = 0
    excluded = 0
    covered = 0
    _, proposed, _, _ = propose_from_projections(projections) if projections else ([], [], [], [])
    for el in proposed:
        projected += 1
        key = _prov_key(el.get("provenance") or {})
        if key in inv_keys:
            covered += 1
        elif key in dropped_keys:
            excluded += 1
        else:
            missing += 1
            blocking += 1

    click.echo(
        f"coverage: projected={projected} covered={covered} excluded={excluded} missing={missing}"
    )
    click.echo(f"conflicts: {len(plan.get('conflicts') or [])}")
    click.echo(f"unknown: datatype={unknown_dt} cardinality={unknown_card} (advisory)")
    if missing:
        click.echo("  blocking: projected rows missing from inventory and not plan-excluded")

    after = tracking_file().read_text(encoding="utf-8")
    if before != after:
        raise click.ClickException("verify mutated tracking.yaml — this is a bug")
    if blocking:
        raise click.ClickException(f"extract verify failed: {blocking} blocking issue(s)")
    log_info("extract verify passed")
