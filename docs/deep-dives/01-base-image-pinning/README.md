# 01 - Base image pinning

## Current implementation

- `FROM eclipse-temurin:25-jdk@sha256:...`
- `FROM debian:bookworm-slim@sha256:...`

## Why this matters

Pinning by digest makes builds reproducible and auditable. You know exactly what bits were used.

## Possible ways

### Option A: tag only (no digest)
- Example: `FROM eclipse-temurin:25-jdk`
- Pros: simpler updates
- Cons: non-deterministic; same Dockerfile can produce different images over time

### Option B: digest pinning (current)
- Example: `FROM eclipse-temurin:25-jdk@sha256:...`
- Pros: deterministic, safer rollback, supply-chain traceability
- Cons: requires explicit digest refresh process

## Benchmark strategy

This point is mainly about reproducibility/security, but can still be measured indirectly.

- Build same commit on 2 different runners
- Compare resulting runtime image digest and SBOM
- Check vulnerability scan diff across time

## Result template

| Date | Runner | Base image mode | Runtime image digest | Notes |
|---|---|---|---|---|
| YYYY-MM-DD | runner-1 | tag-only/pinned | sha256:... | |

## Benchmark results

**Winner:** `digest-pinned` — policy decision (security / reliability)

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| digest-pinned | 5 | 615 | 1269 | 1455 | 103.02 | 100.0% |
| tag-only | 5 | 6581 | 1431 | 1443 | 103.23 | 100.0% |
