from __future__ import annotations

import sys

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def print_error(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)

