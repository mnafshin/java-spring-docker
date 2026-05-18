from __future__ import annotations

import json


def render(outcome) -> str:  # type: ignore[no-untyped-def]
    payload = {
        "overall": "failed" if outcome.failed else "passed",
        "checks": [{"name": item.name, "status": item.status} for item in outcome.results],
    }
    return json.dumps(payload, indent=2)
