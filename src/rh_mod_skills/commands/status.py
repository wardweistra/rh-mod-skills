"""rh-mod-skills status — Read-only model lifecycle report."""

import click

from rh_mod_skills.commands.annotate import decided_binding_paths, inventory_element_paths
from rh_mod_skills.common import require_model, require_tracking


def _source_count(model: dict) -> int:
    return len(model.get("sources") or [])


def _event_types(model: dict) -> set[str]:
    return {e.get("type") for e in model.get("events") or []}


def compute_stage(model: dict) -> str:
    """Derive stage from tracking events and artifact lists."""
    types = _event_types(model)
    if "model_formalized" in types or model.get("computable"):
        return "formalized"
    if "model_specified" in types:
        return "specified"
    if "element_bound" in types or "annotate_planned" in types:
        return "annotating"
    if "inventory_derived" in types:
        return "extracted"
    if "source_added" in types or _source_count(model) > 0:
        return "ingested"
    return "initialized"


def next_step(stage: str) -> str:
    return {
        "initialized": "ingest",
        "ingested": "extract",
        "extracted": "annotate",
        "annotating": "annotate",
        "specified": "formalize",
        "formalized": "verify",
    }.get(stage, "ingest")


def next_step_for_model(model: dict) -> str:
    """Next is annotate until every inventory path is bound or unbound."""
    stage = compute_stage(model)
    if stage in ("extracted", "annotating"):
        name = model.get("name") or ""
        inv = inventory_element_paths(name)
        if inv and set(inv) <= decided_binding_paths(name):
            return "specify"
        return "annotate"
    return next_step(stage)


def _render_model(model: dict) -> None:
    name = model.get("name", "")
    title = model.get("title", "")
    stage = compute_stage(model)
    nxt = next_step_for_model(model)
    click.echo(f"Model: {name}")
    if title:
        click.echo(f"Title: {title}")
    click.echo(f"Stage: {stage}")
    click.echo(f"Sources: {_source_count(model)}")
    click.echo(f"Next: {nxt}")


@click.command()
@click.argument("model", required=False)
def status(model):
    """Show workflow state of a model. Read-only — does not write tracking.yaml."""
    tracking = require_tracking()
    models = tracking.get("models") or []

    if model:
        entry = require_model(tracking, model)
        _render_model(entry)
        return

    if not models:
        click.echo("No models yet. Run `rh-mod-skills init <model>` to start one.")
        click.echo("Next: init")
        return

    click.echo(f"Models: {len(models)}")
    click.echo("")
    for entry in models:
        name = entry.get("name", "")
        stage = compute_stage(entry)
        nxt = next_step_for_model(entry)
        click.echo(f"{name}\t{stage}\tnext:{nxt}")
