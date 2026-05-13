# 06-runtime-hardening-non-root-tmp

Compare hardened non-root runtime vs root runtime defaults.

## Variants

- `hardened-non-root`
- `root-runtime`

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/06-runtime-hardening-non-root-tmp 10
python3 benchmarks/common/analyze_results.py benchmarks/06-runtime-hardening-non-root-tmp/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
