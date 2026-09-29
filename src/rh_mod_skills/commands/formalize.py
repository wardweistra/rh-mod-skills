"""rh-mod-skills formalize — FHIR logical StructureDefinition from L2 YAML."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import click
from ruamel.yaml import YAML

from rh_mod_skills.commands.annotate import load_yaml_file
from rh_mod_skills.commands.extract import _assert_ingest_clean
from rh_mod_skills.commands.specify import CARD_RE, logical_model_path
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

PLAN_NAME = "formalize-plan.yaml"
SNAPSHOT_NAME = "snapshot.yaml"
BASE_DEFINITION = "http://hl7.org/fhir/StructureDefinition/Base"


def _yaml() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    return y


def formalize_plan_path(name: str) -> Path:
    return model_dir(name) / "process" / "plans" / PLAN_NAME


def computable_dir(name: str) -> Path:
    return model_dir(name) / "computable"


def snapshot_path(name: str) -> Path:
    return computable_dir(name) / SNAPSHOT_NAME


def save_yaml_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        _yaml().dump(data, f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_plan(model: str) -> dict:
    path = formalize_plan_path(model)
    if not path.exists():
        raise click.ClickException(
            f"No formalize plan at {path}. Run `rh-mod-skills formalize plan {model}` first."
        )
    return load_yaml_file(path)


def load_logical_model(model: str) -> dict:
    path = logical_model_path(model)
    if not path.is_file():
        raise click.ClickException(
            f"No logical model at {path}. Run `rh-mod-skills specify implement {model}` first."
        )
    return load_yaml_file(path)


def fhir_name(model: str) -> str:
    parts = [p for p in (model or "").split("-") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or "Model"


def fhir_id(text: str, max_len: int = 64) -> str:
    s = re.sub(r"[^A-Za-z0-9.-]+", "-", str(text or "")).strip("-.")
    if not s:
        s = "id"
    if len(s) <= max_len:
        return s
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{s[: max_len - 9]}-{digest}"


def min_max(cardinality: str | None) -> tuple[int, str]:
    raw = (cardinality or "").strip()
    if not raw or raw == "unknown":
        return 0, "1"
    if not CARD_RE.match(raw):
        return 0, "1"
    lo, hi = raw.split("..", 1)
    return int(lo), hi


def iter_lm_elements(lm: dict):
    for ent in lm.get("entities") or []:
        for el in ent.get("elements") or []:
            yield ent, el


def valueset_url(canonical: str, vs_id: str) -> str:
    if "/StructureDefinition/" in canonical:
        base = canonical.split("/StructureDefinition/", 1)[0]
        return f"{base}/ValueSet/{vs_id}"
    parent = canonical.rsplit("/", 1)[0]
    return f"{parent}/ValueSet/{vs_id}"


def _validate_canonical(canonical: str) -> str:
    url = (canonical or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise click.ClickException(
            "Formalize plan canonical must be an http(s) URI. "
            "Edit process/plans/formalize-plan.yaml then approve."
        )
    return url


def summarize_lm(lm: dict) -> tuple[list[str], int, int, int]:
    unknown_dt: list[str] = []
    unknown_card = 0
    bound = 0
    unbound = 0
    for _ent, el in iter_lm_elements(lm):
        path = el.get("path") or "?"
        if (el.get("datatype") or "unknown") == "unknown":
            unknown_dt.append(path)
        if (el.get("cardinality") or "unknown") == "unknown":
            unknown_card += 1
        status = (el.get("binding") or {}).get("status")
        if status == "bound":
            bound += 1
        elif status == "unbound":
            unbound += 1
    return unknown_dt, unknown_card, bound, unbound


def build_valueset(model: str, canonical: str, version: str, el: dict) -> tuple[str, dict]:
    path = el.get("path") or "element"
    vs_id = fhir_id(f"{model}-{path.replace('.', '-')}")
    binding = el.get("binding") or {}
    url = valueset_url(canonical, vs_id)
    vs = {
        "resourceType": "ValueSet",
        "id": vs_id,
        "url": url,
        "version": version,
        "name": fhir_name(vs_id.replace(".", "-")),
        "status": "draft",
        "compose": {
            "include": [
                {
                    "system": binding.get("system"),
                    "concept": [
                        {
                            "code": str(binding.get("code")),
                            "display": binding.get("display") or "",
                        }
                    ],
                }
            ]
        },
    }
    return vs_id, vs


def build_structure_definition(
    model: str,
    lm: dict,
    canonical: str,
    version: str,
    name: str,
    vs_urls: dict[str, str],
) -> dict:
    root = model
    elements = [
        {
            "id": root,
            "path": root,
            "min": 0,
            "max": "1",
            "short": name,
        }
    ]
    for ent in lm.get("entities") or []:
        eid = ent.get("id") or "entity"
        epath = f"{root}.{eid}"
        elements.append(
            {
                "id": epath,
                "path": epath,
                "short": ent.get("title") or eid,
                "min": 0,
                "max": "1",
                "type": [{"code": "BackboneElement"}],
            }
        )
        for el in ent.get("elements") or []:
            path = el.get("path") or eid
            fpath = f"{root}.{path}"
            lo, hi = min_max(el.get("cardinality"))
            row = {
                "id": fpath,
                "path": fpath,
                "short": el.get("display") or path,
                "definition": el.get("display") or path,
                "min": lo,
                "max": str(hi),
                "type": [{"code": el.get("datatype")}],
            }
            binding = el.get("binding") or {}
            if binding.get("status") == "bound" and path in vs_urls:
                row["binding"] = {
                    "strength": binding.get("strength") or "example",
                    "valueSet": vs_urls[path],
                }
            elements.append(row)
    return {
        "resourceType": "StructureDefinition",
        "id": fhir_id(model),
        "url": canonical,
        "version": version,
        "name": name,
        "status": "draft",
        "kind": "logical",
        "abstract": False,
        "type": canonical,
        "baseDefinition": BASE_DEFINITION,
        "derivation": "specialization",
        "differential": {"element": elements},
    }


def _record_model_formalized(tracking: dict, model_name: str, files: list[str]) -> None:
    m = require_model(tracking, model_name)
    computable = m.setdefault("computable", [])
    for name in files:
        if name not in computable:
            computable.append(name)
    append_model_event(
        tracking,
        model_name,
        "model_formalized",
        f"Formalized logical model: {len(files)} file(s)",
    )
    append_root_event(tracking, "model_formalized", f"{model_name}: logical model formalized")


@click.group()
def formalize():
    """Emit a FHIR logical StructureDefinition from a specified model."""


@formalize.command("plan")
@click.argument("model")
def plan_cmd(model):
    """Write a draft formalize plan (canonical URL + version)."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    lm = load_logical_model(model)
    unknown_dt, unknown_card, bound, unbound = summarize_lm(lm)
    data = {
        "model": model,
        "status": "draft",
        "canonical": f"http://example.org/fhir/StructureDefinition/{model}",
        "version": "0.1.0",
        "name": fhir_name(model),
        "unknown_datatype": unknown_dt,
        "unknown_cardinality": unknown_card,
        "bound": bound,
        "unbound": unbound,
    }
    save_yaml_file(formalize_plan_path(model), data)
    log_info("Wrote formalize plan (status=draft)")
    click.echo(f"  {formalize_plan_path(model)}")
    if unknown_dt:
        log_info(f"{len(unknown_dt)} element(s) still have unknown datatype — implement will fail")


