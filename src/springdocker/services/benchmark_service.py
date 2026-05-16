from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..analyze import format_json, format_table, summarize_csv
from ..compare import compare_summaries, format_delta_json, format_delta_table
from ..regression import RegressionViolation, detect_regressions, load_summaries


def resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = project_root / path
    return path


def validate_reproducibility_with_legacy(
    use_legacy_scripts: bool,
    cpuset_cpus: str | None,
    memory_limit: str | None,
    warmup_runs: int,
    normalized_runtime: bool,
) -> None:
    if use_legacy_scripts and any([cpuset_cpus, memory_limit, warmup_runs > 0, normalized_runtime]):
        raise ValueError("benchmark reproducibility controls require the internal benchmark runner")


def render_comparison(
    project_root: Path,
    raw_csv: str,
    baseline_variant: str,
    output_format: str,
    scenario: str | None,
) -> str:
    csv_path = resolve_path(project_root, raw_csv)
    if not csv_path.exists():
        raise ValueError(f"missing CSV file: {csv_path}")
    summaries = summarize_csv(csv_path, scenario=scenario)
    deltas = compare_summaries(baseline_variant, summaries)
    return format_delta_json(deltas) if output_format == "json" else format_delta_table(deltas)


@dataclass(frozen=True)
class AnalyzeOutcome:
    rendered: str
    output_destination: Path | None
    success_rate_violations: tuple[str, ...]
    regression_violations: tuple[RegressionViolation, ...]
    baseline_missing: Path | None
    baseline_path_used: Path | None
    regression_threshold_pct: float


def analyze_csv(
    project_root: Path,
    raw_csv: str,
    output_format: str,
    scenario: str | None,
    variant: str | None,
    output_path: str | None,
    fail_on_success_rate_below: float | None,
    baseline_path: str | None,
    fail_on_regression_above: float | None,
) -> AnalyzeOutcome:
    csv_path = resolve_path(project_root, raw_csv)
    if not csv_path.exists():
        raise ValueError(f"missing CSV file: {csv_path}")
    if fail_on_success_rate_below is not None and not 0.0 <= fail_on_success_rate_below <= 100.0:
        raise ValueError("--fail-on-success-rate-below must be between 0 and 100")

    summaries = summarize_csv(csv_path, scenario=scenario, variant=variant)
    if not summaries:
        return AnalyzeOutcome(
            rendered="No rows matched the provided filters.",
            output_destination=None,
            success_rate_violations=(),
            regression_violations=(),
            baseline_missing=None,
            baseline_path_used=None,
            regression_threshold_pct=fail_on_regression_above or 20.0,
        )

    rendered = format_json(summaries) if output_format == "json" else format_table(summaries)
    destination: Path | None = None
    if output_path:
        destination = resolve_path(project_root, output_path)

    violations: list[str] = []
    if fail_on_success_rate_below is not None:
        violations = [
            f"success_rate below threshold for {summary.scenario}/{summary.variant}: "
            f"{summary.success_rate_pct:.1f}% < {fail_on_success_rate_below:.1f}%"
            for summary in summaries
            if summary.success_rate_pct < fail_on_success_rate_below
        ]

    baseline_missing: Path | None = None
    baseline_path_used: Path | None = None
    regression_violations: list[RegressionViolation] = []
    threshold = fail_on_regression_above or 20.0
    if baseline_path is not None:
        baseline_file = resolve_path(project_root, baseline_path)
        baseline_path_used = baseline_file
        if not baseline_file.exists():
            baseline_missing = baseline_file
        else:
            baseline_summaries = load_summaries(baseline_file)
            regression_violations = detect_regressions(
                baseline=baseline_summaries,
                current=summaries,
                threshold_pct=threshold,
            )

    return AnalyzeOutcome(
        rendered=rendered,
        output_destination=destination,
        success_rate_violations=tuple(violations),
        regression_violations=tuple(regression_violations),
        baseline_missing=baseline_missing,
        baseline_path_used=baseline_path_used,
        regression_threshold_pct=threshold,
    )
