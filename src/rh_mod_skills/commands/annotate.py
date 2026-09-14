"""rh-mod-skills annotate — terminology bindings on extracted inventory."""

from __future__ import annotations

from pathlib import Path

import click
from ruamel.yaml import YAML

from rh_mod_skills.commands.extract import _assert_ingest_clean, inventory_path
from rh_mod_skills.common import (
    append_model_event,
    append_root_event,
    locked_update_tracking,
    log_info,
    log_warn,
    model_dir,
    require_model,
    require_tracking,
    tracking_file,
)
from rh_mod_skills.terminology import (
    ALLOWED_SYSTEMS,
    parse_candidate_flag,
    system_uri,
)

PLAN_NAME = "annotate-plan.yaml"
BINDINGS_NAME = "bindings.yaml"
ALL_UNDECIDED_WARN = 25
DURABLE_DECISIONS = {"accept", "replace", "unbound"}
SKIP_DECISIONS = {"pending", "reject"}


def _yaml() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    return y


def annotate_plan_path(name: str) -> Path:
    return model_dir(name) / "process" / "plans" / PLAN_NAME


def bindings_path(name: str) -> Path:
    return model_dir(name) / "structured" / BINDINGS_NAME


def load_yaml_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return _yaml().load(f) or {}


def save_yaml_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        _yaml().dump(data, f)


def load_plan(model: str) -> dict:
    path = annotate_plan_path(model)
    if not path.exists():
        raise click.ClickException(
            f"No annotate plan at {path}. Run `rh-mod-skills annotate plan {model}` first."
        )
    return load_yaml_file(path)


def save_plan(model: str, data: dict) -> None:
    save_yaml_file(annotate_plan_path(model), data)


def load_inventory(model: str) -> dict:
    path = inventory_path(model)
    if not path.is_file():
        raise click.ClickException(
            f"No inventory at {path}. Run `rh-mod-skills extract implement {model}` first."
        )
    return load_yaml_file(path)


def load_bindings(model: str) -> dict:
    path = bindings_path(model)
    if not path.is_file():
        return {"model": model, "bindings": []}
    return load_yaml_file(path)


def inventory_elements(inventory: dict) -> list[dict]:
    out: list[dict] = []
    for ent in inventory.get("entities") or []:
        for el in ent.get("elements") or []:
            out.append(el)
    return out


def inventory_element_paths(model_name: str) -> list[str]:
    path = inventory_path(model_name)
    if not path.is_file():
        return []
    return [el["path"] for el in inventory_elements(load_yaml_file(path)) if el.get("path")]


def decided_binding_paths(model_name: str) -> set[str]:
    path = bindings_path(model_name)
    if not path.is_file():
        return set()
    data = load_yaml_file(path)
    return {
        b["path"]
        for b in data.get("bindings") or []
        if b.get("path") and b.get("status") in ("bound", "unbound")
    }


def _assert_annotate_ready(tracking: dict, model: str) -> dict:
    require_model(tracking, model)
    path = inventory_path(model)
    if not path.is_file():
        raise click.ClickException(
            f"No inventory at {path}. Run `rh-mod-skills extract implement {model}` first."
        )
    _assert_ingest_clean(tracking, model)
    return load_inventory(model)


def _validate_systems(systems: tuple[str, ...]) -> list[str]:
    aliases = list(systems) or ["snomed"]
    out = []
    for alias in aliases:
        try:
            system_uri(alias)
        except ValueError as exc:
            raise click.UsageError(str(exc)) from exc
        out.append(alias.lower() if alias.lower() in ALLOWED_SYSTEMS else alias)
    return out


