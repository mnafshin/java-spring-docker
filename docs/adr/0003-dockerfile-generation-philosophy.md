# ADR 0003: Dockerfile generation philosophy

## Status

Accepted

## Context

Dockerfile generation must preserve exact output expectations used by snapshots and explainability tests
while remaining easy to maintain.

## Decision

Use a structured in-memory representation for generation, but render the final text with exact line
preservation. Keep the generator opinionated about container-safe defaults and do not add curl-based
Dockerfile healthchecks.

## Consequences

- Output stays stable enough for snapshot and explainability coverage.
- The Dockerfile generator remains deterministic and human-readable.
- Runtime readiness probing stays at the orchestrator/Kubernetes layer instead of the Dockerfile.

