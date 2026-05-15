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
OPTIONAL_COLUMNS = {"rss_bytes", "cpu_pct", "host", "docker_version", "run_profile"}


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
    rss_mb_avg: float | None = None
    cpu_pct_avg: float | None = None
    host: str | None = None
    docker_version: str | None = None
    run_profile: str | None = None


def _to_int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float_or_none(value: str) -> float | None:
    try:
        return float(value)
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
        rss: list[int] = []
        for item in items:
            rss_value = _to_int_or_none(item.get("rss_bytes", ""))
            if rss_value is not None and rss_value >= 0:
                rss.append(rss_value)

        cpu: list[float] = []
        for item in items:
            cpu_value = _to_float_or_none(item.get("cpu_pct", ""))
            if cpu_value is not None and cpu_value >= 0.0:
                cpu.append(cpu_value)

        ok = sum(1 for i in items if i.get("status") == "ok")
        total = len(items)
        first = items[0] if items else {}

        summaries.append(
            VariantSummary(
                scenario=sc,
                variant=vr,
                runs=total,
                build_avg_ms=statistics.mean(build) if build else None,
                startup_avg_ms=statistics.mean(startup) if startup else None,
                startup_p95_ms=_p95(startup),
                image_mb_avg=(statistics.mean(image) / (1024 * 1024)) if image else None,
                rss_mb_avg=(statistics.mean(rss) / (1024 * 1024)) if rss else None,
                cpu_pct_avg=statistics.mean(cpu) if cpu else None,
                success_rate_pct=((ok / total) * 100.0) if total else 0.0,
                host=first.get("host") or None,
                docker_version=first.get("docker_version") or None,
                run_profile=first.get("run_profile") or None,
            )
        )

    return summaries


def format_table(summaries: list[VariantSummary]) -> str:
    lines = [
        "| Scenario | Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB avg | RSS MB avg | CPU avg (%) | Success rate | Host | Docker | Profile |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]

    for s in summaries:
        build_avg = f"{s.build_avg_ms:.1f}" if s.build_avg_ms is not None else "-"
        startup_avg = f"{s.startup_avg_ms:.1f}" if s.startup_avg_ms is not None else "-"
        startup_p95 = f"{s.startup_p95_ms:.1f}" if s.startup_p95_ms is not None else "-"
        image_mb = f"{s.image_mb_avg:.2f}" if s.image_mb_avg is not None else "-"
        rss_mb = f"{s.rss_mb_avg:.2f}" if s.rss_mb_avg is not None else "-"
        cpu_pct = f"{s.cpu_pct_avg:.1f}" if s.cpu_pct_avg is not None else "-"
        lines.append(
            f"| {s.scenario} | {s.variant} | {s.runs} | {build_avg} | {startup_avg} | {startup_p95} | "
            f"{image_mb} | {rss_mb} | {cpu_pct} | {s.success_rate_pct:.1f}% | "
            f"{s.host or '-'} | {s.docker_version or '-'} | {s.run_profile or '-'} |"
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
            "rss_mb_avg": s.rss_mb_avg,
            "cpu_pct_avg": s.cpu_pct_avg,
            "success_rate_pct": s.success_rate_pct,
            "host": s.host,
            "docker_version": s.docker_version,
            "run_profile": s.run_profile,
        }
        for s in summaries
    ]
    return json.dumps(payload, indent=2, sort_keys=True)
