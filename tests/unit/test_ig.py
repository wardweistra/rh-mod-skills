"""Tests for rh-mod-skills ig sync."""

import json
from unittest.mock import patch

from click.testing import CliRunner

from rh_mod_skills.cli import main
from rh_mod_skills.commands.formalize import formalize
from rh_mod_skills.commands.ig import SCRIPT_NAMES, ig
from rh_mod_skills.commands.status import status
from test_formalize import _mini_extracted, _specified, load_yaml, save_yaml


def _formalized(tmp_consumer, name="spec-demo"):
    runner, name = _specified(tmp_consumer, typed=True, name=name)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code == 0, result.output
    return runner, name


def _stub_fetch(name: str) -> str:
    return f"# stub {name}\n"


def test_help_lists_ig():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ig" in result.output
    sub = CliRunner().invoke(main, ["ig", "--help"])
    assert "sync" in sub.output


def test_sync_requires_snapshot(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    with patch("rh_mod_skills.commands.ig.fetch_script", side_effect=_stub_fetch):
        result = runner.invoke(ig, ["sync", name])
    assert result.exit_code != 0
    assert "snapshot" in result.output.lower()
    assert not (tmp_consumer / "models" / name / "ig" / "ig.ini").exists()


@patch("rh_mod_skills.commands.ig.fetch_script", side_effect=_stub_fetch)
def test_sync_scaffolds_ig_tree(_fetch, tmp_consumer):
    runner, name = _formalized(tmp_consumer)
    result = runner.invoke(ig, ["sync", name])
    assert result.exit_code == 0, result.output
    root = tmp_consumer / "models" / name / "ig"
    assert (root / "ig.ini").is_file()
    assert "fhir.base.template" in (root / "ig.ini").read_text()
    for script in SCRIPT_NAMES:
        assert (root / script).is_file()
    sd = list((root / "input" / "models").glob("StructureDefinition-*.json"))
    vs = list((root / "input" / "vocabulary").glob("ValueSet-*.json"))
    igs = list((root / "input").glob("ImplementationGuide-*.json"))
    assert len(sd) == 1
    assert len(vs) == 0  # US1 mappings-only formalize emits no ValueSets
    assert len(igs) == 1
    ig_json = json.loads(igs[0].read_text(encoding="utf-8"))
    assert ig_json["resourceType"] == "ImplementationGuide"
    assert ig_json["fhirVersion"] == ["4.0.1"]
    refs = {e["reference"]["reference"] for e in ig_json["definition"]["resource"]}
    assert any(r.startswith("StructureDefinition/") for r in refs)
    assert not any(r.startswith("ValueSet/") for r in refs)
    page = ig_json["definition"]["page"]
    assert page["nameUrl"] == "index.html"
    assert page["generation"] == "markdown"
    assert "page" not in page
    assert (root / "input" / "includes" / "menu.xml").is_file()
    assert "index.html" in (root / "input" / "includes" / "menu.xml").read_text()
    assert "toc.html" in (root / "input" / "includes" / "menu.xml").read_text()
    index_md = root / "input" / "pagecontent" / "index.md"
    assert index_md.is_file()
    assert not (root / "publisher.jar").exists()
    assert not list(root.rglob("snapshot.yaml"))
    sidecar = load_yaml(root / "rh-mod.yaml")
    assert sidecar["package_id"]
    assert str(sidecar["url"]).startswith("http")
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    types = [e["type"] for e in tracking["models"][0]["events"]]
    assert "ig_synced" in types
    st = runner.invoke(status, [name])
    assert st.exit_code == 0, st.output
    assert "Next: verify" in st.output


@patch("rh_mod_skills.commands.ig.fetch_script", side_effect=_stub_fetch)
def test_sync_idempotent_keeps_reviewer_files_and_drops_stale(fetch_script, tmp_consumer):
    runner, name = _formalized(tmp_consumer)
    assert runner.invoke(ig, ["sync", name]).exit_code == 0
    fetch_script.reset_mock()
    root = tmp_consumer / "models" / name / "ig"
    ini = root / "ig.ini"
    ini.write_text(ini.read_text() + "# reviewer-template\n", encoding="utf-8")
    extra = root / "input" / "pagecontent" / "notes.md"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("keep me\n", encoding="utf-8")
    index_md = root / "input" / "pagecontent" / "index.md"
    index_md.write_text("# Reviewer home\n", encoding="utf-8")
    menu = root / "input" / "includes" / "menu.xml"
    menu.write_text(menu.read_text() + "<!-- reviewer -->\n", encoding="utf-8")
    vocab = root / "input" / "vocabulary"
    vocab.mkdir(parents=True, exist_ok=True)
    stale = vocab / "ValueSet-stale-demo.json"
    stale.write_text(
        json.dumps(
            {
                "resourceType": "ValueSet",
                "id": "stale-demo",
                "url": "https://example.org/fhir/ValueSet/stale-demo",
                "status": "draft",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    managed_path = root / "managed-files.yaml"
    managed = load_yaml(managed_path)
    managed["files"] = list(managed.get("files") or []) + [
        "input/vocabulary/ValueSet-stale-demo.json"
    ]
    save_yaml(managed_path, managed)
    result = runner.invoke(ig, ["sync", name])
    assert result.exit_code == 0, result.output
    assert fetch_script.call_count == 0
    assert "# reviewer-template" in ini.read_text()
    assert extra.read_text() == "keep me\n"
    assert index_md.read_text() == "# Reviewer home\n"
    assert "<!-- reviewer -->" in menu.read_text()
    assert not stale.is_file()
    ig_json = json.loads(next((root / "input").glob("ImplementationGuide-*.json")).read_text())
    refs = {e["reference"]["reference"] for e in ig_json["definition"]["resource"]}
    assert "ValueSet/stale-demo" not in refs
    page = ig_json["definition"]["page"]
    assert page["nameUrl"] == "index.html"
    assert "page" not in page
