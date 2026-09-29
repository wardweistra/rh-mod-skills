"""rh-mod-skills ig — stage an IG Publisher tree from a formalize snapshot."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import click
import httpx

from rh_mod_skills.commands.annotate import load_yaml_file
from rh_mod_skills.commands.formalize import fhir_id, fhir_name, snapshot_path, write_json
from rh_mod_skills.common import (
    append_model_event,
    append_root_event,
    consumer_root,
    locked_update_tracking,
    log_info,
    model_dir,
    require_model,
    require_tracking,
)

SCRIPTS_PIN = "9e6c7de21624e99dfd6739657a7895dfbe7d1357"
SCRIPT_NAMES = (
    "_build.sh",
    "_build.bat",
    "_genonce.sh",
    "_genonce.bat",
    "_gencontinuous.sh",
    "_gencontinuous.bat",
    "_updatePublisher.sh",
    "_updatePublisher.bat",
)
RAW_BASE = f"https://raw.githubusercontent.com/HL7/ig-publisher-scripts/{SCRIPTS_PIN}"
IG_GITIGNORE = "output/\ntemp/\ninput-cache/\n*.jar\n"


def ig_dir(name: str) -> Path:
    return model_dir(name) / "ig"


def sidecar_path(name: str) -> Path:
    return ig_dir(name) / "rh-mod.yaml"


def managed_path(name: str) -> Path:
    return ig_dir(name) / "managed-files.yaml"


def save_yaml_file(path: Path, data: dict) -> None:
    from ruamel.yaml import YAML

    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        y.dump(data, f)


def fetch_script(name: str) -> str:
    url = f"{RAW_BASE}/{name}"
    try:
        response = httpx.get(url, follow_redirects=True, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise click.ClickException(f"Failed to download IG Publisher script {name}: {exc}") from exc
    return response.text


def guess_package(canonical: str, model: str) -> tuple[str, str]:
    parsed = urlparse(canonical)
    package_id = f"{parsed.netloc}.fhir.{model}".lower()
    if "/StructureDefinition/" in canonical:
        base = canonical.split("/StructureDefinition/", 1)[0]
    else:
        base = canonical.rsplit("/", 1)[0]
    return package_id, f"{base}/ImplementationGuide/{model}"


def load_snapshot(model: str) -> dict:
    path = snapshot_path(model)
    if not path.is_file():
        raise click.ClickException(
            f"No snapshot at {path}. Run `rh-mod-skills formalize implement {model}` first."
        )
    return load_yaml_file(path)


def _ensure_scripts(root: Path, previous_pin: str | None) -> int:
    missing = [n for n in SCRIPT_NAMES if not (root / n).is_file()]
    if previous_pin == SCRIPTS_PIN and not missing:
        return 0
    n = 0
    for name in SCRIPT_NAMES:
        text = fetch_script(name)
        dest = root / name
        dest.write_text(text, encoding="utf-8")
        if name.endswith(".sh"):
            dest.chmod(0o755)
        n += 1
    return n


def _ensure_text(path: Path, contents: str) -> None:
    if path.exists():
        return
    path.write_text(contents, encoding="utf-8")


def _ensure_sidecar(model: str, canonical: str) -> dict:
    path = sidecar_path(model)
    if path.is_file():
        return load_yaml_file(path)
    package_id, url = guess_package(canonical, model)
    data = {"package_id": package_id, "url": url}
    save_yaml_file(path, data)
    return data


def _load_json(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _rel_for(filename: str, resource_type: str) -> str | None:
    if resource_type == "StructureDefinition":
        return f"input/models/{filename}"
    if resource_type == "ValueSet":
        return f"input/vocabulary/{filename}"
    return None


def _posix(rel: str) -> str:
    return rel.replace("\\", "/")


def build_implementation_guide(
    model: str,
    sidecar: dict,
    version: str,
    resources: list[dict],
) -> dict:
    ig_id = fhir_id(model)
    entries = []
    for data in resources:
        rid = data.get("id") or ig_id
        entries.append(
            {
                "reference": {"reference": f"{data.get('resourceType')}/{rid}"},
                "name": data.get("name") or data.get("title") or rid,
                "exampleBoolean": False,
            }
        )
    return {
        "resourceType": "ImplementationGuide",
        "id": ig_id,
        "url": sidecar.get("url"),
        "version": version,
        "name": fhir_name(model),
        "status": "draft",
        "packageId": sidecar.get("package_id"),
        "fhirVersion": ["4.0.1"],
        "definition": {"resource": entries},
    }


def _record_ig_synced(tracking: dict, model_name: str, n: int) -> None:
    append_model_event(
        tracking,
        model_name,
        "ig_synced",
        f"IG tree synced ({n} managed file(s))",
    )
    append_root_event(tracking, "ig_synced", f"{model_name}: IG tree synced")


@click.group()
def ig():
    """Stage an IG Publisher tree from a formalized snapshot."""


@ig.command("sync")
@click.argument("model")
def sync_cmd(model):
    """Copy snapshot JSON into models/<model>/ig/ for the IG Publisher."""
    tracking = require_tracking()
    require_model(tracking, model)
    snap = load_snapshot(model)
    canonical = str(snap.get("canonical") or "").strip()
    version = str(snap.get("version") or "").strip() or "0.1.0"
    if not canonical:
        raise click.ClickException("snapshot.yaml is missing canonical.")

    root = ig_dir(model)
    root.mkdir(parents=True, exist_ok=True)
    previous = load_yaml_file(managed_path(model)) if managed_path(model).is_file() else {}
    fetched = _ensure_scripts(root, previous.get("pin"))
    _ensure_text(
        root / "ig.ini",
        f"[IG]\nig = input/ImplementationGuide-{fhir_id(model)}.json\ntemplate = fhir.base.template\n",
    )
    _ensure_text(root / ".gitignore", IG_GITIGNORE)
    sidecar = _ensure_sidecar(model, canonical)

    consumer = consumer_root()
    copied: list[dict] = []
    desired: list[str] = []
    for row in snap.get("files") or []:
        rel = row.get("path")
        if not rel:
            continue
        src = consumer / rel
        if not src.is_file():
            raise click.ClickException(f"Snapshot file missing: {rel}")
        if src.name == "snapshot.yaml" or src.suffix.lower() != ".json":
            continue
        data = _load_json(src)
        target_rel = _rel_for(src.name, data.get("resourceType") or "")
        if not target_rel:
            continue
        dest = root / target_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        copied.append(data)
        desired.append(_posix(target_rel))

    ig_rel = f"input/ImplementationGuide-{fhir_id(model)}.json"
    write_json(root / ig_rel, build_implementation_guide(model, sidecar, version, copied))
    desired.append(_posix(ig_rel))

    old_files = [_posix(p) for p in (previous.get("files") or [])]
    for rel in old_files:
        if rel in desired:
            continue
        stale = root / rel
        if stale.is_file():
            stale.unlink()

    save_yaml_file(managed_path(model), {"pin": SCRIPTS_PIN, "files": desired})
    locked_update_tracking(lambda t, n=len(desired): _record_ig_synced(t, model, n))
    log_info(f"Synced IG tree ({len(desired)} managed file(s), scripts_fetched={fetched})")
    click.echo(f"  {root}")
