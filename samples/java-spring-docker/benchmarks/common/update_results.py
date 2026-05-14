#!/usr/bin/env python3
import statistics
from collections import defaultdict
from pathlib import Path

from csv_metrics import parse_non_negative_int, percentile_95, read_csv_rows
from metrics_table import VARIANT_TABLE_HEADER, variant_table_row
from recommendation_policy import ALWAYS_BEST_PRACTICE, SCENARIO_WEIGHTS

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / 'benchmarks'
DEEP = ROOT / 'docs' / 'deep-dives'

SCENARIO_NOTES = {
    "08-jvm-container-flags": (
        "> **Context:** On a developer machine with ample RAM the tuned flags may show marginal\n"
        "> extra overhead from ZGC initialization. The real benefit appears under memory-constrained\n"
        "> containers (e.g. 256 Mi limit) where `MaxRAMPercentage=75` prevents heap over-allocation\n"
        "> and `-XX:+ExitOnOutOfMemoryError` enables fast pod restart."
    ),
    "09-base-image-choice": (
        "> **Context:** ubi9-minimal 50% success rate reflects 3 build failures before the\n"
        "> Dockerfile was fixed. Successful runs are valid. Re-run for a clean baseline.\n"
        "> Alpine uses musl libc — the build stage must use `eclipse-temurin:25-jdk-alpine`."
    ),
    "05-jep483-aot-cache": (
        "> **Context:** This scenario is now the canonical complex-app AOT benchmark.\n"
        "> Use at least 15 runs (`--profile full`) for stable startup deltas.\n"
        "> Compare startup gain against added build complexity before rollout."
    ),
    "10-native-vs-jvm": (
        "> **Context:** Native typically wins on cold start and memory footprint, while JVM can\n"
        "> win on long-run throughput due to JIT optimization. Use your 60-minute run results\n"
        "> and endpoint mix to decide per service, not globally."
    ),
}


