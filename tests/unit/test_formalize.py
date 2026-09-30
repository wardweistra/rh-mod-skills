"""Tests for rh-mod-skills formalize."""

import json

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.annotate import annotate
from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.formalize import formalize
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.specify import specify
from rh_mod_skills.commands.status import status
from rh_mod_skills.common import sha256_file

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


def _formalize_plan_path(root, name="spec-demo"):
    return root / "models" / name / "process" / "plans" / "formalize-plan.yaml"


def _computable(root, name="spec-demo"):
    return root / "models" / name / "computable"


def _fill_unknown_types(plan_path):
    plan = load_yaml(plan_path)
    for ent in plan["entities"]:
        for el in ent["elements"]:
            if el["id"] == "sex":
                el["cardinality"] = "0..*"
            if el["id"] == "dob":
                el["datatype"] = "date"
                el["cardinality"] = "0..1"
            if el["id"] == "pid":
                el["datatype"] = "Identifier"
            issues = [i for i in (el.get("issues") or []) if i != "unknown-datatype"]
            if (el.get("cardinality") or "unknown") != "unknown":
                issues = [i for i in issues if i != "unknown-cardinality"]
            el["issues"] = issues
    save_yaml(plan_path, plan)


def _specified(tmp_consumer, typed=True, name="spec-demo"):
    runner, name = _mini_extracted(tmp_consumer, name)
    _annotate_complete(runner, tmp_consumer, name)
    assert runner.invoke(specify, ["plan", name]).exit_code == 0
    if typed:
        _fill_unknown_types(_specify_plan_path(tmp_consumer, name))
    assert runner.invoke(specify, ["approve", name]).exit_code == 0
    result = runner.invoke(specify, ["implement", name])
    assert result.exit_code == 0, result.output
    return runner, name


def test_help_lists_formalize():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "formalize" in result.output
    sub = CliRunner().invoke(main, ["formalize", "--help"])
    assert "plan" in sub.output
    assert "implement" in sub.output
    assert "verify" in sub.output


