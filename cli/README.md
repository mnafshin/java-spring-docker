# springdocker CLI

CLI for Spring Boot Dockerfile and benchmark workflows across Maven and Gradle projects.

## Install

### Local editable

```bash
python3 -m pip install -e .
```

### pipx

```bash
pipx install springdocker
springdocker --help
```

Upgrade:

```bash
pipx upgrade springdocker
```

### uv

```bash
uv tool install springdocker
uv tool upgrade springdocker
```

## Quick usage

```bash
springdocker init --project-root samples/java-spring-docker --build-tool maven --profile quick
springdocker doctor --project-root samples/java-spring-docker
springdocker inspect --project-root samples/java-spring-docker --format json
springdocker explain --project-root samples/java-spring-docker Dockerfile.generated --format json
springdocker benchmark compare --project-root samples/java-spring-docker benchmarks/03-custom-jre-jlink/results/raw.csv --baseline-variant with-jlink-runtime --format json
springdocker dockerfile generate --project-root samples/java-spring-docker --output Dockerfile.generated
springdocker benchmark generate --project-root samples/java-spring-docker --java-version 25
springdocker benchmark run --project-root samples/java-spring-docker --profile quick --runner-arg --skip-native
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/04-jep483-aot-cache/results/raw.csv --format table
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/04-jep483-aot-cache/results/raw.csv --format json --output benchmarks/04-jep483-aot-cache/results/summary.json
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/04-jep483-aot-cache/results/raw.csv --fail-on-success-rate-below 95
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/04-jep483-aot-cache/results/raw.csv --baseline benchmarks/04-jep483-aot-cache/results/baseline.json --fail-on-regression-above 20
```

## Config file (`.springdocker.toml`)

All command resolvers use precedence:

1. CLI flags
2. `.springdocker.toml`
3. defaults

Example:

```toml
[project]
build_tool = "maven"

[doctor]
build_tool = "maven"

[dockerfile]
output = "Dockerfile.generated"
java_version = 25
must_have_modules_file = "must-have.txt"
legacy_scripts = false
wizard_args = []

[benchmark.generate]
java_version = 25
legacy_scripts = false

[benchmark.run]
profile = "quick"
runner_args = ["--skip-native"]
cpuset_cpus = "0-1"
memory_limit = "2g"
warmup_runs = 1
normalized_runtime = true
legacy_scripts = false
```

When `dockerfile.must_have_modules_file` is set, springdocker reads modules from that file
(`must-have.txt` style, one module per line, `#` comments allowed) and injects them into
the jlink module list for reflection/dynamic-loading edge cases.

Create template config:

```bash
springdocker init --project-root samples/java-spring-docker --build-tool gradle
springdocker init --project-root samples/java-spring-docker --build-tool gradle --profile full --print
```

## Legacy compatibility mode

Main command paths are internal and do not require project script files.

To force script wrappers for compatibility:

```bash
springdocker dockerfile generate --use-legacy-scripts ...
springdocker benchmark generate --use-legacy-scripts ...
springdocker benchmark run --use-legacy-scripts ...
```

or set:

```bash
export SPRINGDOCKER_LEGACY_SCRIPTS=1
```

## Inspect command

`springdocker inspect` prints static metadata about the target project:

- detected build tool
- Spring Boot version when present
- Java version when present
- direct dependency coordinates
- generated Dockerfile artifacts in the project root
- basic runtime compatibility guidance

Use `--format json` for machine-readable output.

## Explain command

`springdocker explain` reads a springdocker-generated Dockerfile and describes the optimizations it contains:

- multi-stage layout
- BuildKit cache usage
- jlink runtime stage
- non-root runtime
- tuned JVM flags
- curated must-have modules

Use `--format json` when you want stable structured output.

## Security hardening

See `docs/security-hardening.md` for the runtime hardening defaults and recommended `docker run` flags.

## Binary distribution

See `docs/distribution.md` for packaging notes and sample Homebrew, Scoop, standalone binary, and Docker runtime artifacts.

## Multi-architecture builds

See `docs/multiarch.md` for the Buildx-friendly Dockerfile output and example multi-arch build command.

## Compare command

`springdocker benchmark compare` compares each variant against a required baseline variant and reports deltas.

- `--baseline-variant` selects the variant to compare against.
- `--scenario` narrows the CSV to one scenario.
- `--format json` produces machine-readable deltas.

## Benchmark run reproducibility

`springdocker benchmark run` supports deterministic benchmark controls for local or CI runs:

- `--cpuset-cpus` pins benchmark containers to specific CPUs.
- `--memory` caps container memory.
- `--warmup-runs` executes discarded warmup probes before recording results.
- `--normalized-runtime` applies read-only, no-new-privileges, and tmpfs isolation.

These settings can also come from `[benchmark.run]` in `.springdocker.toml`.
