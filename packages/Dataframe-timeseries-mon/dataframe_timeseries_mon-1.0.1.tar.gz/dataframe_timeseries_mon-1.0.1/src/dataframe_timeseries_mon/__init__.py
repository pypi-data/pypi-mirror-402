"""
dataframe_timeseries_mon

Top-level policy (best practice + your requirements):
- Expose only public (non-underscore) interfaces at top-level.
- Do not export names that exist in BOTH subsystems (no namespace occlusion).
- Provide explicit access paths:
    - dataframe_timeseries_mon.alerting  (wrapper; internal via .raw)
    - dataframe_timeseries_mon.df_window (wrapper; internal via .raw)
- Provide utc_ts at top-level (public).
- Provide _utc_ts callable explicitly, but do NOT include it in __all__ (tidy).
"""

from __future__ import annotations

from typing import Any as _Any

from . import alerting as alerting
from . import df_window as df_window

# Public timestamp helper
utc_ts = alerting.utc_ts

# Explicit-but-not-public (callable if you really type it)
_utc_ts = getattr(alerting, "_utc_ts")

# Collect “public API” names from wrappers
_alerting_public = {n for n in getattr(alerting, "__all__", []) if n and not n.startswith("_")}
_dfwin_public = {n for n in getattr(df_window, "__all__", []) if n and not n.startswith("_")}

_reserved = {"alerting", "df_window", "utc_ts", "_utc_ts", "raw"}

_alerting_candidates = _alerting_public - _reserved
_dfwin_candidates = _dfwin_public - _reserved

_collisions = sorted(_alerting_candidates & _dfwin_candidates)
_unique_alerting = sorted(_alerting_candidates - set(_collisions))
_unique_dfwin = sorted(_dfwin_candidates - set(_collisions))

# Bind only unique names into top-level namespace
for _name in _unique_alerting:
    globals()[_name] = getattr(alerting, _name)

for _name in _unique_dfwin:
    globals()[_name] = getattr(df_window, _name)

# Top-level public exports: exclude _utc_ts to stay tidy on reviews/star-import
__all__ = (
    ["alerting", "df_window", "utc_ts"]
    + _unique_alerting
    + _unique_dfwin
)

# Useful for debugging / reviewers
__collisions__ = tuple(_collisions)


def __getattr__(name: str) -> _Any:
    # Make _utc_ts explicitly callable even though it is not in __all__
    if name == "_utc_ts":
        return _utc_ts

    if name in __collisions__:
        raise AttributeError(
            f"{__name__!r} attribute {name!r} exists in BOTH subsystems. "
            f"Use `{__name__}.alerting.{name}` or `{__name__}.df_window.{name}`."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
