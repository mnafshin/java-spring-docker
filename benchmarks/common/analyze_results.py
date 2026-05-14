#!/usr/bin/env python3
import statistics
import sys
from collections import defaultdict

from csv_metrics import parse_non_negative_int, percentile_95, read_csv_rows


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: analyze_results.py <raw.csv>")
        return 1

    rows = read_csv_rows(sys.argv[1])
    if not rows:
        print("No rows in input CSV")
        return 0

    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row['scenario'], row['variant'])].append(row)

    print("| Scenario | Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB avg | Success rate |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")

    for (scenario, variant), items in sorted(groups.items()):
        build = [v for item in items if (v := parse_non_negative_int(item.get('build_ms'))) is not None]
        startup = [v for item in items if (v := parse_non_negative_int(item.get('startup_ms'))) is not None]
        image = [v for item in items if (v := parse_non_negative_int(item.get('image_bytes'))) is not None]
        ok = sum(1 for item in items if item['status'] == 'ok')
        total = len(items)

        build_avg = f"{statistics.mean(build):.1f}" if build else "-"
        startup_avg = f"{statistics.mean(startup):.1f}" if startup else "-"
        startup_p95_value = percentile_95(startup)
        startup_p95 = f"{startup_p95_value:.1f}" if startup_p95_value is not None else "-"
        image_mb = f"{(statistics.mean(image) / (1024 * 1024)):.2f}" if image else "-"
        success_rate = f"{(ok / total) * 100:.1f}%" if total else "0.0%"

        print(
            f"| {scenario} | {variant} | {total} | {build_avg} | {startup_avg} | {startup_p95} | {image_mb} | {success_rate} |"
        )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

