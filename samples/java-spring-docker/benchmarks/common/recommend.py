#!/usr/bin/env python3
"""
recommend.py  –  reads a raw.csv and emits a winner + recommendation per scenario.

Usage:
    python3 benchmarks/common/recommend.py benchmarks/05-jep483-aot-cache/results/raw.csv
    # or aggregate all scenarios at once:
    python3 benchmarks/common/recommend.py benchmarks/*/results/raw.csv
"""

import csv
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from csv_metrics import parse_non_negative_int
from metrics_table import VARIANT_TABLE_HEADER, variant_table_row
from recommendation_policy import ALWAYS_BEST_PRACTICE, SCENARIO_WEIGHTS


@dataclass
class VariantStats:
    scenario: str
    variant: str
    runs: int = 0
    build_times: list[float] = field(default_factory=list)
    startup_times: list[float] = field(default_factory=list)
    image_sizes: list[float] = field(default_factory=list)
    ok: int = 0

    @property
    def build_avg(self) -> float:
        return statistics.mean(self.build_times) if self.build_times else float("inf")

    @property
    def startup_avg(self) -> float:
        return statistics.mean(self.startup_times) if self.startup_times else float("inf")

    @property
    def startup_p95(self) -> float:
        if len(self.startup_times) >= 2:
            return statistics.quantiles(self.startup_times, n=20)[18]
        return self.startup_times[0] if self.startup_times else float("inf")

    @property
    def image_mb_avg(self) -> float:
        if self.image_sizes:
            return statistics.mean(self.image_sizes) / (1024 * 1024)
        return float("inf")

    @property
    def success_rate(self) -> float:
        return (self.ok / self.runs * 100) if self.runs else 0.0


def load_csv(path: str) -> dict[tuple[str, str], VariantStats]:
    groups: dict[tuple[str, str], VariantStats] = defaultdict(lambda: VariantStats("", ""))
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["scenario"], row["variant"])
            s = groups[key]
            s.scenario = row["scenario"]
            s.variant = row["variant"]
            s.runs += 1
            build_ms = parse_non_negative_int(row.get("build_ms"))
            startup_ms = parse_non_negative_int(row.get("startup_ms"))
            image_bytes = parse_non_negative_int(row.get("image_bytes"))
            if build_ms is not None and build_ms >= 0:
                s.build_times.append(build_ms)
            if startup_ms is not None and startup_ms >= 0:
                s.startup_times.append(startup_ms)
            if image_bytes is not None and image_bytes >= 0:
                s.image_sizes.append(image_bytes)
            if row["status"] == "ok":
                s.ok += 1
    return groups



def _merge_stats(dest: VariantStats, src: VariantStats) -> None:
    dest.scenario = src.scenario
    dest.variant = src.variant
    dest.runs += src.runs
    dest.build_times.extend(src.build_times)
    dest.startup_times.extend(src.startup_times)
    dest.image_sizes.extend(src.image_sizes)
    dest.ok += src.ok


def score(stats: VariantStats, all_stats: list[VariantStats]) -> float:
    """
    Normalised score in [0, 1] – lower metric = better normalised value.
    """
    w_build, w_image, w_startup = SCENARIO_WEIGHTS.get(stats.scenario, (0.33, 0.33, 0.33))

    def normalise(value: float, values: list[float]) -> float:
        lo, hi = min(values), max(values)
        if hi == lo:
            return 0.0
        return (value - lo) / (hi - lo)  # 0 = best (lowest), 1 = worst

    builds = [s.build_avg for s in all_stats if s.build_times]
    images = [s.image_mb_avg for s in all_stats if s.image_sizes]
    startups = [s.startup_avg for s in all_stats if s.startup_times]

    s = 0.0
    if builds and stats.build_times:
        s += w_build * normalise(stats.build_avg, builds)
    if images and stats.image_sizes:
        s += w_image * normalise(stats.image_mb_avg, images)
    if startups and stats.startup_times:
        s += w_startup * normalise(stats.startup_avg, startups)
    return s  # lower = better


