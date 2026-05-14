# 07-healthcheck-readiness

Compare readiness-based healthcheck vs no Docker healthcheck.

## Variants

- `with-readiness-healthcheck`
- `without-healthcheck`

## Run benchmark

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/07-healthcheck-readiness 10
python3 benchmarks/common/analyze_results.py benchmarks/07-healthcheck-readiness/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
- Build tool: **maven** | Java version: **25**
