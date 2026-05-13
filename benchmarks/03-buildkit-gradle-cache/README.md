# 03-buildkit-gradle-cache

Compare BuildKit cache mounts vs no cache mounts in Docker build.

## Variants

- `with-buildkit-cache`
- `without-buildkit-cache`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/03-buildkit-gradle-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/03-buildkit-gradle-cache/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
