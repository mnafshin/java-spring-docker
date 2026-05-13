# 01-base-image-pinning

Compare digest-pinned base images vs floating tags.

## Variants

- `digest-pinned`
- `tag-only`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/01-base-image-pinning 10
python3 benchmarks/common/analyze_results.py benchmarks/01-base-image-pinning/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
