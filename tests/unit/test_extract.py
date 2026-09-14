"""Tests for rh-mod-skills extract."""

from collections import Counter
from pathlib import Path

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.status import status

from pdf_fixtures import write_empty_pdf

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "l1"
IKNL = FIXTURES / "nkr-breast" / "IKNL_Data_dictionary.xlsx"


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


def _ingest_iknl():
    runner = CliRunner()
    _init()
    runner.invoke(ingest, ["plan", "nkr-breast", "--source", str(IKNL)])
    runner.invoke(ingest, ["approve", "nkr-breast"])
    result = runner.invoke(ingest, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    return runner


def test_plan_iknl_five_entities_153_elements(tmp_consumer):
    runner = _ingest_iknl()
    result = runner.invoke(extract, ["plan", "nkr-breast"])
    assert result.exit_code == 0, result.output
    plan = load_yaml(
        tmp_consumer / "models" / "nkr-breast" / "process" / "plans" / "extract-plan.yaml"
    )
    assert plan["status"] == "draft"
    titles = [e["title"] for e in plan["entities"]]
    assert titles == [
        "Patiëntgegevens",
        "Tumorgegevens",
        "Procesgegevens",
        "Risicofactoren",
        "Behandelgegevens",
    ]
    counts = Counter(el["entity"] for el in plan["elements"])
    by_title = {e["title"]: counts[e["id"]] for e in plan["entities"]}
    assert by_title["Behandelgegevens"] == 60
    assert by_title["Tumorgegevens"] == 37
    assert by_title["Procesgegevens"] == 33
    assert by_title["Patiëntgegevens"] == 18
    assert by_title["Risicofactoren"] == 5
    assert len(plan["elements"]) == 153
    first = plan["elements"][0]
    assert first["id"] == "gebdat"
    assert first["display"] == "Geboortedatum"
    assert first["datatype"] == "unknown"
    assert first["cardinality"] == "unknown"
    assert first["provenance"]["sheet"] == "Variabelen"
    assert first["provenance"]["row"] == 1
    assert not (tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml").exists()
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    assert tracking["models"][0]["events"][-1]["type"] == "extract_planned"


def test_implement_fails_without_approval(tmp_consumer):
    runner = _ingest_iknl()
    runner.invoke(extract, ["plan", "nkr-breast"])
    result = runner.invoke(extract, ["implement", "nkr-breast"])
    assert result.exit_code == 1
    assert "not approved" in result.output
    assert not (tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml").exists()
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    types = [e["type"] for e in tracking["models"][0]["events"]]
    assert "inventory_derived" not in types


def test_implement_writes_iknl_inventory(tmp_consumer):
    runner = _ingest_iknl()
    runner.invoke(extract, ["plan", "nkr-breast"])
    assert runner.invoke(extract, ["approve", "nkr-breast"]).exit_code == 0
    result = runner.invoke(extract, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    inv = load_yaml(tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml")
    assert len(inv["entities"]) == 5
    n_el = sum(len(e["elements"]) for e in inv["entities"])
    assert n_el == 153
    gebdat = inv["entities"][0]["elements"][0]
    assert gebdat["id"] == "gebdat"
    assert gebdat["datatype"] == "unknown"
    assert gebdat["cardinality"] == "unknown"
    assert not (tmp_consumer / "models" / "nkr-breast" / "structured" / "bindings.yaml").exists()
    assert not (
        tmp_consumer / "models" / "nkr-breast" / "structured" / "value-domains.yaml"
    ).exists()
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    assert tracking["models"][0]["events"][-1]["type"] == "inventory_derived"
    assert "inventory.yaml" in tracking["models"][0]["structured"]
    st = runner.invoke(status, ["nkr-breast"])
    assert "Stage: extracted" in st.output
    assert "Next: annotate" in st.output
    assert "mapping" not in st.output.lower()


def test_reviewer_drop_and_rename(tmp_consumer):
    runner = _ingest_iknl()
    runner.invoke(extract, ["plan", "nkr-breast"])
    plan_path = tmp_consumer / "models" / "nkr-breast" / "process" / "plans" / "extract-plan.yaml"
    plan = load_yaml(plan_path)
    for ent in plan["entities"]:
        if ent["id"] == "patientgegevens":
            ent["id"] = "patient"
            ent["title"] = "Patient"
    for el in plan["elements"]:
        if el["entity"] == "patientgegevens":
            el["entity"] = "patient"
            el["path"] = el["path"].replace("patientgegevens.", "patient.")
        if el["id"] == "gebdat":
            el["decision"] = "drop"
            el["reason"] = "privacy"
    save_yaml(plan_path, plan)
    runner.invoke(extract, ["approve", "nkr-breast"])
    result = runner.invoke(extract, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    inv = load_yaml(tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml")
    titles = [e["title"] for e in inv["entities"]]
    assert "Patient" in titles
    assert "Patiëntgegevens" not in titles
    ids = [el["id"] for e in inv["entities"] for el in e["elements"]]
    assert "gebdat" not in ids
    assert len(ids) == 152
    verify = runner.invoke(extract, ["verify", "nkr-breast"])
    assert verify.exit_code == 0, verify.output
    assert "excluded=1" in verify.output
    assert "missing=0" in verify.output


def test_reviewer_merge_entities(tmp_consumer):
    _init("merge-model")
    csv_path = tmp_consumer / "mini.csv"
    csv_path.write_text(
        "variabele_name,variabele_categorie,variabele_label\n"
        "a,GroupA,Alpha\n"
        "b,GroupB,Beta\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "merge-model", "--source", str(csv_path)])
    runner.invoke(ingest, ["approve", "merge-model"])
    assert runner.invoke(ingest, ["implement", "merge-model"]).exit_code == 0
    runner.invoke(extract, ["plan", "merge-model"])
    plan_path = tmp_consumer / "models" / "merge-model" / "process" / "plans" / "extract-plan.yaml"
    plan = load_yaml(plan_path)
    for ent in plan["entities"]:
        if ent["id"] == "groupb":
            ent["decision"] = "merge-into"
            ent["merge_into"] = "groupa"
            ent["reason"] = "same clinical class"
    save_yaml(plan_path, plan)
    runner.invoke(extract, ["approve", "merge-model"])
    result = runner.invoke(extract, ["implement", "merge-model"])
    assert result.exit_code == 0, result.output
    inv = load_yaml(tmp_consumer / "models" / "merge-model" / "structured" / "inventory.yaml")
    assert len(inv["entities"]) == 1
    assert inv["entities"][0]["id"] == "groupa"
    ids = [el["id"] for el in inv["entities"][0]["elements"]]
    assert ids == ["a", "b"]


def test_pdf_only_plan_fails(tmp_consumer):
    runner = CliRunner()
    _init("pdf-only")
    pdf = write_empty_pdf(tmp_consumer / "blank.pdf")
    runner.invoke(ingest, ["plan", "pdf-only", "--source", str(pdf)])
    runner.invoke(ingest, ["approve", "pdf-only"])
    assert runner.invoke(ingest, ["implement", "pdf-only"]).exit_code == 0
    result = runner.invoke(extract, ["plan", "pdf-only"])
    assert result.exit_code == 1
    assert "table projection" in result.output
    plan = tmp_consumer / "models" / "pdf-only" / "process" / "plans" / "extract-plan.yaml"
    assert not plan.exists()


def test_verify_idempotent(tmp_consumer):
    runner = _ingest_iknl()
    runner.invoke(extract, ["plan", "nkr-breast"])
    runner.invoke(extract, ["approve", "nkr-breast"])
    runner.invoke(extract, ["implement", "nkr-breast"])
    before = (tmp_consumer / "tracking.yaml").read_text()
    v1 = runner.invoke(extract, ["verify", "nkr-breast"])
    v2 = runner.invoke(extract, ["verify", "nkr-breast"])
    assert v1.exit_code == 0, v1.output
    assert v2.exit_code == 0, v2.output
    assert "elements=153" in v1.output
    assert "covered=153" in v1.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before


def test_replace_required_when_inventory_exists(tmp_consumer):
    runner = _ingest_iknl()
    runner.invoke(extract, ["plan", "nkr-breast"])
    runner.invoke(extract, ["approve", "nkr-breast"])
    runner.invoke(extract, ["implement", "nkr-breast"])
    blocked = runner.invoke(extract, ["implement", "nkr-breast"])
    assert blocked.exit_code == 1
    assert "--replace" in blocked.output
    forced = runner.invoke(extract, ["implement", "nkr-breast", "--replace"])
    assert forced.exit_code == 0, forced.output


def test_homonyms_kept_distinct(tmp_consumer):
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
    result = runner.invoke(extract, ["plan", "two-sheet"])
    assert result.exit_code == 0, result.output
    plan = load_yaml(
        tmp_consumer / "models" / "two-sheet" / "process" / "plans" / "extract-plan.yaml"
    )
    statuses = [el for el in plan["elements"] if el["id"] == "status"]
    assert len(statuses) == 2
    sheets = {el["provenance"]["sheet"] for el in statuses}
    assert sheets == {"sheet-a", "sheet-b"}


def test_value_domains_from_code_list_sheet(tmp_consumer):
    _init("with-codes")
    dictionary = tmp_consumer / "dictionary.csv"
    codes = tmp_consumer / "codes.csv"
    dictionary.write_text(
        "variabele_name,variabele_categorie,variabele_label\n"
        "status,Tumorgegevens,Status\n",
        encoding="utf-8",
    )
    codes.write_text(
        "variable,code,display\nstatus,1,Active\nstatus,2,Inactive\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    runner.invoke(
        ingest,
        ["plan", "with-codes", "--source", str(dictionary), "--source", str(codes)],
    )
    runner.invoke(ingest, ["approve", "with-codes"])
    assert runner.invoke(ingest, ["implement", "with-codes"]).exit_code == 0
    runner.invoke(extract, ["plan", "with-codes"])
    runner.invoke(extract, ["approve", "with-codes"])
    result = runner.invoke(extract, ["implement", "with-codes"])
    assert result.exit_code == 0, result.output
    inv = load_yaml(tmp_consumer / "models" / "with-codes" / "structured" / "inventory.yaml")
    el = inv["entities"][0]["elements"][0]
    assert el["id"] == "status"
    assert el["value_domain"] == "status"
    domains = load_yaml(
        tmp_consumer / "models" / "with-codes" / "structured" / "value-domains.yaml"
    )
    assert domains["domains"][0]["id"] == "status"
    assert [c["code"] for c in domains["domains"][0]["codes"]] == ["1", "2"]


def test_help_lists_extract():
    result = CliRunner().invoke(main, ["extract", "--help"])
    assert result.exit_code == 0
    assert "plan" in result.output
    assert "implement" in result.output
    assert "verify" in result.output
