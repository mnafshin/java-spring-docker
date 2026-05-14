# springdocker CLI (v0 scaffold)

This is an initial CLI scaffold to run existing project tooling with a stable interface.

## Install (local editable)

```bash
cd /path/to/your-java25-project
python3 -m pip install -e .
```

## Quick usage

```bash
springdocker init --project-root samples/java-spring-docker --build-tool maven
springdocker doctor --project-root samples/java-spring-docker
springdocker dockerfile generate --project-root samples/java-spring-docker --build-tool maven --output Dockerfile.generated
springdocker benchmark generate --project-root samples/java-spring-docker --build-tool gradle --java-version 25
springdocker benchmark run --project-root samples/java-spring-docker --build-tool maven --profile quick
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/05-jep483-aot-cache/results/raw.csv
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/05-jep483-aot-cache/results/raw.csv --format json --scenario 05-jep483-aot-cache --variant with-aot-cache
```

## Config file (`.springdocker.toml`)

`springdocker benchmark run` supports config merging with precedence:

1. CLI flags
2. `.springdocker.toml`
3. defaults

Example:

```toml
[project]
build_tool = "maven"

[benchmark]
profile = "quick"
runner_args = ["--skip-native"]
```

Run with config:

```bash
springdocker benchmark run --project-root samples/java-spring-docker
springdocker benchmark run --project-root samples/java-spring-docker --config .springdocker.toml
```

Initialize config:

```bash
springdocker init --project-root samples/java-spring-docker --build-tool gradle
springdocker init --project-root samples/java-spring-docker --build-tool maven --force
```

## Notes

- `springdocker` wraps existing scripts under `<project-root>/tools/` and `<project-root>/benchmarks/`.
- If both `pom.xml` and `gradlew` exist, pass `--build-tool` explicitly.
- Extra arguments can be forwarded:
  - Dockerfile wizard: `--wizard-arg "--profile" --wizard-arg "balanced"`
  - Benchmark runner: `--runner-arg "--skip-native"`

