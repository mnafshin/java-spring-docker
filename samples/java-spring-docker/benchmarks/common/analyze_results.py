#!/usr/bin/env python3
import csv
import statistics
import sys
from collections import defaultdict

if len(sys.argv) != 2:
    print("Usage: analyze_results.py <raw.csv>")
    sys.exit(1)

path = sys.argv[1]
rows = []
with open(path, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

if not rows:
    print("No rows in input CSV")
    sys.exit(0)

groups = defaultdict(list)
for row in rows:
    groups[(row['scenario'], row['variant'])].append(row)

print("| Scenario | Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB avg | Success rate |")
print("|---|---|---:|---:|---:|---:|---:|---:|")

for (scenario, variant), items in sorted(groups.items()):
    build = [int(i['build_ms']) for i in items if int(i['build_ms']) >= 0]
    startup = [int(i['startup_ms']) for i in items if int(i['startup_ms']) >= 0]
    image = [int(i['image_bytes']) for i in items if int(i['image_bytes']) >= 0]
    ok = sum(1 for i in items if i['status'] == 'ok')
    total = len(items)

    build_avg = f"{statistics.mean(build):.1f}" if build else "-"
    startup_avg = f"{statistics.mean(startup):.1f}" if startup else "-"
    if len(startup) >= 2:
        p95 = statistics.quantiles(startup, n=20)[18]
        startup_p95 = f"{p95:.1f}"
    elif len(startup) == 1:
        startup_p95 = str(startup[0])
    else:
        startup_p95 = "-"
    image_mb = f"{(statistics.mean(image) / (1024 * 1024)):.2f}" if image else "-"
    success_rate = f"{(ok / total) * 100:.1f}%" if total else "0.0%"

    print(
        f"| {scenario} | {variant} | {total} | {build_avg} | {startup_avg} | {startup_p95} | {image_mb} | {success_rate} |"
    )
