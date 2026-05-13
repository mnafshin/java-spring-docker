# 09 - Base image choice

Compare how the choice of runtime base OS image affects image size, startup time, and build time.

## Variants

| Variant | Runtime base | libc | Package manager | Notes |
|---|---|---|---|---|
| `debian-bookworm-slim` | debian:bookworm-slim | glibc | apt-get | Current production baseline; minimal Debian |
| `ubuntu-noble` | ubuntu:24.04 | glibc | apt-get | Canonical LTS, supported until 2036 |
| `alpine` | alpine:3.21 | musl | apk | Smallest base; build must use alpine-flavoured JDK |
| `eclipse-temurin-jre` | eclipse-temurin:25-jre | glibc | apt-get | Stock JRE, no jlink – reference for jlink overhead |
| `ubi9-minimal` | redhat/ubi9-minimal | glibc | microdnf | Red Hat / OpenShift aligned |

## Key trade-offs to measure

- **Image size**: which base OS leaves the smallest runtime image?
- **Startup time**: does the OS or libc variant affect JVM startup latency?
- **Build time**: how does rebuilding the JDK alignment stage affect CI time?
- **Ecosystem fit**: CVE scan surface, enterprise support, OS tooling compatibility

## Important: Alpine and musl

Alpine uses **musl libc** instead of glibc.
A JRE built on a glibc-based JDK (e.g. normal eclipse-temurin) **cannot run on Alpine**.
The `alpine` variant uses `eclipse-temurin:25-jdk-alpine` for both build and jlink stages.
This is the correct approach, but adds a separate build lineage for that variant.

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/09-base-image-choice 10
python3 benchmarks/common/analyze_results.py benchmarks/09-base-image-choice/results/raw.csv
python3 benchmarks/common/recommend.py benchmarks/09-base-image-choice/results/raw.csv
```

## Notes

- Run on the same machine class and Docker version across all benchmarks.
- Pull all base images fresh before the first run to normalize pull-time bias.
- Run at least 10 samples per variant for startup metrics.
- Separate concerns: this scenario changes only the runtime base image.