def recommend(groups: dict[tuple[str, str], VariantStats]) -> None:
    # Group by scenario
    by_scenario: dict[str, list[VariantStats]] = defaultdict(list)
    for s in groups.values():
        by_scenario[s.scenario].append(s)

    print("# Benchmark recommendations\n")

    for scenario, variants in sorted(by_scenario.items()):
        print(f"## {scenario}\n")

        # Always-best-practice override
        if scenario in ALWAYS_BEST_PRACTICE:
            preferred = ALWAYS_BEST_PRACTICE[scenario]
            print(
                f"**Decision type:** security / reliability policy\n\n"
                f"**Recommended variant:** `{preferred}`\n\n"
                f"> This scenario is not decided by raw metrics. "
                f"The `{preferred}` variant is the best practice regardless of numbers.\n"
            )
            _print_table(variants)
            print()
            continue

        # Skip if no data yet
        if all(v.runs == 0 for v in variants):
            print("_No benchmark data yet. Run the scenario first._\n")
            continue

        failed = [v for v in variants if v.success_rate < 100]
        if failed:
            failed_names = ", ".join(f"`{v.variant}`" for v in failed)
            print(f"> ⚠️  Variants with failures: {failed_names}.\n")

        scored = sorted(variants, key=lambda v: score(v, variants))

        winner = scored[0]
        w_build, w_image, w_startup = SCENARIO_WEIGHTS.get(scenario, (0.33, 0.33, 0.33))
        dominant = max(
            [("build time", w_build), ("image size", w_image), ("startup time", w_startup)],
            key=lambda x: x[1],
        )
        print(
            f"**Decision type:** metric-driven (primary metric: **{dominant[0]}**)\n\n"
            f"**Recommended variant:** `{winner.variant}`\n"
        )

        if len(scored) > 1:
            runner = scored[1]
            delta_startup = winner.startup_avg - runner.startup_avg
            delta_build = winner.build_avg - runner.build_avg
            delta_image = winner.image_mb_avg - runner.image_mb_avg

            improvements = []
            if abs(delta_startup) > 20:
                sign = "faster" if delta_startup < 0 else "slower"
                improvements.append(f"startup {abs(delta_startup):.0f} ms {sign} than `{runner.variant}`")
            if abs(delta_build) > 500:
                sign = "faster" if delta_build < 0 else "slower"
                improvements.append(f"build {abs(delta_build):.0f} ms {sign} than `{runner.variant}`")
            if abs(delta_image) > 0.5:
                sign = "smaller" if delta_image < 0 else "larger"
                improvements.append(f"image {abs(delta_image):.1f} MB {sign} than `{runner.variant}`")

            if improvements:
                print("> " + "; ".join(improvements) + ".\n")

        _print_table(variants)
        print()


def _print_table(variants: list[VariantStats]) -> None:
    print(VARIANT_TABLE_HEADER[0])
    print(VARIANT_TABLE_HEADER[1])
    for v in sorted(variants, key=lambda x: x.variant):
        print(
            variant_table_row(
                variant=v.variant,
                runs=v.runs,
                build_avg=v.build_avg if v.build_times else None,
                startup_avg=v.startup_avg if v.startup_times else None,
                startup_p95=v.startup_p95 if v.startup_times else None,
                image_mb=v.image_mb_avg if v.image_sizes else None,
                success_pct=v.success_rate,
            )
        )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: recommend.py <raw.csv> [raw.csv ...]")
        sys.exit(1)

    all_groups: dict[tuple[str, str], VariantStats] = defaultdict(lambda: VariantStats("", ""))
    for path in sys.argv[1:]:
        loaded = load_csv(path)
        for key, stats in loaded.items():
            _merge_stats(all_groups[key], stats)

    if not all_groups:
        print("No data found in provided CSV files.")
        sys.exit(0)

    recommend(dict(all_groups))


if __name__ == "__main__":
    main()

