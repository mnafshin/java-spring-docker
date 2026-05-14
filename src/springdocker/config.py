from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(frozen=True)
class BenchmarkRunConfig:
    build_tool: str | None
    profile: str
    runner_args: list[str]


def render_default_config(build_tool: str, profile: str = "quick") -> str:
    """Render starter .springdocker.toml content."""
    return (
        "# springdocker project configuration\n"
        "# Precedence: CLI flags > this file > internal defaults\n\n"
        "[project]\n"
        f'build_tool = "{build_tool}"\n\n'
        "[benchmark]\n"
        f'profile = "{profile}"\n'
        "runner_args = [\"--skip-native\"]\n"
    )


def write_default_config(path: Path, build_tool: str, force: bool = False) -> None:
    """Write starter config file; fail if present unless force=True."""
    if path.exists() and not force:
        raise FileExistsError(f"Config already exists: {path}")
    path.write_text(render_default_config(build_tool=build_tool), encoding="utf-8")


def load_config(path: Path) -> dict:
    """Load TOML config file; return empty dict when file is absent."""
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config root must be a TOML table")
    return data


def resolve_benchmark_run_config(
    cli_build_tool: str | None,
    cli_profile: str | None,
    cli_runner_args: list[str] | None,
    loaded_config: dict,
) -> BenchmarkRunConfig:
    """Merge benchmark-run settings with precedence: CLI > config > defaults."""
    project = loaded_config.get("project", {}) if isinstance(loaded_config.get("project", {}), dict) else {}
    benchmark = loaded_config.get("benchmark", {}) if isinstance(loaded_config.get("benchmark", {}), dict) else {}

    cfg_build_tool = project.get("build_tool") if isinstance(project.get("build_tool"), str) else None
    cfg_profile = benchmark.get("profile") if isinstance(benchmark.get("profile"), str) else None
    cfg_runner_args = benchmark.get("runner_args") if isinstance(benchmark.get("runner_args"), list) else None

    runner_args: list[str]
    if cli_runner_args is not None:
        runner_args = cli_runner_args
    elif cfg_runner_args is not None:
        runner_args = [str(v) for v in cfg_runner_args]
    else:
        runner_args = []

    profile = cli_profile or cfg_profile or "quick"
    if profile not in {"quick", "full"}:
        raise ValueError("benchmark profile must be 'quick' or 'full'")

    build_tool = cli_build_tool or cfg_build_tool
    if build_tool is not None and build_tool not in {"maven", "gradle"}:
        raise ValueError("build tool must be 'maven' or 'gradle'")

    return BenchmarkRunConfig(
        build_tool=build_tool,
        profile=profile,
        runner_args=runner_args,
    )

