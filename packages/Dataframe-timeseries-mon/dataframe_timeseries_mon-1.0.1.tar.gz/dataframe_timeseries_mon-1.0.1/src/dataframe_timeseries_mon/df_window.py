"""
Public wrapper around `PBM_SUPPORT_DF_WINDOW`.

Policy:
- Export all names that do NOT start with "_" (public surface).
- Provide ergonomic alias `df_to_ordered_window`.
- Provide explicit advanced access via `raw` (the underlying module object).
- Do NOT export underscore names.
"""

from __future__ import annotations

import importlib as _importlib
from typing import Any as _Any

raw = _importlib.import_module("PBM_SUPPORT_DF_WINDOW")

df_to_ordered_window_API = getattr(raw, "df_to_ordered_window_API")
df_to_ordered_window = df_to_ordered_window_API

_public_names = sorted(n for n in dir(raw) if not n.startswith("_"))
for _name in _public_names:
    globals()[_name] = getattr(raw, _name)

__all__ = ["raw", "df_to_ordered_window", "df_to_ordered_window_API"] + _public_names


def __getattr__(name: str) -> _Any:
    if name in globals():
        return globals()[name]
    raise AttributeError(
        f"{__name__!r} has no attribute {name!r}. "
        f"For internal/underscore functions use `{__name__}.raw`."
    )
