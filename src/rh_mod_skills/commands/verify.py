"""rh-mod-skills verify — read-only lifecycle coordinator."""

from __future__ import annotations

import click
from click.testing import CliRunner

from rh_mod_skills.commands.annotate import (
    _verify_counts,
    annotate,
    inventory_element_paths,
    load_bindings,
    load_inventory,
)
from rh_mod_skills.commands.extract import extract, extract_plan_path, inventory_path
from rh_mod_skills.commands.formalize import computable_dir, formalize, snapshot_path
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.specify import logical_model_path, specify
from rh_mod_skills.common import require_model, require_tracking, tracking_file


def _has_sources(entry: dict) -> bool:
    return bool(entry.get("sources"))


def _has_formalize(name: str) -> bool:
    if snapshot_path(name).is_file():
        return True
    return any(computable_dir(name).glob("StructureDefinition-*.json"))


def _coverage_line(name: str) -> str | None:
    if not inventory_path(name).is_file():
        return None
    inventory = load_inventory(name)
    try:
        bindings = load_bindings(name, validate=True)
    except click.ClickException:
        bindings = {"model": name, "bindings": []}
    mapped, vs_bound, unbound, undecided, _issues = _verify_counts(inventory, bindings)
    n = len(inventory_element_paths(name))
    return (
        f"coverage: inventory={n} mapped={mapped} vs_bound={vs_bound} "
        f"unbound={unbound} undecided={undecided}"
    )


def _run_stage(group, model: str) -> tuple[bool, str]:
    result = CliRunner().invoke(group, ["verify", model])
    return result.exit_code == 0, result.output or ""


def _echo_stage_output(text: str) -> None:
    for line in text.splitlines():
        click.echo(f"  {line}")


def _verify_one(entry: dict) -> int:
    """Print one model report. Return blocking count (0 = pass)."""
    name = entry.get("name") or ""
    click.echo(f"Model: {name}")
    coverage = _coverage_line(name)
    unbound = None
    if coverage:
        click.echo(coverage)
        parts = dict(p.split("=", 1) for p in coverage.split()[1:])
        unbound = parts.get("unbound")

    stages = [
        ("ingest", ingest, _has_sources(entry)),
        ("extract", extract, extract_plan_path(name).is_file()),
        ("annotate", annotate, inventory_path(name).is_file()),
        ("specify", specify, logical_model_path(name).is_file()),
        ("formalize", formalize, _has_formalize(name)),
    ]
    blocking = 0
    for label, group, applicable in stages:
        if not applicable:
            click.echo(f"{label}: skipped")
            continue
        ok, output = _run_stage(group, name)
        click.echo(f"{label}: {'pass' if ok else 'fail'}")
        _echo_stage_output(output)
        if not ok:
            blocking += 1

    advisory = ["validator=not-run"]
    if unbound is not None:
        advisory.insert(0, f"unbound={unbound}")
    click.echo("advisory: " + " ".join(advisory))
    return blocking


@click.command()
@click.argument("model", required=False)
def verify(model):
    """Consolidated non-destructive verify. Does not write tracking.yaml."""
    tracking = require_tracking()
    before = tracking_file().read_text(encoding="utf-8")
    models = tracking.get("models") or []
    blocking = 0

    if model:
        entry = require_model(tracking, model)
        blocking += _verify_one(entry)
    elif not models:
        click.echo("No models yet. Run `rh-mod-skills init <model>` to start one.")
        click.echo("Next: init")
    else:
        click.echo(f"Models: {len(models)}")
        for i, entry in enumerate(models):
            if i:
                click.echo("")
            blocking += _verify_one(entry)

    after = tracking_file().read_text(encoding="utf-8")
    if before != after:
        raise click.ClickException("verify mutated tracking.yaml — this is a bug")
    if blocking:
        raise click.ClickException(f"verify failed: {blocking} blocking model/stage issue(s)")
