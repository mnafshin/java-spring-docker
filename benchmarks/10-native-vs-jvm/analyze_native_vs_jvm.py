#!/usr/bin/env python3
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_MD = ROOT / 'benchmarks' / '10-native-vs-jvm' / 'results' / 'summary.md'
DEEP_DIVE_MD = ROOT / 'docs' / 'deep-dives' / '10-native-vs-jvm' / 'README.md'


def usage() -> None:
    print('Usage: analyze_native_vs_jvm.py <raw.csv>')


def load_rows(path: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r.get('status') == 'ok':
                rows.append(r)
    return rows


def _parse_float(value: str | None) -> float | None:
    if value in ('', '-1', None):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def avg(items: list[dict[str, str]], field: str) -> float:
    vals = [value for x in items if (value := _parse_float(x.get(field))) is not None]
    return statistics.mean(vals) if vals else -1.0


def avg_image_mb(items: list[dict[str, str]]) -> float:
    values: list[float] = []
    for row in items:
        image_mb = _parse_float(row.get('image_mb'))
        image_bytes = _parse_float(row.get('image_bytes'))
        if image_mb is not None:
            values.append(image_mb)
        elif image_bytes is not None:
            values.append(image_bytes / (1024 * 1024))
    return statistics.mean(values) if values else -1.0


def build_variant_stats(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    by_variant: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        by_variant[r['variant']].append(r)

    stats: dict[str, dict[str, float]] = {}
    for variant, items in by_variant.items():
        stats[variant] = {
            'runs': float(len(items)),
            'build_ms': avg(items, 'build_ms'),
            'image_mb': avg_image_mb(items),
            'startup_ms': avg(items, 'startup_ms'),
            'rps': avg(items, 'rps'),
            'p95_ms': avg(items, 'p95_ms'),
            'p99_ms': avg(items, 'p99_ms'),
            'cpu_pct': avg(items, 'cpu_pct'),
            'memory_mb': avg(items, 'memory_mb'),
        }
    return stats


def render_table(stats: dict[str, dict[str, float]]) -> str:
    lines = [
        '| Variant | Runs | Build ms avg | Image MB avg | Startup ms avg | RPS avg | p95 ms avg | p99 ms avg | CPU % avg | Mem MB avg |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for variant in sorted(stats):
        s = stats[variant]
        lines.append(
            f"| {variant} | {int(s['runs'])} | {s['build_ms']:.1f} | {s['image_mb']:.2f} | {s['startup_ms']:.1f} | "
            f"{s['rps']:.2f} | {s['p95_ms']:.2f} | {s['p99_ms']:.2f} | {s['cpu_pct']:.2f} | {s['memory_mb']:.2f} |"
        )
    return '\n'.join(lines)


def recommendation(stats: dict[str, dict[str, float]]) -> str:
    if 'jvm' not in stats or 'native' not in stats:
        return 'Need both `jvm` and `native` rows to generate a recommendation.'

    jvm = stats['jvm']
    native = stats['native']
    startup_gain = jvm['startup_ms'] - native['startup_ms']
    mem_gain = jvm['memory_mb'] - native['memory_mb']
    rps_gain = jvm['rps'] - native['rps']

    if startup_gain > 200 and mem_gain > 10 and rps_gain >= -0.05 * max(jvm['rps'], 1.0):
        return 'Prefer `native` when cold-start and memory efficiency matter most for this workload.'
    if rps_gain > 0.05 * max(native['rps'], 1.0):
        return 'Prefer `jvm` when sustained throughput is the primary goal.'
    return 'No universal winner: choose `native` for startup/memory priorities, `jvm` for steady-state throughput and tooling simplicity.'


def write_benchmark_summary(table: str, decision: str) -> None:
    SUMMARY_MD.write_text(
        f"""# Results summary: 10-native-vs-jvm

## Recommendation

{decision}

## Results table

{table}

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/10-native-vs-jvm/run_native_vs_jvm.sh --duration 60m --vus 50 --cpu-work 12000
python3 benchmarks/10-native-vs-jvm/analyze_native_vs_jvm.py benchmarks/10-native-vs-jvm/results/raw.csv
```
""",
        encoding='utf-8',
    )
    print(f'Updated markdown: {SUMMARY_MD}')


def write_deep_dive_results(table: str, decision: str) -> None:
    if not DEEP_DIVE_MD.exists():
        return

    results_block = (
        '## Benchmark results\n\n'
        f'**Recommendation:** {decision}\n\n'
        f'{table}\n\n'
        '- Prefer native when startup and memory are top priorities (cold starts, scale-to-zero, short-lived workloads).\n'
        '- Prefer JVM when peak throughput and mature runtime tooling are top priorities (long-lived services).\n'
        '- Validate with your own 60m runs and representative endpoint mix before standardizing.\n'
    )

    content = DEEP_DIVE_MD.read_text(encoding='utf-8')
    marker = '## Benchmark results'
    if marker in content:
        content = content[:content.index(marker)] + results_block
    else:
        content = content.rstrip() + '\n\n' + results_block
    DEEP_DIVE_MD.write_text(content, encoding='utf-8')
    print(f'Updated markdown: {DEEP_DIVE_MD}')


def main() -> None:
    if len(sys.argv) != 2:
        usage()
        raise SystemExit(1)

    path = sys.argv[1]
    rows = load_rows(path)
    if not rows:
        print('No successful rows found.')
        raise SystemExit(0)

    stats = build_variant_stats(rows)
    table = render_table(stats)
    decision = recommendation(stats)

    print(table)
    print('\n## Decision hints')
    print(f'- {decision}')
    print('- Prefer native when startup and memory are top priorities (cold starts, scale-to-zero, short-lived workloads).')
    print('- Prefer JVM when peak throughput and mature runtime tooling are top priorities (long-lived high-throughput services).')
    print('- Validate with your own 60m runs and representative endpoint mix before standardizing.')

    write_benchmark_summary(table, decision)
    write_deep_dive_results(table, decision)


if __name__ == '__main__':
    main()

