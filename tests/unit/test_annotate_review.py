"""Tests for annotate export / import (008)."""

from pathlib import Path

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.annotate import annotate
from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "l1"
IKNL = FIXTURES / "nkr-breast" / "IKNL_Data_dictionary.xlsx"

GESL_PATH = "patientgegevens.gesl"
BIO_SEX = "http://snomed.info/sct|734000001|Biological sex"
GENDER = "http://snomed.info/sct|263495000|Gender"
GENDER_ID = "http://snomed.info/sct|33821000087103|Gender identity"
SNOMED = "http://snomed.info/sct"


def load_yaml(path):
    y = YAML()
    with open(path) as f:
        return y.load(f)


def _init(name="nkr-breast"):
    result = CliRunner().invoke(init, [name])
    assert result.exit_code == 0, result.output


def _extract_nkr():
    runner = CliRunner()
    _init()
    runner.invoke(ingest, ["plan", "nkr-breast", "--source", str(IKNL)])
    runner.invoke(ingest, ["approve", "nkr-breast"])
    assert runner.invoke(ingest, ["implement", "nkr-breast"]).exit_code == 0
    runner.invoke(extract, ["plan", "nkr-breast"])
    runner.invoke(extract, ["approve", "nkr-breast"])
    result = runner.invoke(extract, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    return runner


def _plan_path(root, model="nkr-breast"):
    return root / "models" / model / "process" / "plans" / "annotate-plan.yaml"


def _bindings_path(root, model="nkr-breast"):
    return root / "models" / model / "structured" / "bindings.yaml"


def _model_event_types(root, model="nkr-breast"):
    tracking = load_yaml(root / "tracking.yaml")
    for entry in tracking["models"]:
        if entry["name"] == model:
            return [e["type"] for e in entry.get("events") or []]
    return []


def _enrich(runner, element="gesl", model="nkr-breast", candidates=None, query=None):
    args = ["enrich", model, "--element", element]
    if candidates:
        for c in candidates:
            args.extend(["--candidate", c])
    if query:
        args.extend(["--lookup-query", query])
    result = runner.invoke(annotate, args)
    assert result.exit_code == 0, result.output
    return result

GESL_PATH = "patientgegevens.gesl"
BIO_SEX = "http://snomed.info/sct|734000001|Biological sex"
GENDER = "http://snomed.info/sct|263495000|Gender"
GENDER_ID = "http://snomed.info/sct|33821000087103|Gender identity"
SNOMED = "http://snomed.info/sct"


def _review_path(root, model="nkr-breast"):
    return root / "models" / model / "process" / "plans" / "annotate-review.html"


def _write_picks(path: Path, rows: list, model="nkr-breast"):
    y = YAML()
    y.default_flow_style = False
    with open(path, "w", encoding="utf-8") as f:
        y.dump({"model": model, "picks": rows}, f)


def _plan_gesl(runner, *candidates):
    result = runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    assert result.exit_code == 0, result.output
    if candidates:
        _enrich(runner, candidates=list(candidates))


def _import(runner, picks_path):
    return runner.invoke(annotate, ["import", "nkr-breast", "--from", str(picks_path)])


def test_help_lists_export_import():
    result = CliRunner().invoke(main, ["annotate", "--help"])
    assert result.exit_code == 0
    assert "export" in result.output
    assert "import" in result.output


def test_export_writes_html_with_candidates(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    tracking_before = (tmp_consumer / "tracking.yaml").read_text()
    assert not _bindings_path(tmp_consumer).exists()
    result = runner.invoke(annotate, ["export", "nkr-breast"])
    assert result.exit_code == 0, result.output
    html = _review_path(tmp_consumer).read_text(encoding="utf-8")
    assert GESL_PATH in html
    assert "Geslacht" in html
    assert "Biological sex" in html
    assert "734000001" in html
    assert "Gender" in html
    assert "263495000" in html
    assert "Gender identity" in html
    assert "33821000087103" in html
    assert html.find("734000001") < html.find("263495000") < html.find("33821000087103")
    assert "Unbound" in html
    assert "Skip" in html
    assert not _bindings_path(tmp_consumer).exists()
    assert (tmp_consumer / "tracking.yaml").read_text() == tracking_before
    assert "element_bound" not in _model_event_types(tmp_consumer)


def test_export_fails_without_plan(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(annotate, ["export", "nkr-breast"])
    assert result.exit_code != 0
    assert "No annotate plan" in result.output
    assert not _review_path(tmp_consumer).exists()


def test_export_empty_candidates_still_lists_unbound_skip(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner)
    result = runner.invoke(annotate, ["export", "nkr-breast"])
    assert result.exit_code == 0, result.output
    html = _review_path(tmp_consumer).read_text(encoding="utf-8")
    assert GESL_PATH in html
    assert "Unbound" in html
    assert "Skip" in html
    assert "Rank 1" not in html


def test_import_accept_pick_1(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 1, "reason": ""}],
    )
    tracking_before = (tmp_consumer / "tracking.yaml").read_text()
    result = _import(runner, picks)
    assert result.exit_code == 0, result.output
    plan = load_yaml(_plan_path(tmp_consumer))
    assert plan["status"] == "draft"
    el = plan["elements"][0]
    assert el["decision"] == "accept"
    assert el["chosen"]["code"] == "734000001"
    assert el["chosen"]["display"] == "Biological sex"
    assert el["chosen"]["system"] == SNOMED
    assert [c["code"] for c in el["candidates"]] == [
        "734000001",
        "263495000",
        "33821000087103",
    ]
    assert not _bindings_path(tmp_consumer).exists()
    assert (tmp_consumer / "tracking.yaml").read_text() == tracking_before
    assert "element_bound" not in _model_event_types(tmp_consumer)


def test_import_accept_pick_2_not_rank_1(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 2, "reason": ""}],
    )
    result = _import(runner, picks)
    assert result.exit_code == 0, result.output
    el = load_yaml(_plan_path(tmp_consumer))["elements"][0]
    assert el["decision"] == "accept"
    assert el["chosen"]["code"] == "263495000"
    assert el["chosen"]["display"] == "Gender"
    assert [c["code"] for c in el["candidates"]] == [
        "734000001",
        "263495000",
        "33821000087103",
    ]


