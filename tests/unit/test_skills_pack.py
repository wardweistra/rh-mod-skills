"""Constitution skill-pack layout for curated skills."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / "skills" / ".curated"

FULL_PACKS = ("rh-mod-ingest", "rh-mod-status")
SKILL_ONLY = ("rh-mod-extract", "rh-mod-annotate")


def _frontmatter_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    for line in text[3:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def test_ingest_and_status_are_full_packs():
    for name in FULL_PACKS:
        pack = CURATED / name
        skill = pack / "SKILL.md"
        assert skill.is_file(), pack
        assert (pack / "reference.md").is_file(), pack
        examples = pack / "examples"
        assert examples.is_dir(), pack
        assert any(examples.iterdir()), pack
        assert _frontmatter_name(skill) == name


def test_extract_and_annotate_remain_skill_md_only():
    for name in SKILL_ONLY:
        pack = CURATED / name
        assert (pack / "SKILL.md").is_file()
        assert not (pack / "reference.md").exists()
        assert _frontmatter_name(pack / "SKILL.md") == name
