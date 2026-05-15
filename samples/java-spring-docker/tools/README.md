# Dockerfile wizard

Use `tools/dockerfile_wizard.py` to generate a Dockerfile based on your runtime requirements.

## Why

Benchmarks showed that some decisions are policy-driven (always keep) while others are environment-dependent.
This wizard helps you generate a fit-for-purpose Dockerfile without manually editing many blocks.

## Policy defaults you should usually keep

- non-root runtime user
- digest pinning (where supported in your process)

## Interactive usage

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py --interactive --output Dockerfile.generated
```

## Non-interactive usage (example)

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py \
  --runtime-base debian-bookworm-slim \
  --buildkit-cache \
  --jlink \
  --non-root \
  --tuned-jvm \
  --output Dockerfile.generated
```

## Portability flags (for non-default project layouts)

- `--source-dir`: source tree copied in build stage (default `src`)
- `--jar-glob`: built JAR path glob in builder image (defaults: Gradle `build/libs/*-SNAPSHOT.jar`, Maven `target/*.jar`)
- `--native-bin-path`: native executable path in builder image (overrides build-tool default)
- `--app-port`: app container port to expose (default `8080`)
- `--management-port`: optional management port to expose (default `8081`)

Example:

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py \
  --profile balanced \
  --build-tool maven \
  --source-dir service/src \
  --jar-glob 'target/*.jar' \
  --app-port 9000 \
  --management-port 9001 \
  --output Dockerfile.generated
```

## One-flag profiles

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py --profile balanced --output Dockerfile.generated
```

Available profiles:

- `balanced`: default production baseline (debian + buildkit + jlink)
- `smallest`: alpine-focused image size profile
- `enterprise`: ubi9-minimal profile for OpenShift/RHEL contexts
- `simplest`: eclipse-temurin-jre profile (no jlink)
- `coldstart`: balanced + JEP 483 AOT cache
- `native`: native-image container build/run path

### Override any profile option explicitly

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py \
  --profile smallest \
  --runtime-base debian-bookworm-slim \
  --no-jlink \
  --output Dockerfile.generated
```

### Generate native-image Dockerfile

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py --profile native --output Dockerfile.generated
```

or explicitly:

```bash
cd /path/to/your-java25-project
python3 tools/dockerfile_wizard.py --profile balanced --native-image --output Dockerfile.generated
```

## Suggested profiles

- **Balanced production**: `debian-bookworm-slim + buildkit-cache + jlink + non-root + tuned-jvm`
- **Smallest image**: `alpine + jlink` (verify musl compatibility in your environment)
- **Enterprise RHEL/OpenShift**: `ubi9-minimal + jlink`
- **Simplest maintenance**: `eclipse-temurin-jre` (no jlink)

## Validate generated output

```bash
cd /path/to/your-java25-project
docker build -f Dockerfile.generated -t app:generated .
```
