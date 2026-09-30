"""rh-mod-skills formalize — FHIR logical StructureDefinition from L2 YAML."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import click
from ruamel.yaml import YAML

from rh_mod_skills.commands.annotate import load_yaml_file, validate_value_set
from rh_mod_skills.commands.extract import _assert_ingest_clean
from rh_mod_skills.commands.specify import (
    CARD_RE,
    assert_logical_model_v2,
    logical_model_path,
)
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
FHIR_PATH_SEGMENT_MAX = 64
DEFAULT_CANONICAL_HOST = "https://example.org/fhir"


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
    data = load_yaml_file(path)
    return assert_logical_model_v2(data)


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


def mapping_identity(system: str) -> str:
    """Stable StructureDefinition.mapping identity slug from a system URI."""
    s = re.sub(r"^https?://", "", str(system or "").strip(), flags=re.I)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return fhir_id(s or "system")


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


def default_canonical_base(model: str) -> str:
    return f"{DEFAULT_CANONICAL_HOST}/{model}"


def derive_structure_definition_url(canonical_base: str, model_id: str) -> str:
    base = (canonical_base or "").strip().rstrip("/")
    return f"{base}/StructureDefinition/{model_id}"


def _validate_http_uri(url: str, field: str) -> str:
    cleaned = (url or "").strip().rstrip("/")
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise click.ClickException(
            f"Formalize plan {field} must be an http(s) URI. "
            "Edit process/plans/formalize-plan.yaml then approve."
        )
    return cleaned


def resolve_plan_canonical(plan: dict, model: str) -> tuple[str, str]:
    """Return (canonical_base, StructureDefinition url) for Epic A single-SD."""
    base_raw = plan.get("canonical_base")
    explicit = (plan.get("canonical") or "").strip()
    if base_raw is not None and str(base_raw).strip():
        base = _validate_http_uri(str(base_raw), "canonical_base")
        derived = derive_structure_definition_url(base, model)
        last = derived.rsplit("/", 1)[-1]
        if last != model:
            raise click.ClickException(
                f"Derived StructureDefinition URL last segment must equal model id {model!r} "
                f"(got {last!r}). Example canonical_base: {default_canonical_base(model)}"
            )
        if explicit and explicit.rstrip("/") != derived:
            raise click.ClickException(
                f"Formalize plan canonical must equal "
                f"{{canonical_base}}/StructureDefinition/{{model}} ({derived!r}); "
                f"got {explicit!r}."
            )
        return base, derived
    if not explicit:
        raise click.ClickException(
            "Formalize plan needs canonical_base (preferred) or canonical. "
            f"Example canonical_base: {default_canonical_base(model)}"
        )
    url = _validate_http_uri(explicit, "canonical")
    last = url.rsplit("/", 1)[-1]
    if last != model:
        raise click.ClickException(
            f"Formalize plan canonical last segment must equal the model id {model!r} "
            f"(IG Publisher requires StructureDefinition.url to match the differential root). "
            f"Got {last!r}. Prefer canonical_base "
            f"{default_canonical_base(model)!r} → …/StructureDefinition/{model}."
        )
    if "/StructureDefinition/" in url:
        base = url.split("/StructureDefinition/", 1)[0]
    else:
        base = url.rsplit("/", 1)[0]
    return base, url


def long_path_segments(model: str, lm: dict) -> list[str]:
    """FHIR path name portions (dot segments) must be ≤ 64 characters."""
    paths = [model]
    for ent in lm.get("entities") or []:
        eid = ent.get("id") or "entity"
        paths.append(f"{model}.{eid}")
        for el in ent.get("elements") or []:
            path = el.get("path") or eid
            paths.append(f"{model}.{path}")
    bad: list[str] = []
    for full in paths:
        for part in str(full).split("."):
            if len(part) > FHIR_PATH_SEGMENT_MAX:
                bad.append(f"{full} (segment {part!r} is {len(part)} chars)")
    return bad


def element_status(el: dict) -> str | None:
    status = el.get("status")
    if status in ("mapped", "unbound"):
        return status
    mappings = el.get("mappings") or []
    if mappings:
        return "mapped"
    vs = el.get("value_set")
    if isinstance(vs, dict) and vs:
        return "mapped"
    binding = el.get("binding") or {}
    if binding.get("status") == "bound":
        return "mapped"
    if binding.get("status") == "unbound":
        return "unbound"
    return status


def summarize_lm(lm: dict) -> tuple[list[str], int, int, int, int]:
    unknown_dt: list[str] = []
    unknown_card = 0
    mapped = 0
    value_set_bound = 0
    unbound = 0
    for _ent, el in iter_lm_elements(lm):
        path = el.get("path") or "?"
        if (el.get("datatype") or "unknown") == "unknown":
            unknown_dt.append(path)
        if (el.get("cardinality") or "unknown") == "unknown":
            unknown_card += 1
        status = element_status(el)
        vs = el.get("value_set")
        if isinstance(vs, dict) and vs:
            value_set_bound += 1
        if status == "mapped":
            mapped += 1
        elif status == "unbound":
            unbound += 1
    return unknown_dt, unknown_card, mapped, value_set_bound, unbound


def collect_mapping_identities(lm: dict) -> list[dict]:
    """StructureDefinition.mapping entries for every distinct system URI."""
    by_id: dict[str, dict] = {}
    for _ent, el in iter_lm_elements(lm):
        for m in el.get("mappings") or []:
            system = m.get("system")
            if not system:
                continue
            ident = mapping_identity(str(system))
            by_id.setdefault(
                ident,
                {"identity": ident, "uri": str(system), "name": ident},
            )
    return list(by_id.values())


def build_valueset(
    model: str,
    canonical: str,
    version: str,
    el: dict,
    vs: dict,
) -> tuple[str, dict]:
    """Build a multi-concept ValueSet from authored value_set.concepts[]."""
    path = el.get("path") or "element"
    vs_id = fhir_id(f"{model}-{path.replace('.', '-')}")
    url = valueset_url(canonical, vs_id)
    by_system: dict[str, list[dict]] = {}
    for concept in vs.get("concepts") or []:
        system = concept.get("system")
        code = concept.get("code")
        if not system or code in (None, ""):
            continue
        by_system.setdefault(str(system), []).append(
            {
                "code": str(code),
                "display": concept.get("display") or "",
            }
        )
    if not by_system:
        raise click.ClickException(
            f"value_set on {path} has no valid concepts with system+code"
        )
    include = [
        {"system": system, "concept": concepts}
        for system, concepts in by_system.items()
    ]
    resource = {
        "resourceType": "ValueSet",
        "id": vs_id,
        "url": url,
        "version": version,
        "name": fhir_name(vs_id.replace(".", "-")),
        "status": "draft",
        "compose": {"include": include},
    }
    return vs_id, resource


def build_structure_definition(
    model: str,
    lm: dict,
    canonical: str,
    version: str,
    name: str,
    vs_urls: dict[str, str] | None = None,
    vs_strengths: dict[str, str] | None = None,
) -> dict:
    vs_urls = vs_urls or {}
    vs_strengths = vs_strengths or {}
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
            ed_mappings = []
            for m in el.get("mappings") or []:
                system = m.get("system")
                code = m.get("code")
                if not system or code in (None, ""):
                    continue
                ed_mappings.append(
                    {
                        "identity": mapping_identity(str(system)),
                        "map": str(code),
                    }
                )
            if ed_mappings:
                row["mapping"] = ed_mappings
            if path in vs_urls:
                row["binding"] = {
                    "strength": vs_strengths.get(path) or "example",
                    "valueSet": vs_urls[path],
                }
            elements.append(row)
    sd = {
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
    identities = collect_mapping_identities(lm)
    if identities:
        sd["mapping"] = identities
    return sd


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
    """Write a draft formalize plan (canonical_base + version)."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    lm = load_logical_model(model)
    unknown_dt, unknown_card, mapped, value_set_bound, unbound = summarize_lm(lm)
    canonical_base = default_canonical_base(model)
    canonical = derive_structure_definition_url(canonical_base, model)
    data = {
        "model": model,
        "status": "draft",
        "canonical_base": canonical_base,
        "canonical": canonical,
        "version": "0.1.0",
        "name": fhir_name(model),
        "unknown_datatype": unknown_dt,
        "unknown_cardinality": unknown_card,
        "mapped": mapped,
        "value_set_bound": value_set_bound,
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
    """Write StructureDefinition, ValueSets (when authored), and snapshot under computable/."""
    tracking = require_tracking()
    require_model(tracking, model)
    _assert_ingest_clean(tracking, model)
    plan = load_plan(model)
    if plan.get("status") != "approved":
        raise click.ClickException(
            f"Formalize plan is not approved (status={plan.get('status')!r}). "
            f"Run `rh-mod-skills formalize approve {model}` after review."
        )
    canonical_base, canonical = resolve_plan_canonical(plan, model)
    version = str(plan.get("version") or "").strip()
    if not version:
        raise click.ClickException("Formalize plan version is empty.")
    name = str(plan.get("name") or fhir_name(model))
    lm = load_logical_model(model)
    unknown_dt, _unknown_card, _mapped, _vs_bound, _unbound = summarize_lm(lm)
    if unknown_dt:
        listed = ", ".join(unknown_dt[:8])
        more = "" if len(unknown_dt) <= 8 else f" (+{len(unknown_dt) - 8} more)"
        raise click.ClickException(
            f"Cannot formalize with unknown datatype: {listed}{more}. "
            "Fix types on the specify plan and re-implement specify first."
        )
    too_long = long_path_segments(model, lm)
    if too_long:
        listed = "; ".join(too_long[:6])
        more = "" if len(too_long) <= 6 else f" (+{len(too_long) - 6} more)"
        raise click.ClickException(
            f"Cannot formalize: FHIR path name portions must be ≤ {FHIR_PATH_SEGMENT_MAX} characters: "
            f"{listed}{more}. Re-run extract so slugs are truncated, then specify again."
        )

    for _ent, el in iter_lm_elements(lm):
        status = element_status(el)
        mappings = el.get("mappings") or []
        vs = validate_value_set(el.get("path"), el.get("value_set"))
        if status == "mapped":
            if mappings:
                for m in mappings:
                    if not m.get("system") or m.get("code") in (None, ""):
                        raise click.ClickException(
                            f"Mapped element {el.get('path')} has a mapping missing system/code."
                        )
            if not mappings and vs is None:
                raise click.ClickException(
                    f"Mapped element {el.get('path')} is missing mappings[] and value_set."
                )

    out_dir = computable_dir(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("ValueSet-*.json"):
        stale.unlink()
    for stale in out_dir.glob("ConceptMap-*.json"):
        stale.unlink()

    vs_urls: dict[str, str] = {}
    vs_strengths: dict[str, str] = {}
    json_files: list[Path] = []
    for _ent, el in iter_lm_elements(lm):
        path = el.get("path")
        vs = validate_value_set(path, el.get("value_set"))
        if vs is None:
            continue
        vs_id, vs_resource = build_valueset(model, canonical, version, el, vs)
        vs_path = out_dir / f"ValueSet-{vs_id}.json"
        write_json(vs_path, vs_resource)
        vs_urls[path] = vs_resource["url"]
        vs_strengths[path] = vs["strength"]
        json_files.append(vs_path)

    sd = build_structure_definition(
        model, lm, canonical, version, name, vs_urls=vs_urls, vs_strengths=vs_strengths
    )
    sd_path = out_dir / f"StructureDefinition-{fhir_id(model)}.json"
    write_json(sd_path, sd)
    json_files.insert(0, sd_path)

    root = consumer_root()
    json_meta = [
        {"path": str(p.relative_to(root)), "checksum": sha256_file(p)} for p in json_files
    ]
    snap = {
        "model": model,
        "canonical_base": canonical_base,
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
    for p in json_files[1:]:
        click.echo(f"  {p}")
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
        url = str(sd.get("url") or "")
        last = url.rstrip("/").rsplit("/", 1)[-1] if url else ""
        if last and last != model:
            click.echo(
                f"  blocking: StructureDefinition.url last segment is {last!r}, "
                f"expected model id {model!r}"
            )
            blocking_n += 1
    else:
        sd = {}
        click.echo("structuredefinition: missing")
        blocking_n += 1

    _unknown_dt, unknown_card, mapped, value_set_bound, _unbound = summarize_lm(lm)
    click.echo(
        f"cardinality-default-n={unknown_card} mapped={mapped} "
        f"value_set_bound={value_set_bound} validator=not-run"
    )

    too_long = long_path_segments(model, lm)
    for issue in too_long:
        click.echo(f"  blocking: path name portion exceeds {FHIR_PATH_SEGMENT_MAX}: {issue}")
        blocking_n += 1

    expected_leaf = {f"{model}.{el.get('path')}" for _e, el in iter_lm_elements(lm) if el.get("path")}
    expected_ent = {f"{model}.{ent.get('id')}" for ent in lm.get("entities") or [] if ent.get("id")}
    expected = expected_leaf | expected_ent | {model}
    actual = _sd_paths(sd)
    if sd:
        for path in sorted(expected - actual):
            click.echo(f"  blocking: differential missing path {path}")
            blocking_n += 1
        sd_map_ids = {
            m.get("identity") for m in (sd.get("mapping") or []) if m.get("identity")
        }
        by_path = {
            el.get("path"): el
            for el in (sd.get("differential") or {}).get("element") or []
            if el.get("path")
        }
        for _ent, el in iter_lm_elements(lm):
            path = el.get("path")
            fpath = f"{model}.{path}" if path else None
            mappings = el.get("mappings") or []
            try:
                value_set = validate_value_set(path, el.get("value_set"))
            except click.ClickException as exc:
                click.echo(f"  blocking: {exc}")
                blocking_n += 1
                value_set = None
            row = by_path.get(fpath or "") or {}
            if mappings and value_set is None:
                # mappings-only: must have ElementDefinition.mapping; must NOT have ValueSet/binding
                ed_maps = row.get("mapping") or []
                if len(ed_maps) != len(mappings):
                    click.echo(
                        f"  blocking: ElementDefinition.mapping count mismatch for {path}"
                    )
                    blocking_n += 1
                for m in mappings:
                    ident = mapping_identity(str(m.get("system") or ""))
                    if ident not in sd_map_ids:
                        click.echo(
                            f"  blocking: missing StructureDefinition.mapping identity {ident} "
                            f"for {path}"
                        )
                        blocking_n += 1
                if row.get("binding"):
                    click.echo(
                        f"  blocking: mappings-only path {path} must not have ElementDefinition.binding"
                    )
                    blocking_n += 1
                vs_id = fhir_id(f"{model}-{(path or '').replace('.', '-')}")
                vs_file = computable_dir(model) / f"ValueSet-{vs_id}.json"
                if vs_file.is_file():
                    click.echo(f"  blocking: mappings-only path {path} must not have ValueSet")
                    blocking_n += 1
            if value_set is not None:
                binding = row.get("binding") or {}
                if not binding.get("valueSet"):
                    click.echo(
                        f"  blocking: value_set path {path} missing ElementDefinition.binding.valueSet"
                    )
                    blocking_n += 1
                elif binding.get("strength") != value_set.get("strength"):
                    click.echo(
                        f"  blocking: value_set path {path} binding strength mismatch"
                    )
                    blocking_n += 1
                vs_id = fhir_id(f"{model}-{(path or '').replace('.', '-')}")
                vs_file = computable_dir(model) / f"ValueSet-{vs_id}.json"
                if not vs_file.is_file():
                    click.echo(f"  blocking: value_set path {path} missing ValueSet file")
                    blocking_n += 1
            if list(computable_dir(model).glob("ConceptMap-*.json")):
                click.echo("  blocking: ConceptMap resources are out of scope")
                blocking_n += 1
                break

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
