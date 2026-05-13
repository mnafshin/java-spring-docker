# 05-jep483-aot-cache

Compare startup with and without JEP 483 runtime cache usage.

## Variants

- `with-aot-cache`
- `without-aot-cache`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
