# Benchmark common tooling

## Files

- `run_scenario.sh`: builds and runs all variants in one scenario and appends metrics to CSV.
- `analyze_results.py`: turns the raw CSV into a markdown summary table.

## Example

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```
