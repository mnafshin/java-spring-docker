# 02-multi-stage-build-structure

Compare specialized multi-stage pipeline vs simpler two-stage pipeline.

## Variants

- `specialized-multi-stage`
- `simple-two-stage`

## Run benchmark

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/02-multi-stage-build-structure 10
python3 benchmarks/common/analyze_results.py benchmarks/02-multi-stage-build-structure/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
- Build tool: **maven** | Java version: **25**