def resolve_elements(
    inventory: dict,
    element_flags: tuple[str, ...],
    all_undecided: bool,
    bindings: dict,
) -> list[dict]:
    all_els = inventory_elements(inventory)
    by_path = {el.get("path"): el for el in all_els if el.get("path")}
    by_id: dict[str, list[dict]] = {}
    for el in all_els:
        by_id.setdefault(el.get("id"), []).append(el)

    if all_undecided:
        decided = {
            b.get("path")
            for b in bindings.get("bindings") or []
            if b.get("status") in ("bound", "unbound")
        }
        selected = [el for el in all_els if el.get("path") not in decided]
        if not selected:
            raise click.ClickException("No undecided inventory elements remain.")
        return selected

    selected = []
    seen: set[str] = set()
    for spec in element_flags:
        if spec in by_path:
            el = by_path[spec]
        else:
            matches = by_id.get(spec) or []
            if len(matches) > 1:
                paths = ", ".join(m.get("path") or "?" for m in matches)
                raise click.ClickException(
                    f"Element id '{spec}' is not unique; use a path ({paths})."
                )
            if len(matches) == 0:
                raise click.ClickException(
                    f"Unknown element '{spec}'. It is not an inventory path or unique id."
                )
            el = matches[0]
        path = el.get("path")
        if path in seen:
            continue
        seen.add(path)
        selected.append(el)
    return selected


def _record_annotate_planned(tracking: dict, model_name: str, n: int) -> None:
    append_model_event(
        tracking,
        model_name,
        "annotate_planned",
        f"Annotate plan drafted: {n} element(s)",
    )
    append_root_event(tracking, "annotate_planned", f"{model_name}: annotate plan drafted")


def _record_element_bound(tracking: dict, model_name: str, summary: str, files: list[str]) -> None:
    m = require_model(tracking, model_name)
    structured = m.setdefault("structured", [])
    for name in files:
        if name not in structured:
            structured.append(name)
    append_model_event(tracking, model_name, "element_bound", summary)
    append_root_event(tracking, "element_bound", f"{model_name}: {summary}")


def _chosen_dict(el: dict) -> dict:
    chosen = el.get("chosen") or {}
    return {
        "system": chosen.get("system"),
        "code": chosen.get("code"),
        "display": chosen.get("display"),
    }


def _binding_row(el: dict) -> dict:
    decision = el.get("decision") or "pending"
    chosen = _chosen_dict(el)
    if decision == "unbound":
        reason = (el.get("reason") or "").strip()
        if not reason:
            raise click.ClickException(
                f"Element {el.get('path')} is unbound but has no reason."
            )
        return {
            "path": el["path"],
            "id": el.get("id"),
            "display": el.get("display"),
            "status": "unbound",
            "decision": "unbound",
            "strength": None,
            "system": None,
            "code": None,
            "display_term": None,
            "reason": reason,
        }
    if decision == "replace":
        if not chosen.get("code") or not chosen.get("system"):
            raise click.ClickException(
                f"Element {el.get('path')} is replace but chosen system/code is missing."
            )
        term = {
            "system": chosen["system"],
            "code": str(chosen["code"]),
            "display": chosen.get("display") or "",
        }
    elif decision == "accept":
        if chosen.get("code") and chosen.get("system"):
            term = {
                "system": chosen["system"],
                "code": str(chosen["code"]),
                "display": chosen.get("display") or "",
            }
        else:
            candidates = el.get("candidates") or []
            if not candidates:
                raise click.ClickException(
                    f"Element {el.get('path')} is accept but has no candidates and no chosen code."
                )
            first = candidates[0]
            term = {
                "system": first.get("system"),
                "code": str(first.get("code")),
                "display": first.get("display") or "",
            }
    else:
        raise click.ClickException(f"Cannot bind decision {decision!r} for {el.get('path')}")
    return {
        "path": el["path"],
        "id": el.get("id"),
        "display": el.get("display"),
        "status": "bound",
        "decision": decision,
        "strength": el.get("strength") or "example",
        "system": term["system"],
        "code": term["code"],
        "display_term": term["display"],
        "reason": el.get("reason") or "",
    }


@click.group()
def annotate():
    """Bind inventory elements to terminology codes."""