def test_import_then_implement_without_approve_fails(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 1, "reason": ""}],
    )
    assert _import(runner, picks).exit_code == 0
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code != 0
    assert "not approved" in result.output
    assert not _bindings_path(tmp_consumer).exists()


def test_import_unknown_path_fails_closed(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX)
    before = _plan_path(tmp_consumer).read_text(encoding="utf-8")
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": "patientgegevens.gebdat", "decision": "unbound", "reason": "n/a"}],
    )
    result = _import(runner, picks)
    assert result.exit_code != 0
    assert "patientgegevens.gebdat" in result.output
    assert _plan_path(tmp_consumer).read_text(encoding="utf-8") == before
    assert not _bindings_path(tmp_consumer).exists()


def test_import_unbound_skip_replace(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(
        annotate,
        ["plan", "nkr-breast", "--element", "gesl", "--element", "gebdat", "--element", "incdat"],
    )
    assert result.exit_code == 0, result.output
    _enrich(runner, element="gesl", candidates=[BIO_SEX])
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [
            {
                "path": "patientgegevens.gebdat",
                "decision": "unbound",
                "reason": "identifier / no terminology needed",
            },
            {"path": "patientgegevens.incdat", "decision": "reject"},
            {
                "path": GESL_PATH,
                "decision": "replace",
                "chosen": {
                    "system": SNOMED,
                    "code": "407376001",
                    "display": "Male",
                },
            },
        ],
    )
    result = _import(runner, picks)
    assert result.exit_code == 0, result.output
    by_id = {el["id"]: el for el in load_yaml(_plan_path(tmp_consumer))["elements"]}
    assert by_id["gebdat"]["decision"] == "unbound"
    assert by_id["gebdat"]["reason"] == "identifier / no terminology needed"
    assert by_id["gebdat"]["chosen"]["code"] is None
    assert by_id["incdat"]["decision"] == "reject"
    assert by_id["gesl"]["decision"] == "replace"
    assert by_id["gesl"]["chosen"]["code"] == "407376001"
    assert by_id["gesl"]["chosen"]["display"] == "Male"
    assert not _bindings_path(tmp_consumer).exists()


