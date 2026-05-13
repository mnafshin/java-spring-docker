# 04-custom-jre-jlink

Compare custom jlink runtime vs stock JRE runtime.

## Variants

- `with-jlink-runtime`
- `without-jlink-runtime`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/04-custom-jre-jlink 10
python3 benchmarks/common/analyze_results.py benchmarks/04-custom-jre-jlink/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
