"""
Public wrapper around `alerting_subsystem`.

Policy:
- Export all names that do NOT start with "_" (public surface).
- Additionally provide utc_ts (public) and _utc_ts (available but not “public API” by default).
- Provide explicit advanced access via `raw` (the underlying module object).
- Do NOT export other underscore names.
"""

from __future__ import annotations

import importlib as _importlib
from typing import Any as _Any

raw = _importlib.import_module("alerting_subsystem")

# Explicit exports
utc_ts = getattr(raw, "utc_ts")
_utc_ts = getattr(raw, "_utc_ts")

# Export every non-underscore name from the underlying module
_public_names = sorted(n for n in dir(raw) if not n.startswith("_"))
for _name in _public_names:
    globals()[_name] = getattr(raw, _name)

# NOTE: _utc_ts intentionally NOT included in __all__ to keep star-import tidy
__all__ = ["raw", "utc_ts"] + _public_names


def __getattr__(name: str) -> _Any:
    """
    Strict policy:
    - Only exported names are accessible directly from this wrapper.
    - Internal/underscore access must go through `raw`.
    - _utc_ts is intentionally available explicitly (dtm.alerting._utc_ts) but not in __all__.
    """
    if name == "_utc_ts":
        return _utc_ts
    if name in globals():
        return globals()[name]
    raise AttributeError(
        f"{__name__!r} has no attribute {name!r}. "
        f"For internal/underscore functions use `{__name__}.raw`."
    )