def test_import_skip_alias_is_reject(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX)
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(picks, [{"path": GESL_PATH, "decision": "skip"}])
    result = _import(runner, picks)
    assert result.exit_code == 0, result.output
    assert load_yaml(_plan_path(tmp_consumer))["elements"][0]["decision"] == "reject"


def test_import_resets_approved_to_draft(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    assert runner.invoke(annotate, ["approve", "nkr-breast"]).exit_code == 0
    assert load_yaml(_plan_path(tmp_consumer))["status"] == "approved"
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 1, "reason": ""}],
    )
    result = _import(runner, picks)
    assert result.exit_code == 0, result.output
    plan = load_yaml(_plan_path(tmp_consumer))
    assert plan["status"] == "draft"
    assert plan["elements"][0]["chosen"]["code"] == "734000001"
    impl = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert impl.exit_code != 0
    assert not _bindings_path(tmp_consumer).exists()


def test_import_unbound_without_reason_fails(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner)
    before = _plan_path(tmp_consumer).read_text(encoding="utf-8")
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(picks, [{"path": GESL_PATH, "decision": "unbound", "reason": ""}])
    result = _import(runner, picks)
    assert result.exit_code != 0
    assert "unbound" in result.output.lower()
    assert _plan_path(tmp_consumer).read_text(encoding="utf-8") == before


def test_import_model_mismatch_fails(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX)
    before = _plan_path(tmp_consumer).read_text(encoding="utf-8")
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 1}],
        model="other-model",
    )
    result = _import(runner, picks)
    assert result.exit_code != 0
    assert "other-model" in result.output
    assert _plan_path(tmp_consumer).read_text(encoding="utf-8") == before


def test_import_invalid_pick_fails(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX)
    before = _plan_path(tmp_consumer).read_text(encoding="utf-8")
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(picks, [{"path": GESL_PATH, "decision": "accept", "pick": 9}])
    result = _import(runner, picks)
    assert result.exit_code != 0
    assert "pick 9" in result.output
    assert _plan_path(tmp_consumer).read_text(encoding="utf-8") == before


def test_export_after_import_checks_previous_pick(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 2, "reason": ""}],
    )
    assert _import(runner, picks).exit_code == 0
    result = runner.invoke(annotate, ["export", "nkr-breast"])
    assert result.exit_code == 0, result.output
    html = _review_path(tmp_consumer).read_text(encoding="utf-8")
    assert 'value="2" checked' in html
    assert 'value="1" checked' not in html


def test_import_then_approve_implement_binds_picked_code(tmp_consumer):
    runner = _extract_nkr()
    _plan_gesl(runner, BIO_SEX, GENDER, GENDER_ID)
    picks = tmp_consumer / "annotate-picks.yaml"
    _write_picks(
        picks,
        [{"path": GESL_PATH, "decision": "accept", "pick": 1, "reason": ""}],
    )
    assert _import(runner, picks).exit_code == 0
    assert not _bindings_path(tmp_consumer).exists()
    assert runner.invoke(annotate, ["approve", "nkr-breast"]).exit_code == 0
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    row = load_yaml(_bindings_path(tmp_consumer))["bindings"][0]
    assert row["code"] == "734000001"
    assert row["display_term"] == "Biological sex"
    assert row["decision"] == "accept"
