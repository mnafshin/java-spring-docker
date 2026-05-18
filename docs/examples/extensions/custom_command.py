from __future__ import annotations

from pathlib import Path


def register(subparsers) -> None:  # type: ignore[no-untyped-def]
    parser = subparsers.add_parser("acme-status", help="Example plugin command")
    parser.add_argument("--project-root", default=".")
    parser.set_defaults(_plugin_handler=handle_acme_status)


def handle_acme_status(args, project_root: Path) -> int:  # type: ignore[no-untyped-def]
    del args
    print(f"acme-status ok for {project_root}")
    return 0
