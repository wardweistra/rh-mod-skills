.PHONY: install test test-unit test-skills check-schemas sync-schemas

install:
	uv tool install --editable .

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/

test-skills:
	uv run pytest tests/skills/

check-schemas:
	@diff -r schemas/ src/rh_mod_skills/schemas/ && echo "Schemas in sync" || \
		(echo "Schema drift detected — run: make sync-schemas" && exit 1)

sync-schemas:
	mkdir -p src/rh_mod_skills/schemas
	cp schemas/*.yaml src/rh_mod_skills/schemas/ 2>/dev/null || true
	@echo "Bundled schemas updated from schemas/"
