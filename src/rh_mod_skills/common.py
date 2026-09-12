"""Shared utilities for the rh-mod-skills CLI."""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
import sys
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import click
from ruamel.yaml import YAML

if sys.platform == "win32":
    import msvcrt

    def lock_file(f) -> None:
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def unlock_file(f) -> None:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def lock_file(f) -> None:
        fcntl.flock(f, fcntl.LOCK_EX)

    def unlock_file(f) -> None:
        fcntl.flock(f, fcntl.LOCK_UN)


MODEL_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
TOOL_PACKAGE_NAME = "rh-mod-skills"


def config_value(key: str, default: str | None = None) -> str | None:
    """Return a config value from the environment."""
    return os.environ.get(key, default)


def consumer_root() -> Path:
    """Return the consumer project root.

    Precedence: ``RH_REPO_ROOT`` → walk up for ``tracking.yaml`` → cwd.
    """
    if env := config_value("RH_REPO_ROOT"):
        return Path(env).resolve()
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        if (parent / "tracking.yaml").exists():
            return parent
    return cwd


def tracking_file() -> Path:
    if env := config_value("RH_TRACKING_FILE"):
        return Path(env)
    return consumer_root() / "tracking.yaml"


def models_root() -> Path:
    if env := config_value("RH_MODELS_ROOT"):
        return Path(env)
    return consumer_root() / "models"


def model_dir(name: str) -> Path:
    return models_root() / name


def is_tool_repo(path: Path) -> bool:
    """True if *path* is the rh-mod-skills tool repository."""
    pyproject = path / "pyproject.toml"
    if not pyproject.is_file():
        return False
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return data.get("project", {}).get("name") == TOOL_PACKAGE_NAME


def is_example_project(path: Path) -> bool:
    return path.name == "example-project" and is_tool_repo(path.parent)


def assert_init_root_allowed(root: Path) -> None:
    """Refuse to scaffold inside the tool repo unless example-project or RH_REPO_ROOT."""
    if config_value("RH_REPO_ROOT"):
        return
    resolved = root.resolve()
    if is_example_project(resolved):
        return
    if is_tool_repo(resolved):
        raise click.ClickException(
            "Refusing to init inside the rh-mod-skills tool repository. "
            "Run from a consumer project (e.g. example-project/) or set RH_REPO_ROOT."
        )


def require_kebab_case(model_id: str) -> None:
    if not MODEL_ID_RE.match(model_id):
        raise click.UsageError(
            f"Model name must be kebab-case (lowercase letters, digits, hyphens only): {model_id}"
        )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def log_info(msg: str) -> None:
    click.echo(f"✓ {msg}")


def log_warn(msg: str) -> None:
    click.echo(f"! [WARN] {msg}")


def _yaml_rt() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    return y


def load_tracking() -> dict:
    y = _yaml_rt()
    with open(tracking_file(), encoding="utf-8") as f:
        data = y.load(f) or {}
    data.setdefault("models", [])
    data.setdefault("events", [])
    if "topics" in data:
        raise click.ClickException(
            "tracking.yaml uses topics: — this product uses models/. "
            "This is not an rh-skills consumer project."
        )
    return data


def save_tracking(data: dict) -> None:
    tf = tracking_file()
    y = _yaml_rt()
    with tempfile.NamedTemporaryFile(
        mode="w", dir=tf.parent, suffix=".tmp", delete=False, encoding="utf-8"
    ) as tmp:
        y.dump(data, tmp)
        tmp_path = tmp.name
    os.replace(tmp_path, tf)


@contextlib.contextmanager
def _tracking_lock():
    lock_path = tracking_file().with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w", encoding="utf-8") as lf:
        lock_file(lf)
        try:
            yield
        finally:
            unlock_file(lf)


def locked_update_tracking(fn) -> None:
    with _tracking_lock():
        tracking = require_tracking()
        fn(tracking)
        save_tracking(tracking)


def require_tracking() -> dict:
    tf = tracking_file()
    if not tf.exists():
        raise click.ClickException(
            f"No tracking.yaml found. Run `rh-mod-skills init <model>` to start a model."
        )
    return load_tracking()


def ensure_tracking() -> None:
    tf = tracking_file()
    if tf.exists():
        return
    tf.parent.mkdir(parents=True, exist_ok=True)
    y = YAML()
    y.default_flow_style = False
    skeleton = {"schema_version": "1.0", "models": [], "events": []}
    try:
        with open(tf, "x", encoding="utf-8") as f:
            y.dump(skeleton, f)
    except FileExistsError:
        pass


def append_root_event(tracking: dict, type_: str, description: str) -> None:
    tracking.setdefault("events", []).append(
        {
            "timestamp": now_iso(),
            "type": type_,
            "description": description,
        }
    )


def append_model_event(tracking: dict, model_name: str, type_: str, description: str) -> None:
    for model in tracking.get("models", []):
        if model["name"] == model_name:
            model.setdefault("events", []).append(
                {
                    "timestamp": now_iso(),
                    "type": type_,
                    "description": description,
                }
            )
            return


def require_model(tracking: dict, name: str) -> dict:
    for model in tracking.get("models", []):
        if model["name"] == name:
            return model
    raise click.UsageError(
        f"Model '{name}' not found. Run `rh-mod-skills init {name}` to start it."
    )


def default_title(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split("-"))
