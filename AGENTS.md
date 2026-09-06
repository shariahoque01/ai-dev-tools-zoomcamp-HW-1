Commands

- `uv sync` - install dependencies
- `uv run manage.py migrate` - apply database migrations
- `uv run pytest` - the whole suite
- `uv run pytest config/tests.py` - one test file
- `uv run ruff check .` - lint

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without
  asking.
