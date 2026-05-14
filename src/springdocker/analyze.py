from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = {
    "scenario",
    "variant",
    "build_ms",
    "startup_ms",
    "image_bytes",
    "status",
}


@dataclass(frozen=True)
class VariantSummary:
    scenario: str
    variant: str
    runs: int
    build_avg_ms: float | None
    startup_avg_ms: float | None
    startup_p95_ms: float | None
    image_mb_avg: float | None
    success_rate_pct: float


def _to_int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _p95(values: list[int]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    return statistics.quantiles(values, n=20)[18]


def summarize_csv(path: Path, scenario: str | None = None, variant: str | None = None) -> list[VariantSummary]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        rows: list[dict[str, str]] = list(reader)

    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        sc = row.get("scenario", "")
        vr = row.get("variant", "")
        if scenario and sc != scenario:
            continue
        if variant and vr != variant:
            continue
        groups.setdefault((sc, vr), []).append(row)

    summaries: list[VariantSummary] = []
    for (sc, vr), items in sorted(groups.items()):
        build = [v for i in items if (v := _to_int_or_none(i.get("build_ms", ""))) is not None and v >= 0]
        startup = [v for i in items if (v := _to_int_or_none(i.get("startup_ms", ""))) is not None and v >= 0]
        image = [v for i in items if (v := _to_int_or_none(i.get("image_bytes", ""))) is not None and v >= 0]

        ok = sum(1 for i in items if i.get("status") == "ok")
        total = len(items)

        summaries.append(
            VariantSummary(
                scenario=sc,
                variant=vr,
                runs=total,
                build_avg_ms=statistics.mean(build) if build else None,
                startup_avg_ms=statistics.mean(startup) if startup else None,
                startup_p95_ms=_p95(startup),
                image_mb_avg=(statistics.mean(image) / (1024 * 1024)) if image else None,
                success_rate_pct=((ok / total) * 100.0) if total else 0.0,
            )
        )

    return summaries


def format_table(summaries: list[VariantSummary]) -> str:
    lines = [
        "| Scenario | Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB avg | Success rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for s in summaries:
        build_avg = f"{s.build_avg_ms:.1f}" if s.build_avg_ms is not None else "-"
        startup_avg = f"{s.startup_avg_ms:.1f}" if s.startup_avg_ms is not None else "-"
        startup_p95 = f"{s.startup_p95_ms:.1f}" if s.startup_p95_ms is not None else "-"
        image_mb = f"{s.image_mb_avg:.2f}" if s.image_mb_avg is not None else "-"
        lines.append(
            f"| {s.scenario} | {s.variant} | {s.runs} | {build_avg} | {startup_avg} | {startup_p95} | {image_mb} | {s.success_rate_pct:.1f}% |"
        )

    return "\n".join(lines)


def format_json(summaries: list[VariantSummary]) -> str:
    payload = [
        {
            "scenario": s.scenario,
            "variant": s.variant,
            "runs": s.runs,
            "build_avg_ms": s.build_avg_ms,
            "startup_avg_ms": s.startup_avg_ms,
            "startup_p95_ms": s.startup_p95_ms,
            "image_mb_avg": s.image_mb_avg,
            "success_rate_pct": s.success_rate_pct,
        }
        for s in summaries
    ]
    return json.dumps(payload, indent=2, sort_keys=True)

