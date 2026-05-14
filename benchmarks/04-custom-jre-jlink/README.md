# 04-custom-jre-jlink

Compare custom jlink/jdeps runtime (Java 25+) vs stock JRE runtime. jdeps uses --multi-release to resolve modules accurately for this JVM version.

## Variants

- `with-jlink-runtime`
- `without-jlink-runtime`

## Run benchmark

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/04-custom-jre-jlink 10
python3 benchmarks/common/analyze_results.py benchmarks/04-custom-jre-jlink/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
- Build tool: **maven** | Java version: **25**
