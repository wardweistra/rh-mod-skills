"""Tests for rh-mod-skills verify coordinator."""

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.formalize import formalize
from rh_mod_skills.commands.init import init
from rh_mod_skills.commands.ingest import ingest
from rh_mod_skills.commands.status import status
from rh_mod_skills.commands.verify import verify
from test_formalize import _mini_extracted, _specified, load_yaml, save_yaml


def _formalized(tmp_consumer, name="spec-demo"):
    runner, name = _specified(tmp_consumer, typed=True, name=name)
    assert runner.invoke(formalize, ["plan", name]).exit_code == 0
    assert runner.invoke(formalize, ["approve", name]).exit_code == 0
    result = runner.invoke(formalize, ["implement", name])
    assert result.exit_code == 0, result.output
    return runner, name


def test_help_lists_verify():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "verify" in result.output


def test_formalized_idempotent_coverage_and_advisory(tmp_consumer):
    runner, name = _formalized(tmp_consumer)
    before = (tmp_consumer / "tracking.yaml").read_text()
    v1 = runner.invoke(verify, [name])
    v2 = runner.invoke(verify, [name])
    assert v1.exit_code == 0, v1.output
    assert v2.exit_code == 0, v2.output
    assert "coverage: inventory=3 mapped=1 unbound=2 undecided=0" in v1.output
    assert "ingest: pass" in v1.output
    assert "extract: pass" in v1.output
    assert "annotate: pass" in v1.output
    assert "specify: pass" in v1.output
    assert "formalize: pass" in v1.output
    assert "unbound=2" in v1.output
    assert "validator=not-run" in v1.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before
    st = runner.invoke(status, [name])
    assert st.exit_code == 0, st.output
    assert "Next: verify" in st.output


def test_checksum_tamper_fails_without_tracking_write(tmp_consumer):
    runner, name = _formalized(tmp_consumer)
    snap_path = tmp_consumer / "models" / name / "computable" / "snapshot.yaml"
    snap = load_yaml(snap_path)
    snap["files"][0]["checksum"] = "0" * 64
    save_yaml(snap_path, snap)
    before = (tmp_consumer / "tracking.yaml").read_text()
    result = runner.invoke(verify, [name])
    assert result.exit_code != 0
    assert "formalize: fail" in result.output
    assert (tmp_consumer / "tracking.yaml").read_text() == before


def test_extracted_skips_later_stages(tmp_consumer):
    runner, name = _mini_extracted(tmp_consumer)
    before = (tmp_consumer / "tracking.yaml").read_text()
    result = runner.invoke(verify, [name])
    assert result.exit_code == 0, result.output
    assert "ingest: pass" in result.output
    assert "extract: pass" in result.output
    assert "annotate: pass" in result.output
    assert "specify: skipped" in result.output
    assert "formalize: skipped" in result.output
    assert "structuredefinition: missing" not in result.output.lower()
    assert (tmp_consumer / "tracking.yaml").read_text() == before


def test_empty_portfolio_matches_status(tmp_consumer):
    y = YAML()
    y.default_flow_style = False
    with open(tmp_consumer / "tracking.yaml", "w") as f:
        y.dump({"schema_version": "1.0", "models": [], "events": []}, f)
    result = CliRunner().invoke(verify, [])
    assert result.exit_code == 0, result.output
    assert "No models yet" in result.output
    assert "Next: init" in result.output


def test_portfolio_reports_all_and_fails_on_drift(tmp_consumer):
    runner, ok_name = _mini_extracted(tmp_consumer, name="ok-model")
    csv2 = tmp_consumer / "other.csv"
    csv2.write_text("name,label,datatype\nx,X,string\n", encoding="utf-8")
    assert runner.invoke(init, ["drift-demo"]).exit_code == 0
    runner.invoke(ingest, ["plan", "drift-demo", "--source", str(csv2)])
    runner.invoke(ingest, ["approve", "drift-demo"])
    assert runner.invoke(ingest, ["implement", "drift-demo"]).exit_code == 0
    dest = tmp_consumer / "models" / "drift-demo" / "sources" / "raw" / "other.csv"
    dest.write_bytes(dest.read_bytes() + b"x")
    result = runner.invoke(verify, [])
    assert result.exit_code != 0
    assert "ok-model" in result.output
    assert "drift-demo" in result.output
    assert "ingest: fail" in result.output
