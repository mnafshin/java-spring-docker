# 09 - Base image choice

Compare how the choice of runtime base OS affects image size, startup time, and build time.

## Current implementation

The production `Dockerfile` uses `debian:bookworm-slim` with a custom jlink JRE.

## Variants

| Variant | Runtime OS | libc | Package manager | Notes |
|---|---|---|---|---|
| `debian-bookworm-slim` | debian:bookworm-slim | glibc | apt-get | Minimal Debian; production baseline |
| `ubuntu-noble` | ubuntu:24.04 | glibc | apt-get | Canonical LTS until 2036 |
| `alpine` | alpine:3.21 | musl | apk | Smallest; requires musl-linked JDK in all stages |
| `eclipse-temurin-jre` | eclipse-temurin:25-jre | glibc | apt-get | Stock JRE (no jlink); useful as size reference |
| `ubi9-minimal` | redhat/ubi9-minimal | glibc | microdnf | Red Hat / OpenShift aligned |

## Key trade-offs

- **Image size**: Alpine produces the smallest image; eclipse-temurin-jre the largest.
- **Startup time**: glibc variants (debian, ubuntu, ubi9) start faster than Alpine (musl JVM overhead).
- **Ecosystem support**: ubi9 for OpenShift/RHEL environments; Ubuntu for Canonical-supported workloads.
- **Complexity**: Alpine requires all build stages to use the `alpine` flavoured JDK image.

## Alpine and musl — important note

Alpine uses **musl libc** instead of glibc.
A jlink JRE built from `eclipse-temurin:25-jdk` (glibc) **cannot run on Alpine**.
The `alpine` variant uses `eclipse-temurin:25-jdk-alpine` for **all stages** (build, jlink, runtime).

## Benchmark strategy

- Fix all other variables (same app, same JVM flags, no AOT cache) — only the runtime base differs.
- Measure image size, startup time, and build time.
- Run at least 5 samples per variant.
- Pull base images fresh before first run.

## Result template

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| alpine | | | | | | |
| debian-bookworm-slim | | | | | | |
| eclipse-temurin-jre | | | | | | |
| ubi9-minimal | | | | | | |
| ubuntu-noble | | | | | | |

## Benchmark results

**Winner:** `ubi9-minimal` — primary metric: **image size**

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| alpine | 6 | 5215 | 1515 | 1733 | 65.90 | 100.0% |
| debian-bookworm-slim | 6 | 1801 | 1422 | 1440 | 90.75 | 100.0% |
| eclipse-temurin-jre | 6 | 1754 | 1532 | 2309 | 134.51 | 100.0% |
| ubi9-minimal | 6 | 850 | 1333 | 1465 | 96.11 | 50.0% |
| ubuntu-noble | 6 | 2834 | 1386 | 1450 | 89.57 | 100.0% |

> **Context:** ubi9-minimal 50% success rate reflects 3 build failures before the
> Dockerfile was fixed. Successful runs are valid. Re-run for a clean baseline.
> Alpine uses musl libc — the build stage must use `eclipse-temurin:25-jdk-alpine`.

