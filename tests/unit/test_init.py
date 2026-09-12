"""Tests for rh-mod-skills init."""

from pathlib import Path

from click.testing import CliRunner
from ruamel.yaml import YAML

from rh_mod_skills.cli import main
from rh_mod_skills.commands.init import init


def load_yaml(path):
    y = YAML()
    with open(path) as f:
        return y.load(f)


def test_init_creates_directory_structure(tmp_consumer):
    result = CliRunner().invoke(init, ["nkr-breast"])
    assert result.exit_code == 0, result.output
    md = tmp_consumer / "models" / "nkr-breast"
    assert md.is_dir()
    assert (md / "sources").is_dir()
    assert (md / "structured").is_dir()
    assert (md / "computable").is_dir()
    assert (md / "process" / "plans").is_dir()
    assert (md / "MODEL.md").is_file()
    assert (md / "process" / "notes.md").is_file()
    assert not (tmp_consumer / "topics").exists()


def test_init_creates_tracking_yaml(tmp_consumer):
    result = CliRunner().invoke(init, ["nkr-breast"])
    assert result.exit_code == 0, result.output
    assert (tmp_consumer / "tracking.yaml").exists()


def test_init_tracking_schema_and_events(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast", "--title", "NKR breast"])
    data = load_yaml(tmp_consumer / "tracking.yaml")
    assert str(data["schema_version"]) == "1.0"
    assert "topics" not in data
    names = [m["name"] for m in data["models"]]
    assert names == ["nkr-breast"]
    model = data["models"][0]
    assert model["title"] == "NKR breast"
    assert model["sources"] == []
    assert model["events"][0]["type"] == "created"
    assert data["events"][0]["type"] == "model_created"


def test_init_model_md_contains_name(tmp_consumer):
    CliRunner().invoke(init, ["encr-standard-dataset", "--description", "ENCR minimum dataset"])
    content = (tmp_consumer / "models" / "encr-standard-dataset" / "MODEL.md").read_text()
    assert 'name: "encr-standard-dataset"' in content
    assert "ENCR minimum dataset" in content


def test_init_flags(tmp_consumer):
    result = CliRunner().invoke(
        init,
        [
            "nkr-breast",
            "--title",
            "NKR breast cancer data dictionary",
            "--description",
            "IKNL variables",
            "--author",
            "Test Author",
        ],
    )
    assert result.exit_code == 0, result.output
    model = load_yaml(tmp_consumer / "tracking.yaml")["models"][0]
    assert model["title"] == "NKR breast cancer data dictionary"
    assert model["description"] == "IKNL variables"
    assert model["author"] == "Test Author"


def test_init_default_title_from_kebab(tmp_consumer):
    CliRunner().invoke(init, ["nkr-breast"])
    model = load_yaml(tmp_consumer / "tracking.yaml")["models"][0]
    assert model["title"] == "Nkr Breast"


def test_init_fails_if_model_exists(tmp_consumer):
    runner = CliRunner()
    runner.invoke(init, ["nkr-breast"])
    result = runner.invoke(init, ["nkr-breast"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_init_fails_for_uppercase(tmp_consumer):
    result = CliRunner().invoke(init, ["NkrBreast"])
    assert result.exit_code == 2


def test_init_help_on_main(tmp_consumer):
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "status" in result.output


def test_init_succeeds_from_example_project_layout(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "rh-mod-skills"\n', encoding="utf-8")
    consumer = tmp_path / "example-project"
    consumer.mkdir()
    monkeypatch.delenv("RH_REPO_ROOT", raising=False)
    monkeypatch.delenv("RH_TRACKING_FILE", raising=False)
    monkeypatch.delenv("RH_MODELS_ROOT", raising=False)
    monkeypatch.chdir(consumer)
    result = CliRunner().invoke(init, ["nkr-breast"])
    assert result.exit_code == 0, result.output
    assert (consumer / "tracking.yaml").exists()
    assert (consumer / "models" / "nkr-breast" / "MODEL.md").exists()


def test_init_refuses_tool_repo_without_rh_repo_root(monkeypatch):
    repo = Path(__file__).resolve().parents[2]
    monkeypatch.delenv("RH_REPO_ROOT", raising=False)
    monkeypatch.delenv("RH_TRACKING_FILE", raising=False)
    monkeypatch.delenv("RH_MODELS_ROOT", raising=False)
    monkeypatch.chdir(repo)
    result = CliRunner().invoke(init, ["nkr-breast"])
    assert result.exit_code == 1
    assert "tool repository" in result.output
    assert not (repo / "models" / "nkr-breast").exists()
    assert not (repo / "tracking.yaml").exists()
