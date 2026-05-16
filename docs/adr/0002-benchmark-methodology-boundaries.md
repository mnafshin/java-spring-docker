# ADR 0002: Benchmark methodology boundaries

## Status

Accepted

## Context

`springdocker` benchmark features are focused on reproducible Docker-based comparisons and report
aggregation. The project also documents optional profiling columns, but it does not own JVM profiling
agents or cluster-level metrics ingestion.

## Decision

Keep the benchmark runner centered on deterministic Docker runs and CSV generation. Treat advanced
profiling fields as optional inputs in the analyzer rather than mandatory runtime dependencies.

## Consequences

- The CLI stays simple and portable across local and CI environments.
- Optional GC/allocation/startup-phase data can be ingested when another tool provides it.
- Benchmark regressions remain tied to the same CSV and JSON summary model.

