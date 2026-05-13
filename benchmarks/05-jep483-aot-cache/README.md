# 05-jep483-aot-cache (canonical complex-app scenario)

Compare startup with and without JEP 483 runtime cache on the production-like Spring application used in this repository.

## Variants

- `with-aot-cache`
- `without-aot-cache`
- `minimal-app`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 15
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

## Notes

- This is the primary AOT benchmark for decision-making and presentations.
- Keep environment stable across runs (CPU, memory, Docker version).
- Use at least 15 samples per variant for stable comparison.

