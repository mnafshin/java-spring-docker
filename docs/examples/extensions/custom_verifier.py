from __future__ import annotations


def verify(context) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    marker = context.project_root / ".acme-policy-ok"
    if marker.exists():
        return "passed", "acme policy marker present"
    return "failed", "missing .acme-policy-ok marker"
