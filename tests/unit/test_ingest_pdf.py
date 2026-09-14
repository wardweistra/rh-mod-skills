"""Tests for PDF table projection on ingest (004)."""

from pathlib import Path

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.commands.extract import extract
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from pdf_fixtures import write_empty_pdf, write_text_pdf

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "l1"
ENCR = FIXTURES / "encr-standard-dataset" / "ENCR-Recommendation-standard-dataset_Mar2023.pdf"
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


def _init(name="encr-standard-dataset"):
    result = CliRunner().invoke(init, [name])
    assert result.exit_code == 0, result.output


def test_encr_plan_lists_table_1_and_2(tmp_consumer):
    _init()
    result = CliRunner().invoke(
        ingest,
        [
            "plan",
            "encr-standard-dataset",
            "--source",
            str(ENCR),
            "--origin-url",
            "https://www.encr.eu/ENCR-Recommendations",
        ],
    )
    assert result.exit_code == 0, result.output
    plan = load_yaml(
        tmp_consumer
        / "models"
        / "encr-standard-dataset"
        / "process"
        / "plans"
        / "ingest-plan.yaml"
    )
    assert plan["status"] == "draft"
    src = plan["sources"][0]
    assert src["type"] == "pdf"
    assert src["projection"] == "tables"
    names = [t["name"] for t in src["tables"]]
    assert "Table 1" in names
    assert "Table 2" in names
    by_name = {t["name"]: t for t in src["tables"]}
    assert by_name["Table 1"]["columns"][:2] == ["Variable", "Comment"]
    assert by_name["Table 1"]["row_count"] == 20
    assert by_name["Table 1"]["decision"] == "include"
    assert by_name["Table 2"]["columns"][0] == "Type of cancer"
    assert by_name["Table 2"]["row_count"] == 5
    assert 4 in by_name["Table 2"]["pages"]


