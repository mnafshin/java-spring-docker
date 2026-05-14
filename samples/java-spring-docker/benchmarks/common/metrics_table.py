#!/usr/bin/env python3
"""Shared markdown table helpers for benchmark variant metrics."""

from __future__ import annotations

VARIANT_TABLE_HEADER = [
    "| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |",
    "|---|---:|---:|---:|---:|---:|---:|",
]


def format_optional_metric(value: float | int | None, decimals: int) -> str:
    if value is None:
        return "-"
    return f"{value:.{decimals}f}"


def format_success_pct(success_pct: float) -> str:
    return f"{success_pct:.1f}%"


def variant_table_row(
    *,
    variant: str,
    runs: int,
    build_avg: float | int | None,
    startup_avg: float | int | None,
    startup_p95: float | int | None,
    image_mb: float | int | None,
    success_pct: float,
) -> str:
    ba = format_optional_metric(build_avg, 0)
    sa = format_optional_metric(startup_avg, 0)
    sp = format_optional_metric(startup_p95, 0)
    im = format_optional_metric(image_mb, 2)
    sr = format_success_pct(success_pct)
    return f"| {variant} | {runs} | {ba} | {sa} | {sp} | {im} | {sr} |"

