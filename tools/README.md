# Dockerfile wizard

Use `tools/dockerfile_wizard.py` to generate a Dockerfile based on your runtime requirements.

## Why

Benchmarks showed that some decisions are policy-driven (always keep) while others are environment-dependent.
This wizard helps you generate a fit-for-purpose Dockerfile without manually editing many blocks.

## Policy defaults you should usually keep

- non-root runtime user
- readiness healthcheck
- digest pinning (where supported in your process)

## Interactive usage

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
python3 tools/dockerfile_wizard.py --interactive --output Dockerfile.generated
```

## Non-interactive usage (example)

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
python3 tools/dockerfile_wizard.py \
  --runtime-base debian-bookworm-slim \
  --buildkit-cache \
  --jlink \
  --non-root \
  --healthcheck \
  --tuned-jvm \
  --output Dockerfile.generated
```

## One-flag profiles

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
python3 tools/dockerfile_wizard.py --profile balanced --output Dockerfile.generated
```

Available profiles:

- `balanced`: default production baseline (debian + buildkit + jlink)
- `smallest`: alpine-focused image size profile
- `enterprise`: ubi9-minimal profile for OpenShift/RHEL contexts
- `simplest`: eclipse-temurin-jre profile (no jlink)
- `coldstart`: balanced + JEP 483 AOT cache

### Override any profile option explicitly

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
python3 tools/dockerfile_wizard.py \
  --profile smallest \
  --runtime-base debian-bookworm-slim \
  --no-jlink \
  --output Dockerfile.generated
```

## Suggested profiles

- **Balanced production**: `debian-bookworm-slim + buildkit-cache + jlink + non-root + healthcheck + tuned-jvm`
- **Smallest image**: `alpine + jlink` (verify musl compatibility in your environment)
- **Enterprise RHEL/OpenShift**: `ubi9-minimal + jlink`
- **Simplest maintenance**: `eclipse-temurin-jre` (no jlink)

## Validate generated output

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
docker build -f Dockerfile.generated -t app:generated .
```

