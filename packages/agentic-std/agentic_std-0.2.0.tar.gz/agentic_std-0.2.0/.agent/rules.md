# Project Rules

## Tech Stack

- [x] Language: Python 3.10+
- [x] CLI Framework: Typer (or Click as alternative)
- [x] Packaging: `pyproject.toml` with `entry_points` for global CLI access
- [x] Distribution: PyPI (`pip install agentic-std`)
- [x] HTTP Client: `requests` or `httpx` (for sync engine)

## Naming Conventions

- [x] Files: `snake_case.py`
- [x] Classes: `PascalCase`
- [x] Variables/Functions: `snake_case`
- [x] Constants: `SCREAMING_SNAKE_CASE`
- [x] CLI Commands: `kebab-case` (e.g., `acs init`, `acs update`)

## Directory Structure

```
acs-cli/
├── src/
│   └── acs_cli/
│       ├── __init__.py
│       ├── cli.py          # CLI entry points
│       ├── templates/      # Bundled template files
│       └── sync.py         # Update/sync logic
├── pyproject.toml
├── README.md
└── .agent/
```

## Verification Steps

- [ ] **Unit Tests**: Run `pytest` before marking tasks complete
- [ ] **Linting**: Ensure code passes `ruff` or `flake8` checks
- [ ] **Type Checking**: Run `mypy` for type validation
- [x] **Manual Check**: Test `acs init` and `acs update` in a fresh directory
- [x] **Build Check**: Verify `pip install -e .` and `acs update` work without errors
