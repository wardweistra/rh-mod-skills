"""Shared pytest fixtures for rh-mod-skills CLI tests."""

import os

import pytest


@pytest.fixture
def tmp_consumer(tmp_path):
    """Empty consumer project; init creates tracking.yaml here."""
    env_overrides = {
        "RH_REPO_ROOT": str(tmp_path),
        "RH_TRACKING_FILE": str(tmp_path / "tracking.yaml"),
        "RH_MODELS_ROOT": str(tmp_path / "models"),
    }
    old = {k: os.environ.get(k) for k in env_overrides}
    for k, v in env_overrides.items():
        os.environ[k] = v
    yield tmp_path
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
