"""Tests for rh-mod-skills ingest."""

from collections import Counter
from pathlib import Path

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
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


def _init(name="nkr-breast"):
    result = CliRunner().invoke(init, [name])
    assert result.exit_code == 0, result.output


def test_plan_does_not_copy_sources(tmp_consumer):
    _init()
    result = CliRunner().invoke(
        ingest, ["plan", "nkr-breast", "--source", str(IKNL)]
    )
    assert result.exit_code == 0, result.output
    plan = load_yaml(tmp_consumer / "models" / "nkr-breast" / "process" / "plans" / "ingest-plan.yaml")
    assert plan["status"] == "draft"
    assert plan["sources"][0]["type"] == "excel"
    assert plan["sources"][0]["projection"] == "tables"
    raw = tmp_consumer / "models" / "nkr-breast" / "sources" / "raw"
    assert not raw.exists() or not any(raw.iterdir())


def test_implement_fails_without_approval(tmp_consumer):
    _init()
    CliRunner().invoke(ingest, ["plan", "nkr-breast", "--source", str(IKNL)])
    result = CliRunner().invoke(ingest, ["implement", "nkr-breast"])
    assert result.exit_code == 1
    assert "not approved" in result.output
    assert not (tmp_consumer / "models" / "nkr-breast" / "sources" / "raw" / IKNL.name).exists()


def test_iknl_excel_projection(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(
        ingest,
        [
            "plan",
            "nkr-breast",
            "--source",
            str(IKNL),
            "--origin-url",
            "https://iknl.nl/nkr/cijfers-op-maat/over-datacatalogus",
        ],
    )
    assert runner.invoke(ingest, ["approve", "nkr-breast"]).exit_code == 0
    result = runner.invoke(ingest, ["implement", "nkr-breast"])
    assert result.exit_code == 0, result.output
    dest = tmp_consumer / "models" / "nkr-breast" / "sources" / "raw" / IKNL.name
    assert dest.is_file()
    proj = tmp_consumer / "models" / "nkr-breast" / "sources" / "projections" / "iknl-data-dictionary.yaml"
    data = load_yaml(proj)
    assert data["sheets"][0]["name"] == "Variabelen"
    assert data["sheets"][0]["columns"] == [
        "variabele_name",
        "variabele_categorie",
        "variabele_label",
    ]
    rows = data["sheets"][0]["rows"]
    assert len(rows) == 153
    assert rows[0][:3] == ["gebdat", "Patiëntgegevens", "Geboortedatum"]
    cats = Counter(r[1] for r in rows)
    assert cats["Behandelgegevens"] == 60
    assert cats["Tumorgegevens"] == 37
    assert cats["Procesgegevens"] == 33
    assert cats["Patiëntgegevens"] == 18
    assert cats["Risicofactoren"] == 5
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    src = tracking["models"][0]["sources"][0]
    assert src["type"] == "excel"
    assert src["origin_url"].startswith("https://iknl.nl")
    assert tracking["models"][0]["events"][-1]["type"] == "source_added"
    st = runner.invoke(status, ["nkr-breast"])
    assert "Stage: ingested" in st.output
    assert "Next: extract" in st.output
    assert "mapping" not in st.output.lower()


def test_pdf_without_tables_skips_projection(tmp_consumer):
    _init("blank-pdf")
    pdf = write_empty_pdf(tmp_consumer / "blank.pdf")
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "blank-pdf", "--source", str(pdf)])
    runner.invoke(ingest, ["approve", "blank-pdf"])
    result = runner.invoke(ingest, ["implement", "blank-pdf"])
    assert result.exit_code == 0, result.output
    dest = tmp_consumer / "models" / "blank-pdf" / "sources" / "raw" / pdf.name
    assert dest.is_file()
    proj_dir = tmp_consumer / "models" / "blank-pdf" / "sources" / "projections"
    assert not any(proj_dir.glob("*.yaml")) if proj_dir.exists() else True
    assert not list((tmp_consumer / "models" / "blank-pdf" / "sources").rglob("*.md"))
    tracking = load_yaml(tmp_consumer / "tracking.yaml")
    src = tracking["models"][0]["sources"][0]
    assert src["type"] == "pdf"
    assert src["projection"] == "skipped"
    verify = runner.invoke(ingest, ["verify", "blank-pdf"])
    assert verify.exit_code == 0, verify.output
    assert "skipped (no-text-layer)" in verify.output


def test_verify_idempotent_and_drift(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "nkr-breast", "--source", str(IKNL)])
    runner.invoke(ingest, ["approve", "nkr-breast"])
    runner.invoke(ingest, ["implement", "nkr-breast"])
    before = (tmp_consumer / "tracking.yaml").read_text()
    v1 = runner.invoke(ingest, ["verify", "nkr-breast"])
    v2 = runner.invoke(ingest, ["verify", "nkr-breast"])
    assert v1.exit_code == 0, v1.output
    assert v2.exit_code == 0, v2.output
    assert "rows=153" in v1.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before
    dest = tmp_consumer / "models" / "nkr-breast" / "sources" / "raw" / IKNL.name
    dest.write_bytes(dest.read_bytes() + b"x")
    drifted = runner.invoke(ingest, ["verify", "nkr-breast"])
    assert drifted.exit_code == 1
    assert "DRIFT" in drifted.output


def test_csv_projection(tmp_consumer):
    _init("csv-model")
    csv_path = tmp_consumer / "mini.csv"
    csv_path.write_text(
        "variabele_name,variabele_categorie,variabele_label\ngebdat,Patiëntgegevens,Geboortedatum\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "csv-model", "--source", str(csv_path)])
    runner.invoke(ingest, ["approve", "csv-model"])
    result = runner.invoke(ingest, ["implement", "csv-model"])
    assert result.exit_code == 0, result.output
    data = load_yaml(tmp_consumer / "models" / "csv-model" / "sources" / "projections" / "mini.yaml")
    assert data["type"] == "csv"
    assert data["sheets"][0]["rows"] == [["gebdat", "Patiëntgegevens", "Geboortedatum"]]


def test_acknowledge_drift_required_when_l2_present(tmp_consumer):
    _init()
    runner = CliRunner()
    runner.invoke(ingest, ["plan", "nkr-breast", "--source", str(IKNL)])
    runner.invoke(ingest, ["approve", "nkr-breast"])
    runner.invoke(ingest, ["implement", "nkr-breast"])
    l2 = tmp_consumer / "models" / "nkr-breast" / "structured" / "inventory.yaml"
    l2.write_text("elements: []\n", encoding="utf-8")
    other = tmp_consumer / "IKNL_Data_dictionary.xlsx"
    other.write_bytes(IKNL.read_bytes() + b"changed")
    runner.invoke(ingest, ["plan", "nkr-breast", "--source", str(other)])
    runner.invoke(ingest, ["approve", "nkr-breast"])
    blocked = runner.invoke(ingest, ["implement", "nkr-breast"])
    assert blocked.exit_code == 1
    assert "acknowledge-drift" in blocked.output
    assert l2.read_text() == "elements: []\n"
    forced = runner.invoke(ingest, ["implement", "nkr-breast", "--acknowledge-drift"])
    assert forced.exit_code == 0, forced.output
    assert l2.read_text() == "elements: []\n"


def test_help_lists_ingest(tmp_consumer):
    result = CliRunner().invoke(main, ["ingest", "--help"])
    assert result.exit_code == 0
    assert "plan" in result.output
    assert "implement" in result.output
    assert "verify" in result.output
