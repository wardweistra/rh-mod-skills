"""rh-mod-skills specify — L2 logical model from inventory + bindings."""

from __future__ import annotations

import re
from pathlib import Path

import click
from ruamel.yaml import YAML

from rh_mod_skills.commands.annotate import (
    assert_bindings_v2,
    bindings_path,
    decided_binding_paths,
    inventory_element_paths,
    inventory_elements,
    load_bindings,
    load_inventory,
    load_yaml_file,
    validate_mapping_list,
    validate_value_set,
)
from rh_mod_skills.commands.extract import _assert_ingest_clean, inventory_path
from rh_mod_skills.common import (
    append_model_event,
    append_root_event,
    locked_update_tracking,
    log_info,
    model_dir,
    require_model,
    require_tracking,
    tracking_file,
)

PLAN_NAME = "specify-plan.yaml"
LOGICAL_MODEL_NAME = "logical-model.yaml"
CARD_RE = re.compile(r"^\d+\.\.(\d+|\*)$")
FHIR_TYPES = {
    "boolean": "boolean",
    "integer": "integer",
    "decimal": "decimal",
    "string": "string",
    "uri": "uri",
    "url": "url",
    "canonical": "canonical",
    "base64binary": "base64Binary",
    "instant": "instant",
    "date": "date",
    "datetime": "dateTime",
    "time": "time",
    "code": "code",
    "oid": "oid",
    "id": "id",
    "markdown": "markdown",
    "unsignedint": "unsignedInt",
    "positiveint": "positiveInt",
    "uuid": "uuid",
    "coding": "Coding",
    "codeableconcept": "CodeableConcept",
    "identifier": "Identifier",
    "quantity": "Quantity",
    "period": "Period",
    "range": "Range",
    "ratio": "Ratio",
    "humanname": "HumanName",
    "address": "Address",
    "contactpoint": "ContactPoint",
    "attachment": "Attachment",
    "reference": "Reference",
}


def _yaml() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    return y


def specify_plan_path(name: str) -> Path:
    return model_dir(name) / "process" / "plans" / PLAN_NAME


def logical_model_path(name: str) -> Path:
    return model_dir(name) / "structured" / LOGICAL_MODEL_NAME


def save_yaml_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        _yaml().dump(data, f)


def load_plan(model: str) -> dict:
    path = specify_plan_path(model)
    if not path.exists():
        raise click.ClickException(
            f"No specify plan at {path}. Run `rh-mod-skills specify plan {model}` first."
        )
    return load_yaml_file(path)


def save_plan(model: str, data: dict) -> None:
    save_yaml_file(specify_plan_path(model), data)


def normalize_datatype(raw) -> str:
    s = str(raw or "").strip()
    if not s or s.lower() == "unknown":
        return "unknown"
    return FHIR_TYPES.get(s.lower(), "unknown")


def normalize_cardinality(raw) -> str:
    s = str(raw or "").strip()
    if not s or s.lower() == "unknown":
        return "unknown"
    if CARD_RE.match(s):
        return s
    return "unknown"


def snapshot_from_binding(row: dict) -> dict:
    """Copy bindings 2.0 fields onto the LM element (no nested binding singleton)."""
    status = row.get("status")
    if status == "unbound":
        return {
            "status": "unbound",
            "mappings": [],
            "value_set": None,
            "reason": (row.get("reason") or "").strip(),
        }
    mappings_raw = list(row.get("mappings") or [])
    vs = validate_value_set(row.get("path"), row.get("value_set"))
    mappings = validate_mapping_list(row.get("path"), mappings_raw) if mappings_raw else []
    if not mappings and vs is None:
        raise click.ClickException(
            f"mapped binding {row.get('path')!r} needs mappings and/or value_set"
        )
    return {
        "status": "mapped",
        "mappings": mappings,
        "value_set": vs,
        "reason": row.get("reason") or "",
    }


def _issues(datatype: str, cardinality: str) -> list[str]:
    issues = []
    if datatype == "unknown":
        issues.append("unknown-datatype")
    if cardinality == "unknown":
        issues.append("unknown-cardinality")
    return issues


