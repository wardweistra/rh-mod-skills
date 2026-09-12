from click.testing import CliRunner

from rh_mod_skills.cli import main


def test_version_command():
    result = CliRunner().invoke(main, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


def test_help_lists_cli():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "logical models" in result.output.lower()
