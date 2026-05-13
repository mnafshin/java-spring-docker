# 08-jvm-container-flags

Compare tuned JVM flags vs mostly-default JVM startup.

## Variants

- `tuned-flags`
- `defaults-like`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/08-jvm-container-flags 10
python3 benchmarks/common/analyze_results.py benchmarks/08-jvm-container-flags/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
