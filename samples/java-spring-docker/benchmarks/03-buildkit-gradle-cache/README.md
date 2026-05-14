# 03-buildkit-gradle-cache

Compare BuildKit maven cache mounts vs no cache mounts in Docker build.

## Variants

- `with-buildkit-maven-cache`
- `without-buildkit-maven-cache`

## Run benchmark

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/03-buildkit-gradle-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/03-buildkit-gradle-cache/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
- Build tool: **maven** | Java version: **25**
