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

## Quick usage

```bash
springdocker init --project-root samples/java-spring-docker --build-tool maven --profile quick
springdocker doctor --project-root samples/java-spring-docker
springdocker dockerfile generate --project-root samples/java-spring-docker --output Dockerfile.generated
springdocker benchmark generate --project-root samples/java-spring-docker --java-version 25
springdocker benchmark run --project-root samples/java-spring-docker --profile quick --runner-arg --skip-native
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/05-jep483-aot-cache/results/raw.csv --format table
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/05-jep483-aot-cache/results/raw.csv --format json --output benchmarks/05-jep483-aot-cache/results/summary.json
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/05-jep483-aot-cache/results/raw.csv --fail-on-success-rate-below 95
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
legacy_scripts = false
wizard_args = []

[benchmark.generate]
java_version = 25
legacy_scripts = false

[benchmark.run]
profile = "quick"
runner_args = ["--skip-native"]
legacy_scripts = false
```

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