@annotate.command("plan")
@click.argument("model")
@click.option(
    "--element",
    "elements",
    multiple=True,
    help="Inventory path or unique id (repeatable).",
)
@click.option(
    "--all-undecided",
    is_flag=True,
    help="Include every inventory element that is not yet bound or unbound.",
)
@click.option(
    "--system",
    "systems",
    multiple=True,
    help="Candidate code system alias (snomed, loinc, icd-10). Repeatable. Default: snomed.",
)
def plan_cmd(model, elements, all_undecided, systems):
    """Write a draft annotate plan. Does not call ReasonHub; record MCP hits with enrich."""
    if bool(elements) == bool(all_undecided):
        raise click.UsageError("Pass --element (repeatable) or --all-undecided, not both or neither.")
    tracking = require_tracking()
    inventory = _assert_annotate_ready(tracking, model)
    aliases = _validate_systems(systems)
    bindings = load_bindings(model)
    selected = resolve_elements(inventory, elements, all_undecided, bindings)
    if all_undecided and len(selected) > ALL_UNDECIDED_WARN:
        log_warn(
            f"--all-undecided includes {len(selected)} elements (>{ALL_UNDECIDED_WARN}); "
            "record MCP hits with `annotate enrich` per element"
        )

    planned = []
    for el in selected:
        query = el.get("display") or el.get("id") or ""
        planned.append(
            {
                "id": el.get("id"),
                "path": el.get("path"),
                "display": el.get("display"),
                "query": query,
                "decision": "pending",
                "strength": "example",
                "reason": "",
                "chosen": {"system": None, "code": None, "display": None},
                "candidates": [],
            }
        )

    data = {
        "model": model,
        "status": "draft",
        "systems": aliases,
        "elements": planned,
    }
    save_plan(model, data)
    locked_update_tracking(lambda t, n=len(planned): _record_annotate_planned(t, model, n))
    log_info(f"Wrote annotate plan ({len(planned)} element(s), status=draft)")
    click.echo(f"  {annotate_plan_path(model)}")
    for item in planned:
        click.echo(
            f"  - {item['path']}  candidates={len(item['candidates'])}  query={item['query']!r}"
        )


@annotate.command("approve")
@click.argument("model")
def approve_cmd(model):
    """Mark the annotate plan approved (human gate)."""
    tracking = require_tracking()
    require_model(tracking, model)
    data = load_plan(model)
    data["status"] = "approved"
    save_plan(model, data)
    log_info(f"Approved annotate plan for {model}")


@annotate.command("enrich")
@click.argument("model")
@click.option(
    "--element",
    "element",
    required=True,
    help="Inventory path or unique id to attach candidates to.",
)
@click.option(
    "--candidate",
    "raw_candidates",
    multiple=True,
    help="MCP hit to record. Format: system|code|display[|distance[|confidence]]. Repeatable. At most 5 kept.",
)
@click.option("--lookup-query", default=None, help="Query used for MCP search. Defaults to the plan query.")
@click.option("--lookup-notes", default=None, help="Optional notes from the MCP lookup.")
def enrich_cmd(model, element, raw_candidates, lookup_query, lookup_notes):
    """Record ReasonHub MCP candidates on a draft plan element. Does not search."""
    tracking = require_tracking()
    require_model(tracking, model)
    plan = load_plan(model)
    if plan.get("status") == "approved":
        raise click.ClickException(
            "Annotate plan is already approved. Re-run `annotate plan` for a new draft before enriching."
        )
    inventory = _assert_annotate_ready(tracking, model)
    resolved = resolve_elements(inventory, (element,), False, load_bindings(model))
    target_path = resolved[0]["path"]
    match = None
    for el in plan.get("elements") or []:
        if el.get("path") == target_path:
            match = el
            break
    if match is None:
        raise click.ClickException(
            f"Element '{element}' (path {target_path}) is not in the annotate plan."
        )
    parsed = []
    for raw in raw_candidates:
        try:
            parsed.append(parse_candidate_flag(raw))
        except ValueError as exc:
            raise click.UsageError(str(exc)) from exc
    if len(parsed) > 5:
        log_warn(f"Keeping first 5 of {len(parsed)} candidates (FR-006 cap)")
        parsed = parsed[:5]
    for i, hit in enumerate(parsed, start=1):
        hit["rank"] = i
    match["candidates"] = parsed
    if lookup_query:
        match["query"] = lookup_query
    if lookup_notes is not None:
        match["lookup_notes"] = lookup_notes
    save_plan(model, plan)
    log_info(f"Recorded {len(parsed)} candidate(s) for {target_path}")
    click.echo(f"  {annotate_plan_path(model)}")