def test_implement_fails_without_approval_no_projection(tmp_consumer):
    _init()
    CliRunner().invoke(ingest, ["plan", "encr-standard-dataset", "--source", str(ENCR)])
    result = CliRunner().invoke(ingest, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 1
    assert "not approved" in result.output
    proj = tmp_consumer / "models" / "encr-standard-dataset" / "sources" / "projections"
    assert not proj.exists() or not any(proj.glob("*.yaml"))


def test_encr_implement_projects_two_tables(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "encr-standard-dataset", "--source", str(ENCR)])
    runner.invoke(ingest, ["approve", "encr-standard-dataset"])
    result = runner.invoke(ingest, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 0, result.output
    raw = (
        tmp_consumer
        / "models"
        / "encr-standard-dataset"
        / "sources"
        / "raw"
        / ENCR.name
    )
    assert raw.is_file()
    assert not list(
        (tmp_consumer / "models" / "encr-standard-dataset" / "sources").rglob("*.md")
    )
    proj = tmp_consumer / "models" / "encr-standard-dataset" / "sources" / "projections"
    yaml_files = list(proj.glob("*.yaml"))
    assert len(yaml_files) == 1
    data = load_yaml(yaml_files[0])
    assert data["type"] == "pdf"
    sheets = {s["name"]: s for s in data["sheets"]}
    assert set(sheets) == {"Table 1", "Table 2"}
    assert sheets["Table 1"]["columns"] == ["Variable", "Comment"]
    assert len(sheets["Table 1"]["rows"]) == 20
    assert sheets["Table 1"]["rows"][0][0] == "Personal identification"
    assert len(sheets["Table 2"]["rows"]) == 5
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    src = tracking["models"][0]["sources"][0]
    assert src["projection"] == "tables"
    verify = runner.invoke(ingest, ["verify", "encr-standard-dataset"])
    assert verify.exit_code == 0, verify.output
    assert "sheets=2" in verify.output
    assert "skipped" not in verify.output.split("projection:")[-1][:40]


def test_exclude_table_2_keeps_table_1_only(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "encr-standard-dataset", "--source", str(ENCR)])
    plan_path = (
        tmp_consumer
        / "models"
        / "encr-standard-dataset"
        / "process"
        / "plans"
        / "ingest-plan.yaml"
    )
    plan = load_yaml(plan_path)
    for table in plan["sources"][0]["tables"]:
        if table["name"] == "Table 2":
            table["decision"] = "exclude"
            table["reason"] = "not the variable list"
    save_yaml(plan_path, plan)
    runner.invoke(ingest, ["approve", "encr-standard-dataset"])
    result = runner.invoke(ingest, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 0, result.output
    data = load_yaml(
        next(
            (
                tmp_consumer
                / "models"
                / "encr-standard-dataset"
                / "sources"
                / "projections"
            ).glob("*.yaml")
        )
    )
    assert [s["name"] for s in data["sheets"]] == ["Table 1"]
    assert len(data["sheets"][0]["rows"]) == 20


def test_all_tables_excluded_skips_projection(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "encr-standard-dataset", "--source", str(ENCR)])
    plan_path = (
        tmp_consumer
        / "models"
        / "encr-standard-dataset"
        / "process"
        / "plans"
        / "ingest-plan.yaml"
    )
    plan = load_yaml(plan_path)
    for table in plan["sources"][0]["tables"]:
        table["decision"] = "exclude"
        table["reason"] = "reviewer declined"
    save_yaml(plan_path, plan)
    runner.invoke(ingest, ["approve", "encr-standard-dataset"])
    result = runner.invoke(ingest, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 0, result.output
    proj = tmp_consumer / "models" / "encr-standard-dataset" / "sources" / "projections"
    assert not proj.exists() or not any(proj.glob("*.yaml"))
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    src = tracking["models"][0]["sources"][0]
    assert src["projection"] == "skipped"
    assert src["skip_reason"] == "no-tables-approved"


def test_empty_pdf_no_text_layer(tmp_consumer):
    _init("blank-pdf")
    pdf = write_empty_pdf(tmp_consumer / "blank.pdf")
    runner = CliRunner()
    plan = runner.invoke(ingest, ["plan", "blank-pdf", "--source", str(pdf)])
    assert plan.exit_code == 0, plan.output
    data = load_yaml(tmp_consumer / "models" / "blank-pdf" / "process" / "plans" / "ingest-plan.yaml")
    assert data["sources"][0]["projection"] == "skipped"
    assert data["sources"][0]["skip_reason"] == "no-text-layer"
    runner.invoke(ingest, ["approve", "blank-pdf"])
    result = runner.invoke(ingest, ["implement", "blank-pdf"])
    assert result.exit_code == 0, result.output
    proj = tmp_consumer / "models" / "blank-pdf" / "sources" / "projections"
    assert not proj.exists() or not any(proj.glob("*.yaml"))
    verify = runner.invoke(ingest, ["verify", "blank-pdf"])
    assert verify.exit_code == 0, verify.output
    assert "no-text-layer" in verify.output
    extract_plan = runner.invoke(extract, ["plan", "blank-pdf"])
    assert extract_plan.exit_code == 1
    assert "table projection" in extract_plan.output


def test_text_only_pdf_no_tables(tmp_consumer):
    _init("prose-pdf")
    pdf = write_text_pdf(tmp_consumer / "prose.pdf")
    runner = CliRunner()
    plan = runner.invoke(ingest, ["plan", "prose-pdf", "--source", str(pdf)])
    assert plan.exit_code == 0, plan.output
    data = load_yaml(tmp_consumer / "models" / "prose-pdf" / "process" / "plans" / "ingest-plan.yaml")
    assert data["sources"][0]["skip_reason"] == "no-tables-detected"
    runner.invoke(ingest, ["approve", "prose-pdf"])
    assert runner.invoke(ingest, ["implement", "prose-pdf"]).exit_code == 0
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    assert tracking["models"][0]["sources"][0]["projection"] == "skipped"


def test_mixed_excel_and_empty_pdf(tmp_consumer):
    _init("mixed")
    pdf = write_empty_pdf(tmp_consumer / "blank.pdf")
    runner = CliRunner()
    runner.invoke(
        ingest,
        ["plan", "mixed", "--source", str(IKNL), "--source", str(pdf)],
    )
    runner.invoke(ingest, ["approve", "mixed"])
    result = runner.invoke(ingest, ["implement", "mixed"])
    assert result.exit_code == 0, result.output
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    by_name = {s["name"]: s for s in tracking["models"][0]["sources"]}
    assert any(s.get("projection") == "tables" for s in by_name.values())
    assert any(s.get("skip_reason") == "no-text-layer" for s in by_name.values())
    iknl_proj = tmp_consumer / "models" / "mixed" / "sources" / "projections" / "iknl-data-dictionary.yaml"
    assert iknl_proj.is_file()
    rows = load_yaml(iknl_proj)["sheets"][0]["rows"]
    assert len(rows) == 153


def test_independent_pdf_sources(tmp_consumer):
    _init("two-pdf")
    empty = write_empty_pdf(tmp_consumer / "blank.pdf")
    runner = CliRunner()
    runner.invoke(
        ingest,
        ["plan", "two-pdf", "--source", str(ENCR), "--source", str(empty)],
    )
    runner.invoke(ingest, ["approve", "two-pdf"])
    result = runner.invoke(ingest, ["implement", "two-pdf"])
    assert result.exit_code == 0, result.output
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    by_type = {s["name"]: s for s in tracking["models"][0]["sources"]}
    tables = [s for s in by_type.values() if s.get("projection") == "tables"]
    skipped = [s for s in by_type.values() if s.get("projection") == "skipped"]
    assert len(tables) == 1
    assert len(skipped) == 1
    assert skipped[0]["skip_reason"] == "no-text-layer"


def test_extract_after_encr_tables(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "encr-standard-dataset", "--source", str(ENCR)])
    runner.invoke(ingest, ["approve", "encr-standard-dataset"])
    assert runner.invoke(ingest, ["implement", "encr-standard-dataset"]).exit_code == 0
    plan = runner.invoke(extract, ["plan", "encr-standard-dataset"])
    assert plan.exit_code == 0, plan.output
    runner.invoke(extract, ["approve", "encr-standard-dataset"])
    result = runner.invoke(extract, ["implement", "encr-standard-dataset"])
    assert result.exit_code == 0, result.output
    inv = load_yaml(
        tmp_consumer / "models" / "encr-standard-dataset" / "structured" / "inventory.yaml"
    )
    n_el = sum(len(e["elements"]) for e in inv["entities"])
    assert n_el == 25  # 20 Table 1 + 5 Table 2
    ids = [el["id"] for e in inv["entities"] for el in e["elements"]]
    assert "personal-identification" in ids
    assert not (
        tmp_consumer / "models" / "encr-standard-dataset" / "structured" / "bindings.yaml"
    ).exists()
