"""rh-mod-skills init — Scaffold a new model workspace."""

import subprocess

import click

from rh_mod_skills.common import (
    append_model_event,
    append_root_event,
    assert_init_root_allowed,
    consumer_root,
    default_title,
    ensure_tracking,
    load_tracking,
    log_info,
    model_dir,
    now_iso,
    require_kebab_case,
    save_tracking,
    today_date,
    tracking_file,
)


def _default_author() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        name = result.stdout.strip()
        return name if name else "unknown"
    except Exception:
        return "unknown"


@click.command()
@click.argument("model")
@click.option("--title", default=None, help="Human-readable title")
@click.option("--description", default=None, help="Brief description")
@click.option("--author", default=None, help="Author name or team")
def init(model, title, description, author):
    """Scaffold a new model directory and register it in tracking.yaml."""
    require_kebab_case(model)
    root = consumer_root()
    assert_init_root_allowed(root)

    if not title:
        title = default_title(model)
    if not description:
        description = "A source data model"
    if not author:
        author = _default_author()

    md = model_dir(model)
    tf = tracking_file()

    if tf.exists():
        existing = load_tracking()
        names = [m.get("name") for m in existing.get("models", [])]
        if model in names:
            raise click.ClickException(f"Model '{model}' already exists at {md}")

    for subdir in ["sources", "structured", "computable", "process/plans"]:
        (md / subdir).mkdir(parents=True, exist_ok=True)

    timestamp = now_iso()
    today = today_date()

    ensure_tracking()
    tracking = load_tracking()
    tracking["models"].append(
        {
            "name": model,
            "title": title,
            "description": description,
            "author": author,
            "created_at": timestamp,
            "sources": [],
            "structured": [],
            "computable": [],
            "events": [],
        }
    )
    append_root_event(tracking, "model_created", "Model scaffolded with rh-mod-skills init")
    append_model_event(tracking, model, "created", "Model scaffolded with rh-mod-skills init")
    save_tracking(tracking)

    (md / "process" / "notes.md").write_text(
        f"""\
# Research Notes — {model}

## Open Questions

<!-- Questions to resolve before proceeding. Check off when resolved. -->
- [ ]

## Decisions

<!-- Key choices made and why. -->
-

## Source Conflicts

<!-- Contradictions between sources. Document and resolve. -->

## Notes

<!-- Free-form observations. -->
""",
        encoding="utf-8",
    )

    (md / "MODEL.md").write_text(
        f"""\
---
name: "{model}"
description: "{description}"
compatibility: "rh-mod-skills >= 0.1.0"
metadata:
  author: "{author}"
  created: "{today}"
---

## Overview

{description}

## Artifact levels

- **L1 (Sources)**: Codebooks and dictionaries under `sources/`
- **L2 (Structured)**: Inventory, bindings, specified logical model
- **L3 (Computable)**: FHIR logical `StructureDefinition` + ValueSets
""",
        encoding="utf-8",
    )

    log_info(f"Initialized model: {model}")
    click.echo(f"  Location: {md}")
    click.echo(f"  Tracking: {tf}")
    click.echo("  Structure:")
    click.echo(f"    models/{model}/")
    click.echo("      sources/      (L1 codebooks — empty until ingest)")
    click.echo("      structured/   (L2 YAML)")
    click.echo("      computable/   (L3 FHIR JSON)")
    click.echo("      process/plans/")
    click.echo("      MODEL.md")
