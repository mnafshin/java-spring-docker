# Contributing

Thanks for helping improve `springdocker`.

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## Before you push

Run the existing checks:

```bash
pytest
ruff check src tests
mypy src
```

## Change shape

- Keep commits small and focused.
- Add or update tests when behavior changes.
- Update docs when you change CLI flags, generated output, or benchmark flow.

## Code layout

- `src/springdocker/` for CLI and core logic
- `tests/unit/` for pure unit coverage
- `tests/integration/` for command and flow coverage
- `tests/e2e/` for end-to-end CLI flows
- `tests/benchmark/` for benchmark and snapshot coverage
- `samples/java-spring-docker/` for sample project assets