@formalize.command("approve")
@click.argument("model")
def approve_cmd(model):
    """Mark the formalize plan approved (human gate)."""
    tracking = require_tracking()
    require_model(tracking, model)
    data = load_plan(model)
    data["status"] = "approved"
    save_yaml_file(formalize_plan_path(model), data)
    log_info(f"Approved formalize plan for {model}")


@formalize.command("implement")
@click.argument("model")
def implement_cmd(model):
    """Write StructureDefinition, ValueSets, and snapshot under computable/."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    plan = load_plan(model)
    if plan.get("status") != "approved":
        raise click.ClickException(
            f"Formalize plan is not approved (status={plan.get('status')!r}). "
            f"Run `rh-mod-skills formalize approve {model}` after review."
        )
    canonical = _validate_canonical(str(plan.get("canonical") or ""))
    version = str(plan.get("version") or "").strip()
    if not version:
        raise click.ClickException("Formalize plan version is empty.")
    name = str(plan.get("name") or fhir_name(model))
    lm = load_logical_model(model)
    unknown_dt, _unknown_card, _bound, _unbound = summarize_lm(lm)
    if unknown_dt:
        listed = ", ".join(unknown_dt[:8])
        more = "" if len(unknown_dt) <= 8 else f" (+{len(unknown_dt) - 8} more)"
        raise click.ClickException(
            f"Cannot formalize with unknown datatype: {listed}{more}. "
            "Fix types on the specify plan and re-implement specify first."
        )

    out_dir = computable_dir(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    vs_urls: dict[str, str] = {}
    json_files: list[Path] = []
    for _ent, el in iter_lm_elements(lm):
        binding = el.get("binding") or {}
        if binding.get("status") != "bound":
            continue
        if not binding.get("system") or binding.get("code") in (None, ""):
            raise click.ClickException(
                f"Bound element {el.get('path')} is missing system/code."
            )
        vs_id, vs = build_valueset(model, canonical, version, el)
        vs_path = out_dir / f"ValueSet-{vs_id}.json"
        write_json(vs_path, vs)
        vs_urls[el.get("path")] = vs["url"]
        json_files.append(vs_path)

    sd = build_structure_definition(model, lm, canonical, version, name, vs_urls)
    sd_path = out_dir / f"StructureDefinition-{fhir_id(model)}.json"
    write_json(sd_path, sd)
    json_files.append(sd_path)

    root = consumer_root()
    json_meta = [
        {"path": str(p.relative_to(root)), "checksum": sha256_file(p)} for p in json_files
    ]
    snap = {
        "model": model,
        "canonical": canonical,
        "version": version,
        "kind": "logical",
        "files": json_meta,
    }
    snap_file = snapshot_path(model)
    save_yaml_file(snap_file, snap)

    tracking_names = [p.name for p in json_files]
    tracking_names.append(SNAPSHOT_NAME)
    locked_update_tracking(
        lambda t, names=tracking_names: _record_model_formalized(t, model, names)
    )
    log_info(f"Wrote formalized logical model ({len(json_meta)} JSON file(s))")
    click.echo(f"  {sd_path}")
    click.echo(f"  {snap_file}")


def _sd_paths(sd: dict) -> set[str]:
    return {
        el.get("path")
        for el in (sd.get("differential") or {}).get("element") or []
        if el.get("path")
    }


@formalize.command("verify")
@click.argument("model")
def verify_cmd(model):
    """Non-destructive formalize report. Does not write tracking events."""
    tracking = require_tracking()
    require_model(tracking, model)
    before = tracking_file().read_text(encoding="utf-8")
    blocking_n = 0

    plan_path = formalize_plan_path(model)
    if plan_path.is_file():
        click.echo(f"plan: {load_yaml_file(plan_path).get('status')}")
    else:
        click.echo("plan: missing")

    try:
        lm = load_logical_model(model)
    except click.ClickException as exc:
        click.echo(f"logical-model: {exc}")
        blocking_n += 1
        lm = {"entities": []}

    sd_file = computable_dir(model) / f"StructureDefinition-{fhir_id(model)}.json"
    if sd_file.is_file():
        sd = json.loads(sd_file.read_text(encoding="utf-8"))
        click.echo("structuredefinition: present")
        if sd.get("kind") != "logical":
            click.echo(f"  blocking: kind is {sd.get('kind')!r}, expected 'logical'")
            blocking_n += 1
        if sd.get("resourceType") != "StructureDefinition":
            click.echo("  blocking: resourceType is not StructureDefinition")
            blocking_n += 1
    else:
        sd = {}
        click.echo("structuredefinition: missing")
        blocking_n += 1

    _unknown_dt, unknown_card, bound, _unbound = summarize_lm(lm)
    click.echo(f"cardinality-default-n={unknown_card} bound={bound} validator=not-run")

    expected_leaf = {f"{model}.{el.get('path')}" for _e, el in iter_lm_elements(lm) if el.get("path")}
    expected_ent = {f"{model}.{ent.get('id')}" for ent in lm.get("entities") or [] if ent.get("id")}
    expected = expected_leaf | expected_ent | {model}
    actual = _sd_paths(sd)
    if sd:
        for path in sorted(expected - actual):
            click.echo(f"  blocking: differential missing path {path}")
            blocking_n += 1
        for _ent, el in iter_lm_elements(lm):
            binding = el.get("binding") or {}
            if binding.get("status") != "bound":
                continue
            vs_id = fhir_id(f"{model}-{(el.get('path') or '').replace('.', '-')}")
            vs_file = computable_dir(model) / f"ValueSet-{vs_id}.json"
            if not vs_file.is_file():
                click.echo(f"  blocking: missing ValueSet for {el.get('path')}")
                blocking_n += 1

    snap_file = snapshot_path(model)
    if snap_file.is_file():
        snap = load_yaml_file(snap_file)
        root = consumer_root()
        for row in snap.get("files") or []:
            rel = row.get("path")
            expected_sum = row.get("checksum")
            if not rel or not expected_sum:
                click.echo(f"  blocking: snapshot row missing path/checksum: {rel}")
                blocking_n += 1
                continue
            target = root / rel
            if not target.is_file():
                click.echo(f"  blocking: snapshot file missing: {rel}")
                blocking_n += 1
                continue
            actual_sum = sha256_file(target)
            if actual_sum != expected_sum:
                click.echo(f"  blocking: checksum mismatch: {rel}")
                blocking_n += 1
    else:
        click.echo("snapshot: missing")
        blocking_n += 1

    after = tracking_file().read_text(encoding="utf-8")
    if before != after:
        raise click.ClickException("verify mutated tracking.yaml — this is a bug")
    if blocking_n:
        raise click.ClickException(f"formalize verify failed: {blocking_n} blocking issue(s)")
    log_info("formalize verify passed")
