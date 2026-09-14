"""Tests for rh-mod-skills status."""

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.status import status


def load_yaml(path):
    y = YAML()
    with open(path) as f:
        return y.load(f)


def test_status_missing_tracking(tmp_consumer):
    result = CliRunner().invoke(status, [])
    assert result.exit_code == 1
    assert "init" in result.output.lower()


def test_status_unknown_model(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast"])
    result = CliRunner().invoke(status, ["missing-model"])
    assert result.exit_code == 2
    assert "not found" in result.output


def test_status_single_model_after_init(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast", "--title", "NKR breast"])
    result = CliRunner().invoke(status, ["nkr-breast"])
    assert result.exit_code == 0, result.output
    assert "Model: nkr-breast" in result.output
    assert "Title: NKR breast" in result.output
    assert "Stage: initialized" in result.output
    assert "Sources: 0" in result.output
    assert "Next: ingest" in result.output
    assert "mapping" not in result.output.lower()
    assert "structuremap" not in result.output.lower()
    assert "fml" not in result.output.lower()


def test_status_list_two_models(tmp_consumer):
    runner = CliRunner()
    runner.invoke(init, ["nkr-breast"])
    runner.invoke(init, ["encr-standard-dataset"])
    result = runner.invoke(status, [])
    assert result.exit_code == 0, result.output
    assert "nkr-breast" in result.output
    assert "encr-standard-dataset" in result.output
    assert "next:ingest" in result.output.replace(" ", "")


def test_status_does_not_write_tracking(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast"])
    before = (tmp_consumer / "tracking.yaml").read_text()
    CliRunner().invoke(status, ["nkr-breast"])
    CliRunner().invoke(main, ["status"])
    after = (tmp_consumer / "tracking.yaml").read_text()
    assert before == after


def test_status_empty_models_message(tmp_consumer):
    y = YAML()
    y.default_flow_style = False
    with open(tmp_consumer / "tracking.yaml", "w") as f:
        y.dump({"schema_version": "1.0", "models": [], "events": []}, f)
    result = CliRunner().invoke(status, [])
    assert result.exit_code == 0
    assert "No models yet" in result.output


def test_status_partial_bindings_next_annotate(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast"])
    inv = tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml"
    y = YAML()
    y.default_flow_style = False
    with open(inv, "w", encoding="utf-8") as f:
        y.dump(
            {
                "model": "nkr-breast",
                "entities": [
                    {
                        "id": "patientgegevens",
                        "title": "P",
                        "elements": [
                            {"id": "gesl", "display": "Geslacht", "path": "patientgegevens.gesl"},
                            {
                                "id": "gebdat",
                                "display": "Geboortedatum",
                                "path": "patientgegevens.gebdat",
                            },
                        ],
                    }
                ],
            },
            f,
        )
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    tracking["models"][0]["events"].append(
        {
            "timestamp": "2026-09-14T00:00:00Z",
            "type": "annotate_planned",
            "description": "test",
        }
    )
    with open(tmp_consumer / "tracking.yaml", "w", encoding="utf-8") as f:
        y.dump(tracking, f)
    with open(
        tmp_consumer / "models" / "nkr-breast" / "structured" / "bindings.yaml",
        "w",
        encoding="utf-8",
    ) as f:
        y.dump(
            {
                "model": "nkr-breast",
                "bindings": [
                    {
                        "path": "patientgegevens.gesl",
                        "status": "bound",
                        "decision": "accept",
                    }
                ],
            },
            f,
        )
    result = CliRunner().invoke(status, ["nkr-breast"])
    assert result.exit_code == 0, result.output
    assert "Stage: annotating" in result.output
    assert "Next: annotate" in result.output


def test_status_all_decided_next_specify(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast"])
    inv = tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml"
    y = YAML()
    y.default_flow_style = False
    with open(inv, "w", encoding="utf-8") as f:
        y.dump(
            {
                "model": "nkr-breast",
                "entities": [
                    {
                        "id": "patientgegevens",
                        "title": "P",
                        "elements": [
                            {"id": "gesl", "display": "Geslacht", "path": "patientgegevens.gesl"},
                        ],
                    }
                ],
            },
            f,
        )
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    tracking["models"][0]["events"].append(
        {
            "timestamp": "2026-09-14T00:00:00Z",
            "type": "element_bound",
            "description": "test",
        }
    )
    with open(tmp_consumer / "tracking.yaml", "w", encoding="utf-8") as f:
        y.dump(tracking, f)
    with open(
        tmp_consumer / "models" / "nkr-breast" / "structured" / "bindings.yaml",
        "w",
        encoding="utf-8",
    ) as f:
        y.dump(
            {
                "model": "nkr-breast",
                "bindings": [
                    {
                        "path": "patientgegevens.gesl",
                        "status": "bound",
                        "decision": "accept",
                    }
                ],
            },
            f,
        )
    result = CliRunner().invoke(status, ["nkr-breast"])
    assert result.exit_code == 0, result.output
    assert "Stage: annotating" in result.output
    assert "Next: specify" in result.output
