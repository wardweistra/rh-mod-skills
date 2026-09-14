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
IKNL_EN = FIXTURES / "nkr-breast-en" / "IKNL_Data_dictionary_en.xlsx"
NBCA = FIXTURES / "nbca" / "IKNL-NBCA-2026-Variabelen-datadictionary-1-0-3-Raster.pdf"


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
    sheets = plan["sheets"]
    assert len(sheets) == 1
    roles = {c["header"]: c["role"] for c in sheets[0]["columns"]}
    assert roles["variabele_name"] == "id"
    assert roles["variabele_categorie"] == "category"
    assert roles["variabele_label"] == "label"
    assert all(c["origin"] == "hint" for c in sheets[0]["columns"])
    assert not (tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml").exists()
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    assert tracking["models"][0]["events"][-1]["type"] == "extract_planned"


def _ingest_named(name: str, source: Path):
    runner = CliRunner()
    _init(name)
    runner.invoke(ingest, ["plan", name, "--source", str(source)])
    runner.invoke(ingest, ["approve", name])
    result = runner.invoke(ingest, ["implement", name])
    assert result.exit_code == 0, result.output
    return runner


def test_plan_english_iknl_five_entities_153_elements(tmp_consumer):
    runner = _ingest_named("nkr-breast-en", IKNL_EN)
    result = runner.invoke(extract, ["plan", "nkr-breast-en"])
    assert result.exit_code == 0, result.output
    plan = load_yaml(
        tmp_consumer / "models" / "nkr-breast-en" / "process" / "plans" / "extract-plan.yaml"
    )
    titles = [e["title"] for e in plan["entities"]]
    assert titles == [
        "Patient data",
        "Tumour data",
        "Process data",
        "Risk factors",
        "Treatment data",
    ]
    counts = Counter(el["entity"] for el in plan["elements"])
    by_title = {e["title"]: counts[e["id"]] for e in plan["entities"]}
    assert by_title["Treatment data"] == 60
    assert by_title["Tumour data"] == 37
    assert by_title["Process data"] == 33
    assert by_title["Patient data"] == 18
    assert by_title["Risk factors"] == 5
    assert len(plan["elements"]) == 153
    first = plan["elements"][0]
    assert first["id"] == "gebdat"
    assert first["display"] == "Date of birth"
    assert first["provenance"]["sheet"] == "Variables"
    assert first["provenance"]["columns"]["id"] == "variable_name"
    roles = {c["header"]: c["role"] for c in plan["sheets"][0]["columns"]}
    assert roles["variable_name"] == "id"
    assert roles["variable_category"] == "category"
    assert roles["variable_label"] == "label"


def test_plan_nbca_three_entities_120_elements(tmp_consumer):
    runner = _ingest_named("nbca", NBCA)
    result = runner.invoke(extract, ["plan", "nbca"])
    assert result.exit_code == 0, result.output
    plan = load_yaml(
        tmp_consumer / "models" / "nbca" / "process" / "plans" / "extract-plan.yaml"
    )
    titles = [e["title"] for e in plan["entities"]]
    assert titles == ["patient", "episode", "tumor"]
    counts = Counter(el["entity"] for el in plan["elements"])
    assert counts["tumor"] == 74
    assert counts["episode"] == 34
    assert counts["patient"] == 12
    assert len(plan["elements"]) == 120
    assert all(el["id"] != "entity" and not el["id"].startswith("row-") for el in plan["elements"])
    first = plan["elements"][0]
    assert first["id"] == "id"
    assert first["display"] == "Zorginstelling"
    assert first["entity"] == "patient"
    geslacht = next(el for el in plan["elements"] if el["id"] == "geslacht")
    assert geslacht["display"] == "Geslacht"
    assert geslacht["provenance"]["columns"]["id"] == "VARIABELE"
    roles = {c["header"]: c["role"] for c in plan["sheets"][0]["columns"]}
    assert roles["VARIABELE"] == "id"
    assert roles["DATASET"] == "category"
    assert roles["omschrijving variabele"] == "label"


def test_unrecognized_layout_one_element_per_row(tmp_consumer):
    _init("odd-sheet")
    csv = tmp_consumer / "odd.csv"
    csv.write_text("foo,bar\nalpha,one\nbeta,two\n", encoding="utf-8")
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "odd-sheet", "--source", str(csv)])
    runner.invoke(ingest, ["approve", "odd-sheet"])
    assert runner.invoke(ingest, ["implement", "odd-sheet"]).exit_code == 0
    result = runner.invoke(extract, ["plan", "odd-sheet"])
    assert result.exit_code == 0, result.output
    plan = load_yaml(
        tmp_consumer / "models" / "odd-sheet" / "process" / "plans" / "extract-plan.yaml"
    )
    ids = [el["id"] for el in plan["elements"]]
    assert ids == ["row-1", "row-2"]
    assert [el["notes"]["foo"] for el in plan["elements"]] == ["alpha", "beta"]
    roles = {c["header"]: c["role"] for c in plan["sheets"][0]["columns"]}
    assert roles == {"foo": "unused", "bar": "unused"}