def _assert_annotate_complete(model: str) -> tuple[dict, dict]:
    inventory = load_inventory(model)
    inv_paths = [p for p in inventory_element_paths(model)]
    if not inv_paths:
        raise click.ClickException(
            f"Inventory at {inventory_path(model)} has no elements. "
            f"Run `rh-mod-skills extract implement {model}` first."
        )
    bpath = bindings_path(model)
    if not bpath.is_file():
        raise click.ClickException(
            f"No bindings at {bpath}. Finish annotate (every path mapped or unbound) first."
        )
    bindings = load_bindings(model, validate=True)
    assert_bindings_v2(bindings)
    decided = decided_binding_paths(model)
    missing = [p for p in inv_paths if p not in decided]
    extra = sorted(decided - set(inv_paths))
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"{len(missing)} inventory path(s) still undecided")
        if extra:
            parts.append(f"{len(extra)} binding path(s) not in inventory")
        raise click.ClickException(
            "Specify requires annotate-complete bindings: " + "; ".join(parts) + ". "
            f"Run `rh-mod-skills annotate verify {model}`."
        )
    return inventory, bindings


def build_specify_plan(model: str, inventory: dict, bindings: dict) -> dict:
    by_path = {b.get("path"): b for b in bindings.get("bindings") or [] if b.get("path")}
    entities = []
    for ent in inventory.get("entities") or []:
        planned = []
        for el in ent.get("elements") or []:
            path = el.get("path")
            row = by_path.get(path) or {}
            datatype = normalize_datatype(el.get("datatype") or el.get("type"))
            cardinality = normalize_cardinality(el.get("cardinality"))
            snap = snapshot_from_binding(row)
            planned.append(
                {
                    "id": el.get("id"),
                    "path": path,
                    "display": el.get("display"),
                    "datatype": datatype,
                    "cardinality": cardinality,
                    "issues": _issues(datatype, cardinality),
                    "status": snap["status"],
                    "mappings": snap["mappings"],
                    "value_set": snap["value_set"],
                    "reason": snap["reason"],
                    "provenance": el.get("provenance") or {},
                }
            )
        entities.append(
            {
                "id": ent.get("id"),
                "title": ent.get("title"),
                "elements": planned,
            }
        )
    return {"model": model, "status": "draft", "entities": entities}


def logical_model_from_plan(plan: dict) -> dict:
    return {
        "schema_version": "2.0",
        "model": plan.get("model"),
        "entities": list(plan.get("entities") or []),
    }


def _iter_lm_elements(data: dict) -> list[dict]:
    out = []
    for ent in data.get("entities") or []:
        out.extend(ent.get("elements") or [])
    return out


def assert_logical_model_v2(lm: dict) -> dict:
    version = str(lm.get("schema_version") or "")
    if version != "2.0":
        raise click.ClickException(
            f"logical-model schema_version must be '2.0' (got {version!r}); "
            "re-specify — nested binding singleton (1.0) is not supported."
        )
    for el in _iter_lm_elements(lm):
        binding = el.get("binding")
        if isinstance(binding, dict) and any(
            k in binding for k in ("system", "code", "strength")
        ):
            raise click.ClickException(
                f"logical-model element {el.get('path')!r} has nested binding singleton; "
                "re-specify for schema 2.0 (mappings[] on the element)."
            )
    return lm


def _record_model_specified(tracking: dict, model_name: str, n: int, files: list[str]) -> None:
    m = require_model(tracking, model_name)
    structured = m.setdefault("structured", [])
    for name in files:
        if name not in structured:
            structured.append(name)
    append_model_event(
        tracking,
        model_name,
        "model_specified",
        f"Logical model specified: {n} element(s)",
    )
    append_root_event(tracking, "model_specified", f"{model_name}: logical model specified")


@click.group()
def specify():
    """Converge inventory and bindings into a logical model."""


@specify.command("plan")
@click.argument("model")
def plan_cmd(model):
    """Write a draft specify plan from complete inventory + bindings."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    inventory, bindings = _assert_annotate_complete(model)
    data = build_specify_plan(model, inventory, bindings)
    save_plan(model, data)
    n = len(_iter_lm_elements(data))
    log_info(f"Wrote specify plan ({n} element(s), status=draft)")
    click.echo(f"  {specify_plan_path(model)}")


@specify.command("approve")
@click.argument("model")
def approve_cmd(model):
    """Mark the specify plan approved (human gate)."""
    tracking = require_tracking()
    require_model(tracking, model)
    data = load_plan(model)
    data["status"] = "approved"
    save_plan(model, data)
    log_info(f"Approved specify plan for {model}")


@specify.command("implement")
@click.argument("model")
def implement_cmd(model):
    """Write structured/logical-model.yaml from the approved plan."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    _assert_annotate_complete(model)
    plan = load_plan(model)
    if plan.get("status") != "approved":
        raise click.ClickException(
            f"Specify plan is not approved (status={plan.get('status')!r}). "
            f"Run `rh-mod-skills specify approve {model}` after review."
        )
    lm = logical_model_from_plan(plan)
    save_yaml_file(logical_model_path(model), lm)
    n = len(_iter_lm_elements(lm))
    files = [LOGICAL_MODEL_NAME]
    locked_update_tracking(lambda t, count=n, f=files: _record_model_specified(t, model, count, f))
    log_info(f"Wrote logical model ({n} element(s))")
    click.echo(f"  {logical_model_path(model)}")


