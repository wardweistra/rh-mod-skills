"""Tests for rh-mod-skills annotate."""

from pathlib import Path

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.annotate import annotate
from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.status import status

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "l1"
IKNL = FIXTURES / "nkr-breast" / "IKNL_Data_dictionary.xlsx"
ENCR = FIXTURES / "encr-standard-dataset" / "ENCR-Recommendation-standard-dataset_Mar2023.pdf"

GESL_CANDIDATE = "http://snomed.info/sct|263495000|Gender"
GESL_CODE = "263495000"
GESL_SYSTEM = "http://snomed.info/sct"
SEX_CANDIDATE = "http://snomed.info/sct|184100006|Patient sex"


def load_yaml(path):
    y = YAML()
    with open(path) as f:
        return y.load(f)


def save_yaml(path, data):
    y = YAML()
    y.default_flow_style = False
    with open(path, "w", encoding="utf-8") as f:
        y.dump(data, f)


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


def _extract_encr():
    runner = CliRunner()
    _init("encr-standard-dataset")
    runner.invoke(ingest, ["plan", "encr-standard-dataset", "--source", str(ENCR)])
    runner.invoke(ingest, ["approve", "encr-standard-dataset"])
    assert runner.invoke(ingest, ["implement", "encr-standard-dataset"]).exit_code == 0
    runner.invoke(extract, ["plan", "encr-standard-dataset"])
    runner.invoke(extract, ["approve", "encr-standard-dataset"])
    result = runner.invoke(extract, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 0, result.output
    return runner


def _plan_path(root, model="nkr-breast"):
    return root / "models" / model / "process" / "plans" / "annotate-plan.yaml"


def _bindings_path(root, model="nkr-breast"):
    return root / "models" / model / "structured" / "bindings.yaml"


def _inventory_path(root, model="nkr-breast"):
    return root / "models" / model / "structured" / "inventory.yaml"


def _set_decisions(plan_path, updates: dict):
    plan = load_yaml(plan_path)
    for el in plan["elements"]:
        patch = updates.get(el["id"]) or updates.get(el["path"])
        if patch:
            el.update(patch)
    save_yaml(plan_path, plan)


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


def test_help_lists_annotate():
    result = CliRunner().invoke(main, ["annotate", "--help"])
    assert result.exit_code == 0
    assert "plan" in result.output
    assert "enrich" in result.output
    assert "implement" in result.output
    assert "verify" in result.output


def test_plan_requires_element_or_all(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(annotate, ["plan", "nkr-breast"])
    assert result.exit_code != 0
    assert "--element" in result.output
    assert not _plan_path(tmp_consumer).exists()


def test_plan_rejects_both_flags(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(
        annotate,
        ["plan", "nkr-breast", "--element", "gesl", "--all-undecided"],
    )
    assert result.exit_code != 0
    assert "not both" in result.output.lower() or "--all-undecided" in result.output


def test_plan_gesl_empty_candidates(tmp_consumer):
    runner = _extract_nkr()
    before_inv = _inventory_path(tmp_consumer).read_text()
    result = runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    assert result.exit_code == 0, result.output
    plan = load_yaml(_plan_path(tmp_consumer))
    assert plan["status"] == "draft"
    assert plan["systems"] == ["snomed"]
    assert len(plan["elements"]) == 1
    el = plan["elements"][0]
    assert el["id"] == "gesl"
    assert el["path"] == "patientgegevens.gesl"
    assert el["query"] == "Geslacht"
    assert el["decision"] == "pending"
    assert el["strength"] == "example"
    assert el["candidates"] == []
    assert _inventory_path(tmp_consumer).read_text() == before_inv
    assert "annotate_planned" in _model_event_types(tmp_consumer)


def test_enrich_records_mcp_candidates(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    result = _enrich(
        runner,
        candidates=[GESL_CANDIDATE, "http://snomed.info/sct|365873007|Gender finding"],
        query="sex",
    )
    assert "2 candidate" in result.output
    el = load_yaml(_plan_path(tmp_consumer))["elements"][0]
    assert el["query"] == "sex"
    assert len(el["candidates"]) == 2
    assert el["candidates"][0]["code"] == GESL_CODE
    assert el["candidates"][0]["rank"] == 1
    assert el["candidates"][0]["system"] == GESL_SYSTEM


def test_enrich_caps_at_five(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    extras = [f"http://snomed.info/sct|{i}|Hit {i}" for i in range(6)]
    result = runner.invoke(
        annotate,
        ["enrich", "nkr-breast", "--element", "gesl", *[a for c in extras for a in ("--candidate", c)]],
    )
    assert result.exit_code == 0, result.output
    assert "WARN" in result.output
    el = load_yaml(_plan_path(tmp_consumer))["elements"][0]
    assert len(el["candidates"]) == 5


def test_enrich_fails_when_approved(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    runner.invoke(annotate, ["approve", "nkr-breast"])
    result = runner.invoke(
        annotate, ["enrich", "nkr-breast", "--element", "gesl", "--candidate", GESL_CANDIDATE]
    )
    assert result.exit_code == 1
    assert "approved" in result.output


def test_implement_fails_without_approval(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 1
    assert "not approved" in result.output
    assert not _bindings_path(tmp_consumer).exists()
    assert "element_bound" not in _model_event_types(tmp_consumer)


def test_accept_gesl_only(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _enrich(runner, candidates=[GESL_CANDIDATE])
    _set_decisions(_plan_path(tmp_consumer), {"gesl": {"decision": "accept"}})
    assert runner.invoke(annotate, ["approve", "nkr-breast"]).exit_code == 0
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    bindings = load_yaml(_bindings_path(tmp_consumer))
    assert len(bindings["bindings"]) == 1
    row = bindings["bindings"][0]
    assert row["path"] == "patientgegevens.gesl"
    assert row["status"] == "bound"
    assert row["decision"] == "accept"
    assert row["strength"] == "example"
    assert row["code"] == GESL_CODE
    assert row["system"] == GESL_SYSTEM
    logical = tmp_consumer / "models" / "nkr-breast" / "structured" / "logical-model.yaml"
    assert not logical.exists()
    assert not list((tmp_consumer / "models" / "nkr-breast" / "computable").glob("*"))
    types = _model_event_types(tmp_consumer)
    assert "annotate_planned" in types
    assert "element_bound" in types
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    assert "bindings.yaml" in tracking["models"][0]["structured"]
    st = runner.invoke(status, ["nkr-breast"])
    assert "Stage: annotating" in st.output
    assert "Next: annotate" in st.output
    verify = runner.invoke(annotate, ["verify", "nkr-breast"])
    assert verify.exit_code == 0, verify.output
    assert "bound=1" in verify.output
    assert "unbound=0" in verify.output
    assert "undecided=152" in verify.output


def test_unbound_replace_and_skip(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(
        annotate,
        ["plan", "nkr-breast", "--element", "gesl", "--element", "gebdat"],
    )
    assert result.exit_code == 0, result.output
    _set_decisions(
        _plan_path(tmp_consumer),
        {
            "gesl": {
                "decision": "replace",
                "chosen": {
                    "system": "http://snomed.info/sct",
                    "code": "407376001",
                    "display": "Male",
                },
            },
            "gebdat": {
                "decision": "unbound",
                "reason": "identifier / no terminology needed",
            },
        },
    )
    runner.invoke(annotate, ["approve", "nkr-breast"])
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    rows = {b["path"]: b for b in load_yaml(_bindings_path(tmp_consumer))["bindings"]}
    assert rows["patientgegevens.gesl"]["code"] == "407376001"
    assert rows["patientgegevens.gesl"]["display_term"] == "Male"
    assert rows["patientgegevens.gesl"]["decision"] == "replace"
    assert rows["patientgegevens.gebdat"]["status"] == "unbound"
    assert rows["patientgegevens.gebdat"]["reason"] == "identifier / no terminology needed"
    assert "263495000" not in rows["patientgegevens.gesl"]["code"]
    verify = runner.invoke(annotate, ["verify", "nkr-breast"])
    assert verify.exit_code == 0, verify.output
    assert "unbound=1" in verify.output
    assert "bound=1" in verify.output


def test_reject_and_pending_not_written(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(
        annotate,
        ["plan", "nkr-breast", "--element", "gesl", "--element", "incdat"],
    )
    _set_decisions(
        _plan_path(tmp_consumer),
        {"gesl": {"decision": "reject"}, "incdat": {"decision": "pending"}},
    )
    runner.invoke(annotate, ["approve", "nkr-breast"])
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    bindings = load_yaml(_bindings_path(tmp_consumer))
    assert bindings["bindings"] == []
    verify = runner.invoke(annotate, ["verify", "nkr-breast"])
    assert "undecided=153" in verify.output


def test_accept_empty_candidates_fails(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _set_decisions(_plan_path(tmp_consumer), {"gesl": {"decision": "accept"}})
    runner.invoke(annotate, ["approve", "nkr-breast"])
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 1
    assert "no candidates" in result.output
    assert not _bindings_path(tmp_consumer).exists()


def test_plan_does_not_require_reasonhub_env(tmp_consumer, monkeypatch):
    monkeypatch.delenv("RH_REASONHUB_URL", raising=False)
    monkeypatch.delenv("RH_REASONHUB_TOKEN", raising=False)
    runner = _extract_nkr()
    result = runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    assert result.exit_code == 0, result.output
    assert load_yaml(_plan_path(tmp_consumer))["elements"][0]["candidates"] == []


def test_enrich_zero_hits(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    result = runner.invoke(annotate, ["enrich", "nkr-breast", "--element", "gesl"])
    assert result.exit_code == 0, result.output
    assert load_yaml(_plan_path(tmp_consumer))["elements"][0]["candidates"] == []


def test_verify_idempotent(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _enrich(runner, candidates=[GESL_CANDIDATE])
    _set_decisions(_plan_path(tmp_consumer), {"gesl": {"decision": "accept"}})
    runner.invoke(annotate, ["approve", "nkr-breast"])
    runner.invoke(annotate, ["implement", "nkr-breast"])
    before = (tmp_consumer / "tracking.yaml").read_text()
    v1 = runner.invoke(annotate, ["verify", "nkr-breast"])
    v2 = runner.invoke(annotate, ["verify", "nkr-breast"])
    assert v1.exit_code == 0, v1.output
    assert v2.exit_code == 0, v2.output
    assert "bound=1" in v1.output and "bound=1" in v2.output
    assert "undecided=152" in v1.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before


def test_merge_by_path_and_replace_flag(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _enrich(runner, candidates=[GESL_CANDIDATE])
    _set_decisions(_plan_path(tmp_consumer), {"gesl": {"decision": "accept"}})
    runner.invoke(annotate, ["approve", "nkr-breast"])
    runner.invoke(annotate, ["implement", "nkr-breast"])

    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gebdat"])
    _set_decisions(
        _plan_path(tmp_consumer),
        {"gebdat": {"decision": "unbound", "reason": "identifier / no terminology needed"}},
    )
    runner.invoke(annotate, ["approve", "nkr-breast"])
    runner.invoke(annotate, ["implement", "nkr-breast"])
    rows = {b["path"]: b for b in load_yaml(_bindings_path(tmp_consumer))["bindings"]}
    assert "patientgegevens.gesl" in rows
    assert rows["patientgegevens.gebdat"]["status"] == "unbound"

    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _set_decisions(
        _plan_path(tmp_consumer),
        {
            "gesl": {
                "decision": "replace",
                "chosen": {
                    "system": "http://snomed.info/sct",
                    "code": "407376001",
                    "display": "Male",
                },
            }
        },
    )
    runner.invoke(annotate, ["approve", "nkr-breast"])
    runner.invoke(annotate, ["implement", "nkr-breast"])
    rows = {b["path"]: b for b in load_yaml(_bindings_path(tmp_consumer))["bindings"]}
    assert rows["patientgegevens.gesl"]["code"] == "407376001"
    assert rows["patientgegevens.gebdat"]["status"] == "unbound"

    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _enrich(runner, candidates=[GESL_CANDIDATE])
    _set_decisions(_plan_path(tmp_consumer), {"gesl": {"decision": "accept"}})
    runner.invoke(annotate, ["approve", "nkr-breast"])
    result = runner.invoke(annotate, ["implement", "nkr-breast", "--replace"])
    assert result.exit_code == 0, result.output
    bindings = load_yaml(_bindings_path(tmp_consumer))
    assert [b["path"] for b in bindings["bindings"]] == ["patientgegevens.gesl"]


def test_pending_does_not_delete_existing(tmp_consumer):
    runner = _extract_nkr()
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    _enrich(runner, candidates=[GESL_CANDIDATE])
    _set_decisions(_plan_path(tmp_consumer), {"gesl": {"decision": "accept"}})
    runner.invoke(annotate, ["approve", "nkr-breast"])
    runner.invoke(annotate, ["implement", "nkr-breast"])
    runner.invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    runner.invoke(annotate, ["approve", "nkr-breast"])
    result = runner.invoke(annotate, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    rows = load_yaml(_bindings_path(tmp_consumer))["bindings"]
    assert len(rows) == 1
    assert rows[0]["path"] == "patientgegevens.gesl"
    assert rows[0]["status"] == "bound"


def test_no_inventory_guides_extract(tmp_consumer):
    _init()
    result = CliRunner().invoke(annotate, ["plan", "nkr-breast", "--element", "gesl"])
    assert result.exit_code == 1
    assert "extract" in result.output.lower()


def test_all_undecided_warns(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(annotate, ["plan", "nkr-breast", "--all-undecided"])
    assert result.exit_code == 0, result.output
    assert "WARN" in result.output
    plan = load_yaml(_plan_path(tmp_consumer))
    assert len(plan["elements"]) == 153
    assert all(el["candidates"] == [] for el in plan["elements"])


def test_system_loinc_recorded(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(
        annotate, ["plan", "nkr-breast", "--element", "gesl", "--system", "loinc"]
    )
    assert result.exit_code == 0, result.output
    plan = load_yaml(_plan_path(tmp_consumer))
    assert plan["systems"] == ["loinc"]


def test_unknown_element_fails(tmp_consumer):
    runner = _extract_nkr()
    result = runner.invoke(annotate, ["plan", "nkr-breast", "--element", "not-a-thing"])
    assert result.exit_code == 1
    assert "Unknown element" in result.output


def test_homonym_id_requires_path(tmp_consumer):
    _init("two-sheet")
    csv_a = tmp_consumer / "sheet-a.csv"
    csv_b = tmp_consumer / "sheet-b.csv"
    csv_a.write_text("name,label\nstatus,Alpha status\n", encoding="utf-8")
    csv_b.write_text("name,label\nstatus,Beta status\n", encoding="utf-8")
    runner = CliRunner()
    runner.invoke(
        ingest,
        ["plan", "two-sheet", "--source", str(csv_a), "--source", str(csv_b)],
    )
    runner.invoke(ingest, ["approve", "two-sheet"])
    assert runner.invoke(ingest, ["implement", "two-sheet"]).exit_code == 0
    runner.invoke(extract, ["plan", "two-sheet"])
    runner.invoke(extract, ["approve", "two-sheet"])
    assert runner.invoke(extract, ["implement", "two-sheet"]).exit_code == 0
    result = runner.invoke(annotate, ["plan", "two-sheet", "--element", "status"])
    assert result.exit_code == 1
    assert "not unique" in result.output
    result = runner.invoke(
        annotate, ["plan", "two-sheet", "--element", "sheet-a.status"]
    )
    assert result.exit_code == 0, result.output
    plan = load_yaml(_plan_path(tmp_consumer, "two-sheet"))
    assert plan["elements"][0]["path"] == "sheet-a.status"


def test_encr_one_table1_element(tmp_consumer):
    runner = _extract_encr()
    before = _inventory_path(tmp_consumer, "encr-standard-dataset").read_text()
    result = runner.invoke(
        annotate, ["plan", "encr-standard-dataset", "--element", "sex-at-birth"]
    )
    assert result.exit_code == 0, result.output
    plan = load_yaml(_plan_path(tmp_consumer, "encr-standard-dataset"))
    assert plan["elements"][0]["path"] == "table-1.sex-at-birth"
    _enrich(
        runner,
        element="sex-at-birth",
        model="encr-standard-dataset",
        candidates=[SEX_CANDIDATE],
    )
    _set_decisions(
        _plan_path(tmp_consumer, "encr-standard-dataset"),
        {"sex-at-birth": {"decision": "accept"}},
    )
    runner.invoke(annotate, ["approve", "encr-standard-dataset"])
    result = runner.invoke(annotate, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 0, result.output
    bindings = load_yaml(_bindings_path(tmp_consumer, "encr-standard-dataset"))
    assert len(bindings["bindings"]) == 1
    assert bindings["bindings"][0]["path"] == "table-1.sex-at-birth"
    assert _inventory_path(tmp_consumer, "encr-standard-dataset").read_text() == before
    verify = runner.invoke(annotate, ["verify", "encr-standard-dataset"])
    assert verify.exit_code == 0, verify.output
    assert "bound=1" in verify.output
    assert "undecided=24" in verify.output
    st = runner.invoke(status, ["encr-standard-dataset"])
    assert "Next: annotate" in st.output