@annotate.command("implement")
@click.argument("model")
@click.option(
    "--replace",
    is_flag=True,
    help="Wipe bindings.yaml and rewrite from this plan's durable decisions only.",
)
def implement_cmd(model, replace):
    """Write structured/bindings.yaml from the approved plan."""
    tracking = require_tracking()
    _assert_annotate_ready(tracking, model)
    plan = load_plan(model)
    if plan.get("status") != "approved":
        raise click.ClickException(
            f"Annotate plan is not approved (status={plan.get('status')!r}). "
            f"Run `rh-mod-skills annotate approve {model}` after review."
        )

    existing = [] if replace else list(load_bindings(model).get("bindings") or [])
    by_path = {b.get("path"): b for b in existing if b.get("path")}
    applied = []
    for el in plan.get("elements") or []:
        decision = el.get("decision") or "pending"
        if decision in SKIP_DECISIONS:
            continue
        if decision not in DURABLE_DECISIONS:
            raise click.ClickException(
                f"Unknown decision {decision!r} for {el.get('path')}"
            )
        row = _binding_row(el)
        by_path[row["path"]] = row
        applied.append(row)

    out = {"model": model, "bindings": list(by_path.values())}
    save_yaml_file(bindings_path(model), out)
    files = [BINDINGS_NAME]

    parts = [f"{r['path']} ({r['decision']})" for r in applied] or ["(none)"]
    summary = "Bindings: " + ", ".join(parts)
    locked_update_tracking(lambda t, s=summary, f=files: _record_element_bound(t, model, s, f))
    log_info(summary)
    if files:
        click.echo(f"  {bindings_path(model)}")


def _verify_counts(inventory: dict, bindings: dict) -> tuple[int, int, int, list[str]]:
    inv_paths = {el["path"] for el in inventory_elements(inventory) if el.get("path")}
    bound = 0
    unbound = 0
    blocking: list[str] = []
    seen: set[str] = set()
    for row in bindings.get("bindings") or []:
        path = row.get("path")
        status = row.get("status")
        if status == "bound":
            bound += 1
            if path not in inv_paths:
                blocking.append(f"bound path not in inventory: {path}")
        elif status == "unbound":
            unbound += 1
            if not (row.get("reason") or "").strip():
                blocking.append(f"unbound missing reason: {path}")
        if path:
            seen.add(path)
    undecided = len(inv_paths - seen)
    return bound, unbound, undecided, blocking


@annotate.command("verify")
@click.argument("model")
def verify_cmd(model):
    """Non-destructive annotate report. Does not write tracking events."""
    tracking = require_tracking()
    require_model(tracking, model)
    before = tracking_file().read_text(encoding="utf-8")
    blocking_n = 0

    plan_path = annotate_plan_path(model)
    if plan_path.is_file():
        plan = load_yaml_file(plan_path)
        approved = plan.get("status") == "approved"
        click.echo(f"plan: {'approved' if approved else plan.get('status')}")
    else:
        click.echo("plan: missing")

    try:
        inventory = load_inventory(model)
    except click.ClickException as exc:
        click.echo(f"inventory: {exc}")
        blocking_n += 1
        inventory = {"entities": []}

    bpath = bindings_path(model)
    if bpath.is_file():
        bindings = load_yaml_file(bpath)
        click.echo("bindings: present")
    else:
        bindings = {"model": model, "bindings": []}
        click.echo("bindings: missing")

    bound, unbound, undecided, issues = _verify_counts(inventory, bindings)
    click.echo(f"bound={bound} unbound={unbound} undecided={undecided}")
    for issue in issues:
        click.echo(f"  blocking: {issue}")
        blocking_n += 1

    after = tracking_file().read_text(encoding="utf-8")
    if before != after:
        raise click.ClickException("verify mutated tracking.yaml — this is a bug")
    if blocking_n:
        raise click.ClickException(f"annotate verify failed: {blocking_n} blocking issue(s)")
    log_info("annotate verify passed")