def _verify_issues(inventory: dict, lm: dict) -> tuple[list[str], int, int]:
    inv_paths = {el["path"] for el in inventory_elements(inventory) if el.get("path")}
    lm_els = _iter_lm_elements(lm)
    lm_paths = {el.get("path") for el in lm_els if el.get("path")}
    blocking: list[str] = []
    unknown_dt = 0
    unknown_card = 0
    for path in sorted(inv_paths - lm_paths):
        blocking.append(f"inventory path missing from logical model: {path}")
    for path in sorted(lm_paths - inv_paths):
        blocking.append(f"logical-model path not in inventory: {path}")
    for el in lm_els:
        path = el.get("path")
        if not (el.get("provenance") or {}):
            blocking.append(f"missing provenance: {path}")
        status = el.get("status")
        if status == "mapped":
            mappings = el.get("mappings") or []
            vs_raw = el.get("value_set")
            try:
                vs = validate_value_set(path, vs_raw)
            except click.ClickException as exc:
                blocking.append(str(exc))
                vs = None
            if mappings:
                try:
                    validate_mapping_list(path, mappings)
                except click.ClickException as exc:
                    blocking.append(str(exc))
            if not mappings and vs is None:
                blocking.append(f"mapped missing mappings and value_set: {path}")
        elif status == "unbound":
            if not (el.get("reason") or "").strip():
                blocking.append(f"unbound missing reason: {path}")
            if el.get("mappings"):
                blocking.append(f"unbound with mappings: {path}")
            if isinstance(el.get("value_set"), dict) and el.get("value_set"):
                blocking.append(f"unbound with value_set: {path}")
        else:
            blocking.append(f"element status missing: {path}")
        if (el.get("datatype") or "unknown") == "unknown":
            unknown_dt += 1
        if (el.get("cardinality") or "unknown") == "unknown":
            unknown_card += 1
    return blocking, unknown_dt, unknown_card


@specify.command("verify")
@click.argument("model")
def verify_cmd(model):
    """Non-destructive specify report. Does not write tracking events."""
    tracking = require_tracking()
    require_model(tracking, model)
    before = tracking_file().read_text(encoding="utf-8")
    blocking_n = 0

    plan_path = specify_plan_path(model)
    if plan_path.is_file():
        plan = load_yaml_file(plan_path)
        click.echo(f"plan: {plan.get('status')}")
    else:
        click.echo("plan: missing")

    try:
        inventory = load_inventory(model)
    except click.ClickException as exc:
        click.echo(f"inventory: {exc}")
        blocking_n += 1
        inventory = {"entities": []}

    lpath = logical_model_path(model)
    if lpath.is_file():
        lm = load_yaml_file(lpath)
        click.echo("logical-model: present")
        try:
            assert_logical_model_v2(lm)
        except click.ClickException as exc:
            click.echo(f"  blocking: {exc}")
            blocking_n += 1
    else:
        lm = {"schema_version": "2.0", "model": model, "entities": []}
        click.echo("logical-model: missing")
        blocking_n += 1

    n = len(_iter_lm_elements(lm))
    click.echo(f"elements={n}")
    issues, unknown_dt, unknown_card = _verify_issues(inventory, lm)
    click.echo(f"unknown-datatype={unknown_dt} unknown-cardinality={unknown_card}")
    for issue in issues:
        click.echo(f"  blocking: {issue}")
        blocking_n += 1

    after = tracking_file().read_text(encoding="utf-8")
    if before != after:
        raise click.ClickException("verify mutated tracking.yaml — this is a bug")
    if blocking_n:
        raise click.ClickException(f"specify verify failed: {blocking_n} blocking issue(s)")
    log_info("specify verify passed")