def test_remap_roles_rebuilds_elements(tmp_consumer):
    _init("odd-sheet")
    csv = tmp_consumer / "odd.csv"
    csv.write_text("foo,bar\nalpha,one\nbeta,two\n", encoding="utf-8")
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "odd-sheet", "--source", str(csv)])
    runner.invoke(ingest, ["approve", "odd-sheet"])
    assert runner.invoke(ingest, ["implement", "odd-sheet"]).exit_code == 0
    assert runner.invoke(extract, ["plan", "odd-sheet"]).exit_code == 0
    plan_path = tmp_consumer / "models" / "odd-sheet" / "process" / "plans" / "extract-plan.yaml"
    plan = load_yaml(plan_path)
    for col in plan["sheets"][0]["columns"]:
        if col["header"] == "foo":
            col["role"] = "id"
            col["origin"] = "reviewer"
        if col["header"] == "bar":
            col["role"] = "label"
            col["origin"] = "reviewer"
    save_yaml(plan_path, plan)
    result = runner.invoke(extract, ["plan", "odd-sheet"])
    assert result.exit_code == 0, result.output
    rebuilt = load_yaml(plan_path)
    roles = {c["header"]: (c["role"], c["origin"]) for c in rebuilt["sheets"][0]["columns"]}
    assert roles["foo"] == ("id", "reviewer")
    assert roles["bar"] == ("label", "reviewer")
    assert [el["id"] for el in rebuilt["elements"]] == ["alpha", "beta"]
    assert [el["display"] for el in rebuilt["elements"]] == ["one", "two"]
    assert runner.invoke(extract, ["approve", "odd-sheet"]).exit_code == 0
    assert runner.invoke(extract, ["implement", "odd-sheet"]).exit_code == 0
    inv = load_yaml(tmp_consumer / "models" / "odd-sheet" / "structured" / "inventory.yaml")
    els = inv["entities"][0]["elements"]
    assert [el["id"] for el in els] == ["alpha", "beta"]
    verify = runner.invoke(extract, ["verify", "odd-sheet"])
    assert verify.exit_code == 0, verify.output
    assert "missing=0" in verify.output

    rehint = runner.invoke(extract, ["plan", "odd-sheet", "--rehint"])
    assert rehint.exit_code == 0, rehint.output
    hinted = load_yaml(plan_path)
    hinted_roles = {c["header"]: c["role"] for c in hinted["sheets"][0]["columns"]}
    assert hinted_roles == {"foo": "unused", "bar": "unused"}
    assert [el["id"] for el in hinted["elements"]] == ["row-1", "row-2"]


def test_replan_preserves_dropped_element(tmp_consumer):
    runner = _ingest_iknl()
    runner.invoke(extract, ["plan", "nkr-breast"])
    plan_path = tmp_consumer / "models" / "nkr-breast" / "process" / "plans" / "extract-plan.yaml"
    plan = load_yaml(plan_path)
    for el in plan["elements"]:
        if el["id"] == "gebdat":
            el["decision"] = "drop"
            el["reason"] = "privacy"
    save_yaml(plan_path, plan)
    result = runner.invoke(extract, ["plan", "nkr-breast"])
    assert result.exit_code == 0, result.output
    rebuilt = load_yaml(plan_path)
    gebdat = next(el for el in rebuilt["elements"] if el["id"] == "gebdat")
    assert gebdat["decision"] == "drop"
    assert gebdat["reason"] == "privacy"


def test_duplicate_id_role_fails_implement(tmp_consumer):
    _init("odd-sheet")
    csv = tmp_consumer / "odd.csv"
    csv.write_text("foo,bar\nalpha,one\nbeta,two\n", encoding="utf-8")
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "odd-sheet", "--source", str(csv)])
    runner.invoke(ingest, ["approve", "odd-sheet"])
    assert runner.invoke(ingest, ["implement", "odd-sheet"]).exit_code == 0
    runner.invoke(extract, ["plan", "odd-sheet"])
    plan_path = tmp_consumer / "models" / "odd-sheet" / "process" / "plans" / "extract-plan.yaml"
    plan = load_yaml(plan_path)
    for col in plan["sheets"][0]["columns"]:
        col["role"] = "id"
    save_yaml(plan_path, plan)
    runner.invoke(extract, ["plan", "odd-sheet"])
    runner.invoke(extract, ["approve", "odd-sheet"])
    result = runner.invoke(extract, ["implement", "odd-sheet"])
    assert result.exit_code == 1
    assert "duplicate column roles" in result.output
    assert not (tmp_consumer / "models" / "odd-sheet" / "structured" / "inventory.yaml").exists()


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
    plan_help = CliRunner().invoke(main, ["extract", "plan", "--help"])
    assert plan_help.exit_code == 0
    assert "--rehint" in plan_help.output
