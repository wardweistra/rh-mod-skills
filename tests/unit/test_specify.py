"""Tests for rh-mod-skills specify."""

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.annotate import annotate
from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.specify import specify
from rh_mod_skills.commands.status import status

SEX_CANDIDATE = "http://loinc.org|76689-9|Sex assigned at birth"


def load_yaml(path):
    y = YAML()
    with open(path) as f:
        return y.load(f)


def save_yaml(path, data):
    y = YAML()
    y.default_flow_style = False
    with open(path, "w", encoding="utf-8") as f:
        y.dump(data, f)


def _set_annotate_decisions(plan_path, updates: dict):
    plan = load_yaml(plan_path)
    for el in plan["elements"]:
        patch = updates.get(el["id"]) or updates.get(el["path"])
        if patch:
            el.update(patch)
    save_yaml(plan_path, plan)


def _mini_extracted(tmp_consumer, name="spec-demo"):
    csv_path = tmp_consumer / "mini.csv"
    csv_path.write_text(
        "name,label,datatype\n"
        "sex,Sex at birth,code\n"
        "dob,Date of birth,F\n"
        "pid,Personal identifier,A\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    assert runner.invoke(init, [name]).exit_code == 0
    runner.invoke(ingest, ["plan", name, "--source", str(csv_path)])
    runner.invoke(ingest, ["approve", name])
    assert runner.invoke(ingest, ["implement", name]).exit_code == 0
    runner.invoke(extract, ["plan", name])
    runner.invoke(extract, ["approve", name])
    assert runner.invoke(extract, ["implement", name]).exit_code == 0, "extract implement"
    return runner, name


def _annotate_complete(runner, tmp_consumer, name="spec-demo"):
    result = runner.invoke(annotate, ["plan", name, "--all-undecided"])
    assert result.exit_code == 0, result.output
    plan_path = tmp_consumer / "models" / name / "process" / "plans" / "annotate-plan.yaml"
    enrich = runner.invoke(
        annotate,
        ["enrich", name, "--element", "sex", "--candidate", SEX_CANDIDATE],
    )
    assert enrich.exit_code == 0, enrich.output
    _set_annotate_decisions(
        plan_path,
        {
            "sex": {"decision": "accept"},
            "dob": {"decision": "unbound", "reason": "date / no terminology needed"},
            "pid": {"decision": "unbound", "reason": "identifier / no terminology needed"},
        },
    )
    assert runner.invoke(annotate, ["approve", name]).exit_code == 0
    impl = runner.invoke(annotate, ["implement", name])
    assert impl.exit_code == 0, impl.output
    return plan_path


def _specify_plan_path(root, name="spec-demo"):
    return root / "models" / name / "process" / "plans" / "specify-plan.yaml"


def _lm_path(root, name="spec-demo"):
    return root / "models" / name / "structured" / "logical-model.yaml"


def test_help_lists_specify():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "specify" in result.output
    sub = CliRunner().invoke(main, ["specify", "--help"])
    assert "plan" in sub.output
    assert "implement" in sub.output
    assert "verify" in sub.output


def test_plan_requires_annotate_complete(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    result = runner.invoke(specify, ["plan", name])
    assert result.exit_code != 0
    assert "annotate" in result.output.lower() or "bindings" in result.output.lower()
    assert not _specify_plan_path(tmp_consumer).exists()


def test_plan_writes_all_paths_and_normalizes_types(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    _annotate_complete(runner, tmp_consumer, name)
    inv_before = (tmp_consumer / "models" / name / "structured" / "inventory.yaml").read_text()
    bind_before = (tmp_consumer / "models" / name / "structured" / "bindings.yaml").read_text()
    result = runner.invoke(specify, ["plan", name])
    assert result.exit_code == 0, result.output
    plan = load_yaml(_specify_plan_path(tmp_consumer, name))
    assert plan["status"] == "draft"
    els = {el["id"]: el for ent in plan["entities"] for el in ent["elements"]}
    assert set(els) == {"sex", "dob", "pid"}
    assert els["sex"]["datatype"] == "code"
    assert els["dob"]["datatype"] == "unknown"
    assert els["pid"]["datatype"] == "unknown"
    assert "unknown-datatype" in els["dob"]["issues"]
    assert els["sex"]["binding"]["status"] == "bound"
    assert els["sex"]["binding"]["code"] == "76689-9"
    assert els["sex"]["binding"]["system"] == "http://loinc.org"
    assert els["dob"]["binding"]["status"] == "unbound"
    assert els["dob"]["binding"]["reason"]
    assert els["sex"]["provenance"]
    assert not _lm_path(tmp_consumer, name).exists()
    assert (tmp_consumer / "models" / name / "structured" / "inventory.yaml").read_text() == inv_before
    assert (tmp_consumer / "models" / name / "structured" / "bindings.yaml").read_text() == bind_before


def test_implement_fails_without_approve(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    _annotate_complete(runner, tmp_consumer, name)
    assert runner.invoke(specify, ["plan", name]).exit_code == 0
    result = runner.invoke(specify, ["implement", name])
    assert result.exit_code != 0
    assert "not approved" in result.output
    assert not _lm_path(tmp_consumer, name).exists()


def test_implement_writes_logical_model_and_status(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    _annotate_complete(runner, tmp_consumer, name)
    assert runner.invoke(specify, ["plan", name]).exit_code == 0
    plan_path = _specify_plan_path(tmp_consumer, name)
    plan = load_yaml(plan_path)
    for ent in plan["entities"]:
        for el in ent["elements"]:
            if el["id"] == "dob":
                el["datatype"] = "date"
                el["cardinality"] = "0..1"
                el["issues"] = []
    save_yaml(plan_path, plan)
    inv_before = (tmp_consumer / "models" / name / "structured" / "inventory.yaml").read_text()
    bind_before = (tmp_consumer / "models" / name / "structured" / "bindings.yaml").read_text()
    assert runner.invoke(specify, ["approve", name]).exit_code == 0
    result = runner.invoke(specify, ["implement", name])
    assert result.exit_code == 0, result.output
    lm = load_yaml(_lm_path(tmp_consumer, name))
    assert "status" not in lm
    by_id = {el["id"]: el for ent in lm["entities"] for el in ent["elements"]}
    assert by_id["dob"]["datatype"] == "date"
    assert by_id["dob"]["cardinality"] == "0..1"
    assert by_id["sex"]["binding"]["code"] == "76689-9"
    assert (tmp_consumer / "models" / name / "structured" / "inventory.yaml").read_text() == inv_before
    assert (tmp_consumer / "models" / name / "structured" / "bindings.yaml").read_text() == bind_before
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    assert "logical-model.yaml" in tracking["models"][0]["structured"]
    types = [e["type"] for e in tracking["models"][0]["events"]]
    assert "model_specified" in types
    st = runner.invoke(status, [name])
    assert st.exit_code == 0, st.output
    assert "Stage: specified" in st.output
    assert "Next: formalize" in st.output


def test_verify_idempotent_and_advisory_unknown(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    _annotate_complete(runner, tmp_consumer, name)
    runner.invoke(specify, ["plan", name])
    runner.invoke(specify, ["approve", name])
    runner.invoke(specify, ["implement", name])
    before = (tmp_consumer / "tracking.yaml").read_text()
    v1 = runner.invoke(specify, ["verify", name])
    v2 = runner.invoke(specify, ["verify", name])
    assert v1.exit_code == 0, v1.output
    assert v2.exit_code == 0, v2.output
    assert "unknown-datatype=" in v1.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before


def test_verify_path_mismatch_fails(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    _annotate_complete(runner, tmp_consumer, name)
    runner.invoke(specify, ["plan", name])
    runner.invoke(specify, ["approve", name])
    runner.invoke(specify, ["implement", name])
    lm_path = _lm_path(tmp_consumer, name)
    lm = load_yaml(lm_path)
    lm["entities"][0]["elements"].pop()
    save_yaml(lm_path, lm)
    result = runner.invoke(specify, ["verify", name])
    assert result.exit_code != 0
    assert "blocking" in result.output