def test_plan_requires_logical_model(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    _annotate_complete(runner, tmp_consumer, name)
    result = runner.invoke(formalize, ["plan", name])
    assert result.exit_code != 0
    assert "logical model" in result.output.lower()
    assert not _formalize_plan_path(tmp_consumer, name).exists()
    assert not list(_computable(tmp_consumer, name).glob("*.json"))
    assert not (_computable(tmp_consumer, name) / "snapshot.yaml").exists()


def test_plan_writes_draft_canonical_and_counts(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=False)
    tracking_before = (tmp_consumer / "tracking.yaml").read_text()
    result = runner.invoke(formalize, ["plan", name])
    assert result.exit_code == 0, result.output
    plan = load_yaml(_formalize_plan_path(tmp_consumer, name))
    assert plan["status"] == "draft"
    assert str(plan["canonical"]).startswith("http")
    assert str(plan["version"])
    assert plan["unknown_cardinality"] >= 1
    unknown = list(plan["unknown_datatype"])
    assert unknown
    assert any("dob" in p for p in unknown)
    assert any("pid" in p for p in unknown)
    assert plan["bound"] == 1
    assert plan["unbound"] == 2
    assert not list(_computable(tmp_consumer, name).glob("*.json"))
    assert not (_computable(tmp_consumer, name) / "snapshot.yaml").exists()
    assert (tmp_consumer / "tracking.yaml").read_text() == tracking_before


def test_plan_lists_unknown_datatype_when_typed(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    result = runner.invoke(formalize, ["plan", name])
    assert result.exit_code == 0, result.output
    plan = load_yaml(_formalize_plan_path(tmp_consumer, name))
    assert list(plan["unknown_datatype"]) == []
    assert plan["unknown_cardinality"] >= 1


def test_implement_fails_without_approve(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code != 0
    assert "not approved" in result.output
    comp = _computable(tmp_consumer, name)
    assert not comp.exists() or not any(comp.iterdir())
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    types = [e["type"] for e in tracking["models"][0]["events"]]
    assert "model_formalized" not in types


def test_implement_fails_unknown_datatype(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=False)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code != 0
    assert "unknown datatype" in result.output.lower()
    comp = _computable(tmp_consumer, name)
    assert not comp.exists() or not list(comp.glob("*.json"))


def test_implement_fails_non_http_canonical(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    plan_path = _formalize_plan_path(tmp_consumer, name)
    plan = load_yaml(plan_path)
    plan["canonical"] = "urn:example:encr"
    save_yaml(plan_path, plan)
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code != 0
    assert "http" in result.output.lower()
    comp = _computable(tmp_consumer, name)
    assert not comp.exists() or not list(comp.glob("*.json"))


def test_implement_fails_canonical_last_segment(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    plan_path = _formalize_plan_path(tmp_consumer, name)
    plan = load_yaml(plan_path)
    plan["canonical"] = "https://encr.eu/fhir/recommendations"
    save_yaml(plan_path, plan)
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code != 0
    assert "last segment" in result.output.lower() or name in result.output
    comp = _computable(tmp_consumer, name)
    assert not comp.exists() or not list(comp.glob("*.json"))


def test_implement_fails_path_segment_over_64(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    lm_path = _lm_path(tmp_consumer, name)
    lm = load_yaml(lm_path)
    lm["entities"][0]["elements"][0]["path"] = "entity." + ("x" * 70)
    save_yaml(lm_path, lm)
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code != 0
    assert "64" in result.output
    comp = _computable(tmp_consumer, name)
    assert not comp.exists() or not list(comp.glob("*.json"))


def test_implement_writes_sd_valuesets_snapshot_and_status(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    lm_path = _lm_path(tmp_consumer, name)
    lm_before = lm_path.read_text()
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code == 0, result.output
    assert lm_path.read_text() == lm_before

    comp = _computable(tmp_consumer, name)
    sd_files = list(comp.glob("StructureDefinition-*.json"))
    assert len(sd_files) == 1
    sd = json.loads(sd_files[0].read_text(encoding="utf-8"))
    assert sd["resourceType"] == "StructureDefinition"
    assert sd["kind"] == "logical"
    assert sd["url"].startswith("http")
    by_path = {el["path"]: el for el in sd["differential"]["element"]}
    assert name in by_path
    lm = load_yaml(lm_path)
    bound_paths = []
    unknown_card_paths = []
    for ent in lm["entities"]:
        epath = f"{name}.{ent['id']}"
        assert by_path[epath]["type"] == [{"code": "BackboneElement"}]
        for el in ent["elements"]:
            fpath = f"{name}.{el['path']}"
            row = by_path[fpath]
            assert row["type"] == [{"code": el["datatype"]}]
            if (el.get("cardinality") or "unknown") == "unknown":
                unknown_card_paths.append(fpath)
                assert row["min"] == 0
                assert row["max"] == "1"
            if el["id"] == "sex":
                assert row["max"] == "*"
                assert row["binding"]["valueSet"]
                bound_paths.append(el["path"])
            else:
                assert "binding" not in row

    vs_files = list(comp.glob("ValueSet-*.json"))
    assert len(vs_files) == len(bound_paths) == 1
    vs = json.loads(vs_files[0].read_text(encoding="utf-8"))
    assert vs["resourceType"] == "ValueSet"
    concept = vs["compose"]["include"][0]["concept"][0]
    assert concept["code"] == "76689-9"

    snap = load_yaml(comp / "snapshot.yaml")
    assert snap["kind"] == "logical"
    json_names = {p.name for p in comp.glob("*.json")}
    listed = {row["path"].rsplit("/", 1)[-1] for row in snap["files"]}
    assert listed == json_names
    for row in snap["files"]:
        target = tmp_consumer / row["path"]
        assert sha256_file(target) == row["checksum"]

    assert not list((tmp_consumer / "models" / name).rglob("mapping.xlsx"))
    assert not list(comp.glob("*.map"))
    assert not list(comp.glob("StructureMap*"))
    assert unknown_card_paths

    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    types = [e["type"] for e in tracking["models"][0]["events"]]
    assert "model_formalized" in types
    computable = tracking["models"][0]["computable"]
    assert any(n.startswith("StructureDefinition-") for n in computable)
    assert "snapshot.yaml" in computable
    st = runner.invoke(status, [name])
    assert st.exit_code == 0, st.output
    assert "Stage: formalized" in st.output
    assert "Next: verify" in st.output


def test_verify_idempotent_and_advisory(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    runner.invoke(formalize, ["plan", name])
    runner.invoke(formalize, ["approve", name])
    assert runner.invoke(formalize, ["implement", name]).exit_code == 0
    before = (tmp_consumer / "tracking.yaml").read_text()
    v1 = runner.invoke(formalize, ["verify", name])
    v2 = runner.invoke(formalize, ["verify", name])
    assert v1.exit_code == 0, v1.output
    assert v2.exit_code == 0, v2.output
    assert "cardinality-default-n=" in v1.output
    assert "validator=not-run" in v1.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before


def test_verify_checksum_tamper_fails(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    runner.invoke(formalize, ["plan", name])
    runner.invoke(formalize, ["approve", name])
    assert runner.invoke(formalize, ["implement", name]).exit_code == 0
    snap_path = _computable(tmp_consumer, name) / "snapshot.yaml"
    snap = load_yaml(snap_path)
    snap["files"][0]["checksum"] = "0" * 64
    save_yaml(snap_path, snap)
    result = runner.invoke(formalize, ["verify", name])
    assert result.exit_code != 0
    assert "checksum" in result.output.lower()


def test_verify_kind_not_logical_fails(tmp_consumer):
    runner, name = _specified(tmp_consumer, typed=True)
    runner.invoke(formalize, ["plan", name])
    runner.invoke(formalize, ["approve", name])
    assert runner.invoke(formalize, ["implement", name]).exit_code == 0
    comp = _computable(tmp_consumer, name)
    sd_path = next(comp.glob("StructureDefinition-*.json"))
    sd = json.loads(sd_path.read_text(encoding="utf-8"))
    sd["kind"] = "resource"
    sd_path.write_text(json.dumps(sd, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    snap_path = comp / "snapshot.yaml"
    snap = load_yaml(snap_path)
    for row in snap["files"]:
        if row["path"].endswith(sd_path.name):
            row["checksum"] = sha256_file(sd_path)
    save_yaml(snap_path, snap)
    result = runner.invoke(formalize, ["verify", name])
    assert result.exit_code != 0
    assert "kind" in result.output.lower() or "logical" in result.output.lower()
