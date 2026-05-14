#!/usr/bin/env python3
"""Shared recommendation policy constants for benchmark scenarios."""

SCENARIO_WEIGHTS: dict[str, tuple[float, float, float]] = {
    "01-base-image-pinning": (0.1, 0.1, 0.1),
    "02-multi-stage-build-structure": (0.3, 0.4, 0.3),
    "03-buildkit-gradle-cache": (0.9, 0.0, 0.1),
    "04-custom-jre-jlink": (0.1, 0.5, 0.4),
    "05-jep483-aot-cache": (0.2, 0.1, 0.7),
    "06-runtime-hardening-non-root-tmp": (0.0, 0.0, 0.0),
    "07-healthcheck-readiness": (0.0, 0.0, 0.0),
    "08-jvm-container-flags": (0.0, 0.1, 0.9),
    "09-base-image-choice": (0.2, 0.5, 0.3),
    "10-native-vs-jvm": (0.2, 0.3, 0.5),
}

ALWAYS_BEST_PRACTICE: dict[str, str] = {
    "01-base-image-pinning": "digest-pinned",
    "06-runtime-hardening-non-root-tmp": "hardened-non-root",
    "07-healthcheck-readiness": "with-readiness-healthcheck",
}

