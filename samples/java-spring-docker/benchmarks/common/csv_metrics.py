#!/usr/bin/env python3
"""Shared CSV parsing helpers for benchmark analysis scripts."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    rows: list[dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as file_obj:
        for row in csv.DictReader(file_obj):
            rows.append(row)
    return rows


def parse_non_negative_int(value: str | None) -> int | None:
    if value in (None, "", "-1"):
        return None
    try:
        parsed = int(value)
        return parsed if parsed >= 0 else None
    except ValueError:
        return None


def parse_non_negative_float(value: str | None) -> float | None:
    if value in (None, "", "-1"):
        return None
    try:
        parsed = float(value)
        return parsed if parsed >= 0 else None
    except ValueError:
        return None


def percentile_95(values: list[int] | list[float]) -> float | None:
    if len(values) >= 2:
        return statistics.quantiles(values, n=20)[18]
    if len(values) == 1:
        return float(values[0])
    return None

