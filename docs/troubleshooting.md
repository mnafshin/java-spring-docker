# Troubleshooting

## `springdocker doctor` reports project detection failures

- Confirm `--project-root` points at a Spring Boot project.
- Ensure `pom.xml`, `build.gradle`, or `build.gradle.kts` exists in the project root.
- Run `springdocker inspect --project-root <path> --format json` to see detected metadata.

## `springdocker dockerfile generate` fails

- Run `springdocker init --project-root <path>` first to create `.springdocker.toml`.
- Ensure the configured Java version is 17 or newer.
- Re-run with `--print` to inspect generated output before writing files.

## Benchmark commands fail

- Verify Docker is available locally (`docker --version`).
- Use the sample project path used in docs (`samples/java-spring-docker/`) when reproducing examples.
- Start with quick profile:
  `springdocker benchmark run --project-root samples/java-spring-docker --profile quick`

## CI behavior differs from local

- Use a clean virtual environment:
  `python3 -m venv .venv && . .venv/bin/activate`
- Install development dependencies:
  `python -m pip install -e ".[dev]"`
- Run the same checks as CI:
  `ruff check src tests && mypy && pytest -q`
