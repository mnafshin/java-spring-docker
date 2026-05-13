# 10 - Native image vs JVM benchmark

This benchmark compares Spring Boot JVM container vs GraalVM native-image container.

## Goals

- cold-start and readiness time
- long-run throughput and tail latency (p95/p99)
- memory and CPU behavior under sustained load
- image size and build time trade-offs

## Variants

- `variants/jvm/Dockerfile`
- `variants/native/Dockerfile`

## Run benchmark (long-run, 60m)

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/10-native-vs-jvm/run_native_vs_jvm.sh --duration 60m --vus 50 --cpu-work 12000
python3 benchmarks/10-native-vs-jvm/analyze_native_vs_jvm.py benchmarks/10-native-vs-jvm/results/raw.csv
```

The analysis command prints a comparison table and refreshes:

- `benchmarks/10-native-vs-jvm/results/summary.md`
- `benchmarks/10-native-vs-jvm/DEEP_DIVE.md` (benchmark deep-dive notes)

## Notes

- Script uses containerized `k6` image (`grafana/k6`) to avoid local install.
- Mixed workload endpoints used by benchmark:
  - `/bench/read`
  - `/bench/cpu?work=12000`
  - `/hello` (periodic)
- On Linux, if `host.docker.internal` is unavailable, keep Docker 20.10+ and the script's `--add-host` mapping.

## Scenario guidance

- **Native better fit**: scale-to-zero, short-lived jobs, low-memory edge workloads.
- **JVM better fit**: long-running throughput-heavy services where warm JIT optimizations dominate.
- **Unknown**: benchmark your own workload; no generic winner exists for all workloads.