def load_csv(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def variant_stats(rows: list[dict[str, str]]) -> list[dict[str, float | int | str | None]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[r['variant']].append(r)
    result: list[dict[str, float | int | str | None]] = []
    for variant, items in groups.items():
        build = [value for r in items if (value := parse_non_negative_int(r.get('build_ms'))) is not None]
        startup = [value for r in items if (value := parse_non_negative_int(r.get('startup_ms'))) is not None]
        images = [value for r in items if (value := parse_non_negative_int(r.get('image_bytes'))) is not None]
        ok = sum(1 for r in items if r['status'] == 'ok')
        startup_p95 = percentile_95(startup)
        result.append({
            'variant': variant,
            'runs': len(items),
            'build_avg': statistics.mean(build) if build else None,
            'startup_avg': statistics.mean(startup) if startup else None,
            'startup_p95': startup_p95,
            'image_mb': statistics.mean(images) / (1024 * 1024) if images else None,
            'success_pct': ok / len(items) * 100,
        })
    return result


def stats_table(vstats: list[dict[str, float | int | str | None]]) -> str:
    lines = list(VARIANT_TABLE_HEADER)
    for v in sorted(vstats, key=lambda x: x['variant']):
        lines.append(
            variant_table_row(
                variant=str(v['variant']),
                runs=int(v['runs']),
                build_avg=v['build_avg'],
                startup_avg=v['startup_avg'],
                startup_p95=v['startup_p95'],
                image_mb=v['image_mb'],
                success_pct=float(v['success_pct']),
            )
        )
    return "\n".join(lines)


def find_winner(vstats: list[dict[str, float | int | str | None]], scenario: str) -> tuple[str, str]:
    if scenario in ALWAYS_BEST_PRACTICE:
        return ALWAYS_BEST_PRACTICE[scenario], "policy"

    w_build, w_image, w_startup = SCENARIO_WEIGHTS.get(scenario, (0.33, 0.33, 0.33))
    builds = [v['build_avg'] for v in vstats if v['build_avg'] is not None]
    images = [v['image_mb'] for v in vstats if v['image_mb'] is not None]
    starts = [v['startup_avg'] for v in vstats if v['startup_avg'] is not None]

    def norm(val, vals):
        lo, hi = min(vals), max(vals)
        return 0.0 if hi == lo else (val - lo) / (hi - lo)

    scores = {}
    for v in vstats:
        s = 0.0
        if builds and v['build_avg'] is not None:
            s += w_build * norm(v['build_avg'], builds)
        if images and v['image_mb'] is not None:
            s += w_image * norm(v['image_mb'], images)
        if starts and v['startup_avg'] is not None:
            s += w_startup * norm(v['startup_avg'], starts)
        scores[v['variant']] = s

    winner = min(scores, key=scores.get)
    return winner, "metric"


def write_summary(scenario: str, vstats: list[dict[str, float | int | str | None]], winner: str, winner_type: str) -> None:
    table = stats_table(vstats)
    notes = SCENARIO_NOTES.get(scenario, "")
    notes_block = f"\n{notes}\n" if notes else ""

    if winner_type == "policy":
        decision = f"✅ **Recommended:** `{winner}` — policy decision (security / reliability, not metric-driven)"
    else:
        w_build, w_image, w_startup = SCENARIO_WEIGHTS.get(scenario, (0.33, 0.33, 0.33))
        primary = max([("build time", w_build), ("image size", w_image), ("startup time", w_startup)], key=lambda x: x[1])
        decision = f"✅ **Recommended:** `{winner}` — metric-driven (primary weight: **{primary[0]}**)"

    path = BENCH / scenario / 'results' / 'summary.md'
    path.write_text(f"""# Results summary: {scenario}

## Recommendation

{decision}

## Results table

{table}
{notes_block}
## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/{scenario} 10
python3 benchmarks/common/recommend.py benchmarks/{scenario}/results/raw.csv
```
""", encoding='utf-8')
    print(f"  summary.md updated: {path}")


def update_deepdive_readme(scenario: str, vstats: list[dict[str, float | int | str | None]], winner: str, winner_type: str) -> None:
    readme_path = DEEP / scenario / 'README.md'
    if not readme_path.exists():
        return

    table = stats_table(vstats)
    notes = SCENARIO_NOTES.get(scenario, "")
    notes_block = f"\n{notes}\n" if notes else ""

    if winner_type == "policy":
        rec_line = f"**Winner:** `{winner}` — policy decision (security / reliability)"
    else:
        w_build, w_image, w_startup = SCENARIO_WEIGHTS.get(scenario, (0.33, 0.33, 0.33))
        primary = max([("build time", w_build), ("image size", w_image), ("startup time", w_startup)], key=lambda x: x[1])
        rec_line = f"**Winner:** `{winner}` — primary metric: **{primary[0]}**"

    results_block = f"""## Benchmark results

{rec_line}

{table}
{notes_block}"""

    content = readme_path.read_text(encoding='utf-8')
    MARKER = "## Benchmark results"
    if MARKER in content:
        content = content[:content.index(MARKER)] + results_block
    else:
        content = content.rstrip() + "\n\n" + results_block + "\n"

    readme_path.write_text(content, encoding='utf-8')
    print(f"  deep-dive README updated: {readme_path}")


def main():
    for csv_path in sorted(BENCH.glob("*/results/raw.csv")):
        rows = load_csv(csv_path)
        if not rows:
            continue
        if 'image_bytes' not in rows[0] and 'image_mb' in rows[0]:
            for row in rows:
                image_mb = row.get('image_mb', '-1')
                if image_mb in ('', '-1', None):
                    row['image_bytes'] = '-1'
                else:
                    row['image_bytes'] = str(int(float(image_mb) * 1024 * 1024))
        required = {'variant', 'build_ms', 'startup_ms', 'image_bytes', 'status'}
        if not required.issubset(rows[0].keys()):
            missing = ", ".join(sorted(required - set(rows[0].keys())))
            print(f"\n[{csv_path.parent.parent.name}] skipped: unsupported schema (missing: {missing})")
            continue
        scenario = csv_path.parent.parent.name
        vstats = variant_stats(rows)
        winner, wtype = find_winner(vstats, scenario)
        print(f"\n[{scenario}] winner={winner} ({wtype})")
        write_summary(scenario, vstats, winner, wtype)
        update_deepdive_readme(scenario, vstats, winner, wtype)

    print("\nDone.")


if __name__ == '__main__':
    main()

