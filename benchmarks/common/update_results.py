#!/usr/bin/env python3
import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path('/Users/afshin/IdeaProjects/sandbox/java-spring-docker')
BENCH = ROOT / 'benchmarks'
DEEP = ROOT / 'docs' / 'deep-dives'

SCENARIO_WEIGHTS = {
    "01-base-image-pinning":             (0.1, 0.1, 0.1),
    "02-multi-stage-build-structure":    (0.3, 0.4, 0.3),
    "03-buildkit-gradle-cache":          (0.9, 0.0, 0.1),
    "04-custom-jre-jlink":               (0.1, 0.5, 0.4),
    "05-jep483-aot-cache":               (0.1, 0.1, 0.8),
    "06-runtime-hardening-non-root-tmp": (0.0, 0.0, 0.0),
    "07-healthcheck-readiness":          (0.0, 0.0, 0.0),
    "08-jvm-container-flags":            (0.0, 0.1, 0.9),
    "09-base-image-choice":              (0.2, 0.5, 0.3),
}

ALWAYS_BEST_PRACTICE = {
    "01-base-image-pinning":             "digest-pinned",
    "06-runtime-hardening-non-root-tmp": "hardened-non-root",
    "07-healthcheck-readiness":          "with-readiness-healthcheck",
}

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
        "> **Context:** The AOT cache is architecture-specific and regenerated at build time.\n"
        "> A marginal startup difference here reflects a warm Docker layer cache run.\n"
        "> The benefit is more pronounced at cold JVM start on a fresh container host."
    ),
}


def load_csv(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def variant_stats(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r['variant']].append(r)
    result = []
    for variant, items in groups.items():
        build = [int(r['build_ms']) for r in items if int(r['build_ms']) >= 0]
        startup = [int(r['startup_ms']) for r in items if int(r['startup_ms']) >= 0]
        images = [int(r['image_bytes']) for r in items if int(r['image_bytes']) >= 0]
        ok = sum(1 for r in items if r['status'] == 'ok')
        result.append({
            'variant': variant,
            'runs': len(items),
            'build_avg': statistics.mean(build) if build else None,
            'startup_avg': statistics.mean(startup) if startup else None,
            'startup_p95': statistics.quantiles(startup, n=20)[18] if len(startup) >= 2 else (startup[0] if startup else None),
            'image_mb': statistics.mean(images) / (1024 * 1024) if images else None,
            'success_pct': ok / len(items) * 100,
        })
    return result


def stats_table(vstats):
    lines = [
        "| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for v in sorted(vstats, key=lambda x: x['variant']):
        ba = f"{v['build_avg']:.0f}" if v['build_avg'] is not None else "-"
        sa = f"{v['startup_avg']:.0f}" if v['startup_avg'] is not None else "-"
        sp = f"{v['startup_p95']:.0f}" if v['startup_p95'] is not None else "-"
        im = f"{v['image_mb']:.2f}" if v['image_mb'] is not None else "-"
        sr = f"{v['success_pct']:.1f}%"
        lines.append(f"| {v['variant']} | {v['runs']} | {ba} | {sa} | {sp} | {im} | {sr} |")
    return "\n".join(lines)


def find_winner(vstats, scenario):
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


def write_summary(scenario, vstats, winner, winner_type):
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
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/{scenario} 10
python3 benchmarks/common/recommend.py benchmarks/{scenario}/results/raw.csv
```
""")
    print(f"  summary.md updated: {path}")


def update_deepdive_readme(scenario, vstats, winner, winner_type):
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

    content = readme_path.read_text()
    MARKER = "## Benchmark results"
    if MARKER in content:
        content = content[:content.index(MARKER)] + results_block
    else:
        content = content.rstrip() + "\n\n" + results_block + "\n"

    readme_path.write_text(content)
    print(f"  deep-dive README updated: {readme_path}")


def main():
    for csv_path in sorted(BENCH.glob("*/results/raw.csv")):
        rows = load_csv(csv_path)
        if not rows:
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

