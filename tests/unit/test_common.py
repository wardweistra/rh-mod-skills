"""Tests for consumer-root and kebab-case helpers."""

from pathlib import Path

import click
import pytest

from rh_mod_skills.common import (
    MODEL_ID_RE,
    assert_init_root_allowed,
    default_title,
    is_example_project,
    is_tool_repo,
    require_kebab_case,
)


def test_kebab_case_accepts_valid_ids():
    require_kebab_case("nkr-breast")
    require_kebab_case("encr-standard-dataset")
    require_kebab_case("a")
    assert MODEL_ID_RE.match("tumor-registry")


def test_kebab_case_rejects_uppercase():
    with pytest.raises(click.UsageError):
        require_kebab_case("NkrBreast")


def test_kebab_case_rejects_underscore():
    with pytest.raises(click.UsageError):
        require_kebab_case("nkr_breast")


def test_default_title_from_kebab():
    assert default_title("nkr-breast") == "Nkr Breast"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_is_tool_repo_this_workspace():
    assert is_tool_repo(_repo_root())


def test_is_example_project_under_tool_repo():
    assert is_example_project(_repo_root() / "example-project")


def test_assert_init_allows_rh_repo_root(tmp_path, monkeypatch):
    monkeypatch.setenv("RH_REPO_ROOT", str(tmp_path))
    assert_init_root_allowed(tmp_path)


def test_assert_init_refuses_tool_repo(monkeypatch):
    repo = _repo_root()
    monkeypatch.delenv("RH_REPO_ROOT", raising=False)
    with pytest.raises(click.ClickException, match="tool repository"):
        assert_init_root_allowed(repo)


def test_assert_init_allows_example_project(monkeypatch):
    monkeypatch.delenv("RH_REPO_ROOT", raising=False)
    assert_init_root_allowed(_repo_root() / "example-project")
