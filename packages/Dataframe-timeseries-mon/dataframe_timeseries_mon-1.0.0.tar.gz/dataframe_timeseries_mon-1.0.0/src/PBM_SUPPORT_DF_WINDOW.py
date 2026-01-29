"""
PBM_SUPPORT_DF_WINDOW_DIAG.py

Universal support module for extracting an ordered time-window list from a pandas DataFrame,
with built-in diagnostics ("DF edge trap" style) and an OPTIONAL bridge into an existing
alerting subsystem via environment variables (NO changes to alerting system required).

Core features
-------------
1) Ordering/window extraction for a single value column (start_hour + num_hours)
2) Safe coercion rules:
   - booleans preserved
   - boolean-like strings parsed ("True"/"False"/"Yes"/"No") if enabled
   - 0/1 treated as boolean ONLY if the entire column is binary-only
   - otherwise values are coerced to float (safe for ints; preserves decimals)
3) Diagnostics (enabled by default):
   - validate DataFrame shape and key columns
   - check NaNs in target column
   - optional strict time-axis check (e.g. "cet_datetime")
   - optional strict coverage of requested hours when hour mapping is used
   - set diagnostic envvars and log markers (with optional DF preview on alarm)

Alert bridge (synergy with existing monitoring; NO rewiring; NEVER "goes nowhere")
---------------------------------------------------------------------------------
If diagnostics are enabled (diag_enable=True), alert bridging is enabled by default.

Default bridge behavior (if caller does not configure routing):
  - publish CAUT for kind="OZE" into PBM_CACHE_{pf}_{kind}_OVERALL for BOTH portfolios:
        ("PCPOL","OZE") and ("PCAGR","OZE")
  - pf list is independent of PBM_TRAP_PORTFOLIO (fanout to both by default)
  - this makes any_alarm(include_caut=True) return True (CAUT-aware)

Why CAUT publishing uses PBM_CACHE keys:
  - Your alerting subsystem derives STATUS from cache keys (OVERALL/DESC/DATA/TS)
  - Trap keys are normalized as OK/ALRM only; CAUT is a cache-level state

Decoupling / redirection controls:
  - You can provide explicit targets (pf/kind pairs) or pfs+kinds.
  - You can disable the default fanout, but the module STILL guarantees a safe fallback
    (unless you explicitly allow "nowhere", which is OFF by default).
  - If you configure only unknown targets and do not explicitly allow unknown-only routing,
    the module publishes to your unknown targets AND also publishes to the safe defaults.

Public-facing function (easy to spot even with `import *`):
  - df_to_ordered_window_API(...)

Diagnostics envvars
-------------------
On each call (unless diagnostics disabled), the module sets:

  <DIAG_BASE_KEY>     = "OK" or "ALRM"
  <DIAG_BASE_KEY>_D   = human-readable detail string

If diag_namespace/diag_name are NOT provided, DIAG_BASE_KEY is generated fresh per call
to avoid collisions.

"""

from __future__ import annotations

from typing import Any, Callable, Hashable, List, Optional, Sequence, Tuple, Union, Dict
import logging
import os
import math
import secrets
from datetime import datetime

import pandas as pd

ColRef = Union[int, str, Hashable]

# Per-import instance ID to reduce collision risk when user does not pin diagnostic names.
_MODULE_INSTANCE_ID = secrets.token_hex(4).upper()

# Conventional portfolio envvar (used by your alerting system)
TRAP_PF_ENV = "PBM_TRAP_PORTFOLIO"


# ----------------------------
# Logging / env helpers
# ----------------------------

def _get_logger(logger: Optional[logging.Logger], name: str) -> logging.Logger:
    lg = logger or logging.getLogger(name)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return lg


def _safe_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return "<unprintable>"


def _sanitize_token(s: Any) -> str:
    out = []
    for ch in str(s):
        if ch.isalnum():
            out.append(ch.upper())
        else:
            out.append("_")
    token = "".join(out)
    while "__" in token:
        token = token.replace("__", "_")
    token = token.strip("_")
    return token if token else "AUTO"


def _env_get(key: str, default: str = "") -> str:
    try:
        return os.getenv(key, default)
    except Exception:
        return default


def _env_set(key: str, value: Any) -> None:
    try:
        os.environ[key] = _safe_str(value)
    except Exception:
        pass


def _trim(s: Any, n: int) -> str:
    try:
        t = ("" if s is None else str(s)).strip()
        if not t:
            return ""
        return (t[:n] + "...") if (n and len(t) > n) else t
    except Exception:
        return ""


def _utc_ts() -> str:
    import time as _time
    try:
        return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(_time.time()))
    except Exception:
        return "1970-01-01T00:00:00Z"


def _set_trap_env(base_key: str, *, ok: bool, detail: str) -> None:
    _env_set(base_key, "OK" if ok else "ALRM")
    _env_set(base_key + "_D", detail)


def _norm_pf(pf: Optional[str]) -> str:
    pf0 = (pf or "").strip()
    if pf0:
        return pf0
    pf1 = _env_get(TRAP_PF_ENV, "").strip()
    return pf1 if pf1 else "UNKNOWN"


def _norm_kind(kind: Optional[str]) -> str:
    k = (kind or "").strip().upper()
    return k if k else "UNKNOWN"


def _trap_status_norm(st: Any) -> str:
    s = ("" if st is None else str(st)).strip().upper()
    if s in ("OK", "ALRM"):
        return s
    return "UNKNOWN"


def _clean_pf_token(pf: Any) -> Optional[str]:
    try:
        t = ("" if pf is None else str(pf)).strip()
        return t if t else None
    except Exception:
        return None


def _clean_kind_token(kind: Any) -> Optional[str]:
    try:
        t = ("" if kind is None else str(kind)).strip().upper()
        return t if t else None
    except Exception:
        return None


# ----------------------------
# Cache-key mirror of alerting_subsystem._cache_keys
# (no dependency on alerting_subsystem required)
# ----------------------------

def _cache_keys(pf: str, kind: str) -> Dict[str, str]:
    pf = _norm_pf(pf)
    kind = _norm_kind(kind)
    base = f"PBM_CACHE_{pf}_{kind}"
    return {
        "BASE": base,
        "TS": base + "_TS",
        "OVERALL": base + "_OVERALL",
        "TRAP": base + "_TRAP",
        "DESC": base + "_DESC",
        "DATA": base + "_DATA",
        "TEXT": f"PBM_LAST_{pf}_{kind}_TEXT",
        "TEXT_TS": f"PBM_LAST_{pf}_{kind}_TS",
        "HELPER_TEXT": f"PBM_HELPER_LAST_{pf}_{kind}_TEXT",
        "HELPER_TS": f"PBM_HELPER_LAST_{pf}_{kind}_TS",
    }


def _publish_cache_state(
    *,
    pf: str,
    kind: str,
    overall: str,
    trap_status: str,
    desc: str,
    data: str,
    stage: str,
    logger: logging.Logger,
) -> None:
    """
    Publish a cache state into PBM_CACHE_* envvars so any_alarm(include_caut=True)
    becomes aware without modifying alerting subsystem code.
    """
    pf_n = _norm_pf(pf)
    kind_n = _norm_kind(kind)
    ks = _cache_keys(pf_n, kind_n)

    _env_set(ks["TS"], _utc_ts())
    _env_set(ks["OVERALL"], overall)
    _env_set(ks["TRAP"], _trap_status_norm(trap_status))
    _env_set(ks["DESC"], _trim(desc, 600) if desc else "(missing)")
    _env_set(ks["DATA"], _trim(data, 1600) if data else "(missing)")

    helper_msg = "\n".join([
        "SYSTEM ALARM" if overall != "OK" else "SYSTEM STATUS REPORT",
        f"UTC: {_utc_ts()}",
        f"FOLIO: {pf_n}",
        f"KIND: {kind_n}",
        f"STAGE: {stage}",
        f"TRAP_STATUS: {_trap_status_norm(trap_status)}",
        f"CHECKS: {_trim(desc, 900) if desc else '(missing)'}",
    ])
    _env_set(ks["HELPER_TEXT"], _trim(helper_msg, 12000))
    _env_set(ks["HELPER_TS"], _utc_ts())

    logger.warning(f"[ALERT_BRIDGE][{overall}] published cache {overall} for {pf_n}/{kind_n}")


# ----------------------------
# Diagnostics naming helpers
# ----------------------------

def _infer_default_diag_name(*, value_col: ColRef, hour_col: Optional[ColRef]) -> str:
    vc = _sanitize_token(f"VAL_{value_col}")
    hc = _sanitize_token(f"HR_{hour_col}") if hour_col is not None else "NOHR"
    return f"{vc}_{hc}"


def _fresh_diag_namespace(diag_namespace: Optional[str]) -> str:
    if diag_namespace and str(diag_namespace).strip():
        return _sanitize_token(diag_namespace)
    return f"DFWIN_{_MODULE_INSTANCE_ID}"


def _fresh_diag_name(diag_name: Optional[str], *, value_col: ColRef, hour_col: Optional[ColRef]) -> str:
    if diag_name and str(diag_name).strip():
        return _sanitize_token(diag_name)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rnd = secrets.token_hex(2).upper()
    hint = _infer_default_diag_name(value_col=value_col, hour_col=hour_col)
    return f"{hint}_{ts}_{rnd}"


def _env_key_base(
    *,
    diag_env_prefix: str,
    diag_namespace: str,
    diag_name: str,
    diag_kind: str,
    portfolio_env_var: Optional[str] = TRAP_PF_ENV,
) -> str:
    pf = _env_get(portfolio_env_var, "").strip() if portfolio_env_var else ""
    parts = [_sanitize_token(diag_env_prefix)]
    if pf:
        parts.append(_sanitize_token(pf))
    parts.append(_sanitize_token(diag_namespace))
    parts.append(_sanitize_token(diag_name))
    parts.append(_sanitize_token(diag_kind))
    return "_".join(parts)


def _safe_df_preview(df: pd.DataFrame, *, max_rows: int, max_cols: int) -> pd.DataFrame:
    try:
        return df.iloc[:max_rows, :max_cols].copy()
    except Exception:
        return df.head(max_rows).copy()


# ----------------------------
# Type / coercion helpers
# ----------------------------

def _is_missing(x: Any) -> bool:
    try:
        return x is None or (isinstance(x, float) and pd.isna(x)) or bool(pd.isna(x))
    except Exception:
        return x is None


def _default_bool_tokens(
    bool_true_tokens: Optional[set[str]],
    bool_false_tokens: Optional[set[str]],
) -> Tuple[set[str], set[str]]:
    # Conservative defaults: do NOT include "0"/"1" here; binary-only inference handles them.
    t = bool_true_tokens if bool_true_tokens is not None else {"true", "yes"}
    f = bool_false_tokens if bool_false_tokens is not None else {"false", "no"}
    return {s.strip().lower() for s in t}, {s.strip().lower() for s in f}


def _parse_bool_str(
    s: str,
    *,
    parse_bool_strings: bool,
    true_tokens: set[str],
    false_tokens: set[str],
) -> Optional[bool]:
    if not parse_bool_strings:
        return None
    tok = s.strip().lower()
    if tok in true_tokens:
        return True
    if tok in false_tokens:
        return False
    return None


def _try_parse_float(x: Any, *, coerce_float: Callable[[Any], float]) -> Optional[float]:
    if _is_missing(x):
        return None
    if isinstance(x, bool):
        return float(x)
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        try:
            return float(s.replace(",", "."))
        except Exception:
            return None
    try:
        return float(coerce_float(x))
    except Exception:
        return None


def _infer_binary_only_01(
    values: Sequence[Any],
    *,
    parse_bool_strings: bool,
    true_tokens: set[str],
    false_tokens: set[str],
    coerce_float: Callable[[Any], float],
) -> bool:
    """
    True if (ignoring nulls) every entry is:
      - bool, or
      - bool-like string, or
      - numeric 0/1 (including "0"/"1")
    """
    saw_any = False
    for v in values:
        if _is_missing(v):
            continue
        saw_any = True

        if isinstance(v, bool):
            continue

        if isinstance(v, str):
            b = _parse_bool_str(v, parse_bool_strings=parse_bool_strings, true_tokens=true_tokens, false_tokens=false_tokens)
            if b is not None:
                continue
            fv = _try_parse_float(v, coerce_float=coerce_float)
            if fv is None or fv not in (0.0, 1.0):
                return False
            continue

        fv = _try_parse_float(v, coerce_float=coerce_float)
        if fv is None or fv not in (0.0, 1.0):
            return False

    return saw_any


def _coerce_value_auto(
    v_raw: Any,
    *,
    binary_only_01: bool,
    parse_bool_strings: bool,
    true_tokens: set[str],
    false_tokens: set[str],
    coerce_float: Callable[[Any], float],
) -> Any:
    if isinstance(v_raw, bool):
        return bool(v_raw)

    if isinstance(v_raw, str):
        b = _parse_bool_str(v_raw, parse_bool_strings=parse_bool_strings, true_tokens=true_tokens, false_tokens=false_tokens)
        if b is not None:
            return b
        if binary_only_01:
            fv = _try_parse_float(v_raw, coerce_float=coerce_float)
            if fv in (0.0, 1.0):
                return bool(int(fv))
        return float(v_raw.strip().replace(",", "."))

    if binary_only_01:
        fv = _try_parse_float(v_raw, coerce_float=coerce_float)
        if fv in (0.0, 1.0):
            return bool(int(fv))

    fv = _try_parse_float(v_raw, coerce_float=coerce_float)
    if fv is None:
        raise ValueError(f"Cannot coerce value to float: {v_raw!r}")
    if isinstance(fv, float) and not math.isfinite(fv):
        raise ValueError(f"Non-finite float: {fv!r}")
    return float(fv)


# ----------------------------
# Time-axis check (optional)
# ----------------------------

def _time_axis_status(
    df: pd.DataFrame,
    time_col: str,
    *,
    expected_rows: Optional[int] = 24,
    freq: str = "H",
) -> Tuple[bool, str]:
    if df is None or df.empty:
        return False, "TIME_EMPTY_DF"
    if time_col not in df.columns:
        return False, f"TIME_MISSING_COLUMN({time_col})"

    t = df[time_col]
    if not pd.api.types.is_datetime64_any_dtype(t):
        t = pd.to_datetime(t, errors="coerce")

    if t.isna().any():
        return False, "TIME_BAD_TIMESTAMP_PARSE"

    n = len(t)
    if expected_rows is not None and n != expected_rows:
        return False, f"TIME_ROWCOUNT({n}!={expected_rows})"

    if t.duplicated().any():
        return False, "TIME_DUPLICATE_TIMESTAMPS"

    if not t.is_monotonic_increasing:
        return False, "TIME_NOT_SORTED"

    day0 = t.iloc[0].floor("D")
    exp_n = n if expected_rows is None else expected_rows
    expected = pd.date_range(day0, periods=exp_n, freq=freq)

    t_cmp = t.reset_index(drop=True)
    exp_cmp = expected[: len(t_cmp)]
    if not (t_cmp == exp_cmp).all():
        return False, f"TIME_GAP_OR_SHIFT({t.iloc[0].strftime('%H:%M')}..{t.iloc[-1].strftime('%H:%M')})"

    return True, "TIME_OK"


# ----------------------------
# Hour mapping / ordering
# ----------------------------

def _hour_to_int(h: Any, *, period: int) -> Optional[int]:
    if isinstance(h, (pd.Timestamp, datetime)):
        return int(h.hour) % period
    try:
        return int(h) % period
    except Exception:
        try:
            ts = pd.to_datetime(h, errors="coerce")
            if pd.isna(ts):
                return None
            return int(ts.hour) % period
        except Exception:
            return None


def _auto_detect_index_as_hour(df: pd.DataFrame, *, period: int) -> bool:
    idx = df.index
    if isinstance(idx, pd.DatetimeIndex):
        return True
    try:
        return (
            idx.is_unique
            and pd.api.types.is_integer_dtype(idx)
            and int(idx.min()) >= 0
            and int(idx.max()) <= (period - 1)
        )
    except Exception:
        return False


def _ordered_from_mapping(
    mapping: Dict[int, Any],
    *,
    start_hour: int,
    num_hours_eff: int,
    period: int,
    fill_missing: Any,
) -> List[Any]:
    out: List[Any] = []
    for i in range(num_hours_eff):
        h = (start_hour + i) % period
        out.append(mapping.get(h, fill_missing))
    return out


def _ordered_from_positional(
    values_raw: Sequence[Any],
    *,
    start_hour: int,
    num_hours_eff: int,
    base_hour: int,
    period: int,
    fill_missing: Any,
) -> List[Any]:
    out: List[Any] = []
    for i in range(num_hours_eff):
        h = (start_hour + i) % period
        idx = (h - int(base_hour)) % period
        out.append(values_raw[idx] if 0 <= idx < len(values_raw) else fill_missing)
    return out


# ----------------------------
# Diagnostics engine
# ----------------------------

def _diagnose_input_df(
    df: pd.DataFrame,
    *,
    value_col: ColRef,
    hour_col: Optional[ColRef],
    use_index_as_hour: bool,
    start_hour: int,
    num_hours_eff: int,
    period: int,
    output: str,
    infer_binary_01_as_bool: bool,
    parse_bool_strings: bool,
    bool_true_tokens: Optional[set[str]],
    bool_false_tokens: Optional[set[str]],
    coerce_float: Callable[[Any], float],
    expected_rows: Optional[int],
    time_col: Optional[str],
    time_freq: str,
    strict_hours_coverage: bool,
) -> Tuple[bool, str, str, Dict[str, Any]]:
    if df is None:
        return False, "DF_NONE", "df is None", {}
    if getattr(df, "empty", False):
        return False, "DF_EMPTY", "df is empty", {"shape": getattr(df, "shape", None)}

    try:
        ser = df.iloc[:, value_col] if isinstance(value_col, int) else df[value_col]
    except Exception as e:
        return False, "DF_MISSING_VALUE_COL", f"missing value_col={value_col!r} ({e})", {"columns": list(getattr(df, "columns", []))}

    if hour_col is not None and hour_col not in df.columns:
        return False, "DF_MISSING_HOUR_COL", f"missing hour_col={hour_col!r}", {"columns": list(df.columns)}

    meta: Dict[str, Any] = {"shape": df.shape}

    if expected_rows is not None and len(df) != expected_rows:
        meta["expected_rows"] = expected_rows
        meta["actual_rows"] = len(df)
        return False, "DF_ROWCOUNT", f"rowcount({len(df)}!={expected_rows})", meta

    if time_col:
        ok_t, st_t = _time_axis_status(df, time_col, expected_rows=expected_rows, freq=time_freq)
        meta["time_status"] = st_t
        if not ok_t:
            return False, "DF_TIME_AXIS", st_t, meta

    nan_count = int(ser.isna().sum()) if hasattr(ser, "isna") else 0
    meta["nan_count"] = nan_count

    true_tokens, false_tokens = _default_bool_tokens(bool_true_tokens, bool_false_tokens)
    values = ser.tolist()

    binary_only = False
    if infer_binary_01_as_bool and output == "auto":
        binary_only = _infer_binary_only_01(
            values,
            parse_bool_strings=parse_bool_strings,
            true_tokens=true_tokens,
            false_tokens=false_tokens,
            coerce_float=coerce_float,
        )
    meta["binary_only_01"] = binary_only

    if output == "float" or (output == "auto" and not binary_only):
        bad_examples: List[str] = []
        sample = [v for v in values if not _is_missing(v)][:2000]
        for v in sample:
            if isinstance(v, bool):
                continue
            if isinstance(v, str):
                b = _parse_bool_str(v, parse_bool_strings=parse_bool_strings, true_tokens=true_tokens, false_tokens=false_tokens)
                if b is not None:
                    continue
            fv = _try_parse_float(v, coerce_float=coerce_float)
            if fv is None or (isinstance(fv, float) and not math.isfinite(fv)):
                bad_examples.append(repr(v))
                if len(bad_examples) >= 3:
                    break
        meta["nonfinite_or_unparseable_examples"] = bad_examples
        if bad_examples:
            return False, "DF_VALUE_COERCE", f"unparseable/nonfinite sample={bad_examples}", meta

    if strict_hours_coverage and (hour_col is not None or use_index_as_hour):
        hours_needed = {(start_hour + i) % period for i in range(num_hours_eff)}
        hours_present: set[int] = set()

        if hour_col is not None:
            for h in df[hour_col].tolist():
                hh = _hour_to_int(h, period=period)
                if hh is not None:
                    hours_present.add(hh)
        else:
            for idx in df.index.tolist():
                hh = _hour_to_int(idx, period=period)
                if hh is not None:
                    hours_present.add(hh)

        missing = sorted(hours_needed - hours_present)
        meta["hours_needed"] = sorted(hours_needed)
        meta["hours_present"] = sorted(hours_present)
        if missing:
            meta["hours_missing"] = missing
            return False, "DF_MISSING_HOURS", f"missing hours={missing}", meta

    if nan_count > 0:
        return False, "DF_NAN_VALUES", f"value_col has NaN count={nan_count}", meta

    return True, "DF_OK", "ok", meta


# ----------------------------
# Alert bridge target resolution
# ----------------------------

def _uniq_pairs(pairs: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen = set()
    out = []
    for pf, kind in pairs:
        key = (pf, kind)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _resolve_bridge_targets(
    *,
    diag_enable: bool,
    alert_bridge_enable: Optional[bool],
    explicit_targets: Optional[Sequence[Tuple[Any, Any]]],
    alert_bridge_pfs: Optional[Sequence[Any]],
    alert_bridge_kinds: Optional[Sequence[Any]],
    include_default_fanout: bool,
    default_fanout_pfs: Sequence[str],
    default_fanout_kind: str,
    include_env_pf: bool,
    env_pf: str,
    known_good_pfs: Sequence[str],
    known_good_kinds: Sequence[str],
    allow_unknown_only: bool,
    allow_nowhere: bool,
    logger: logging.Logger,
) -> List[Tuple[str, str]]:
    """
    Computes final list of (pf, kind) targets.

    Safety rules:
      - If diagnostics enabled, bridge defaults ON unless explicitly disabled by caller.
      - If after user config the resulting target set would "go nowhere", we add safe defaults.
      - If user only provides unknown targets and does not allow unknown-only routing, we ALSO add safe defaults.
    """
    if not diag_enable:
        return []

    bridge_on = bool(diag_enable) if alert_bridge_enable is None else bool(alert_bridge_enable)
    if not bridge_on:
        return []

    defaults = [(str(pf).strip(), str(default_fanout_kind).strip().upper()) for pf in (default_fanout_pfs or ())]
    defaults = [(pf, kind) for pf, kind in defaults if pf and kind]

    # Explicit targets: list of pairs, if provided
    explicit_pairs: List[Tuple[str, str]] = []
    if explicit_targets:
        for pf_raw, kind_raw in explicit_targets:
            pf = _clean_pf_token(pf_raw)
            kind = _clean_kind_token(kind_raw)
            if pf and kind:
                explicit_pairs.append((pf, kind))

    # pfs/kinds cross-product (optional)
    pfs_list: List[str] = []
    kinds_list: List[str] = []
    if alert_bridge_pfs:
        for pf_raw in alert_bridge_pfs:
            pf = _clean_pf_token(pf_raw)
            if pf:
                pfs_list.append(pf)
    if alert_bridge_kinds:
        for k_raw in alert_bridge_kinds:
            k = _clean_kind_token(k_raw)
            if k:
                kinds_list.append(k)

    if pfs_list or kinds_list:
        if not pfs_list:
            # no pfs provided -> use defaults (fanout) pfs as base
            pfs_list = [pf for pf, _ in defaults] if defaults else []
        if not kinds_list:
            kinds_list = [str(default_fanout_kind).strip().upper()]
        for pf in pfs_list:
            for k in kinds_list:
                explicit_pairs.append((pf, k))

    # Env PF inclusion
    env_pairs: List[Tuple[str, str]] = []
    if include_env_pf and env_pf and env_pf != "UNKNOWN":
        # Attach env pf to default kind (or first explicit kind if present)
        env_kind = (explicit_pairs[0][1] if explicit_pairs else str(default_fanout_kind).strip().upper())
        env_pairs.append((env_pf, env_kind))

    # Assemble candidates
    candidates: List[Tuple[str, str]] = []
    if include_default_fanout:
        candidates.extend(defaults)
    candidates.extend(explicit_pairs)
    candidates.extend(env_pairs)

    candidates = _uniq_pairs([(pf.strip(), kind.strip().upper()) for pf, kind in candidates if pf and kind])

    # Guarantee: must not go nowhere unless explicitly allowed
    if not candidates:
        if allow_nowhere:
            logger.warning("[ALERT_BRIDGE] computed NO targets and allow_nowhere=True (not recommended)")
            return []
        logger.warning("[ALERT_BRIDGE] computed NO targets; falling back to safe defaults")
        return _uniq_pairs(defaults) if defaults else []

    # Determine whether this set is "known good" for the current alerting subsystem
    known_good_set = {(str(p).strip(), str(k).strip().upper()) for p in known_good_pfs for k in known_good_kinds}
    intersects_known = any((pf, kind) in known_good_set for pf, kind in candidates)

    # If user routed only to unknown targets and did not explicitly allow it, add safe defaults
    if (not intersects_known) and (not allow_unknown_only) and defaults:
        logger.warning("[ALERT_BRIDGE] targets appear unknown-only; adding safe defaults to prevent 'nowhere'")
        merged = _uniq_pairs(list(defaults) + list(candidates))
        return merged

    return candidates


# ------------------------
# Public-facing API
# ------------------------

def df_to_ordered_window_API(
    df: pd.DataFrame,
    *,
    value_col: ColRef,
    start_hour: int,
    num_hours: int,
    OVERRIDE_TO_6HR: bool = True,
    max_override_hours: int = 6,
    period: int = 24,
    # Hour alignment options:
    hour_col: Optional[ColRef] = None,
    use_index_as_hour: Optional[bool] = None,  # None -> auto-detect
    base_hour: int = 0,                        # used in positional mode
    # Coercion / robustness:
    output: str = "auto",   # "auto" | "float" | "raw"
    invalid: str = "nan",   # "nan" | "keep" | "raise"
    fill_missing: Any = float("nan"),
    dropna: bool = False,
    coerce_float: Callable[[Any], float] = float,
    # Boolean-string parsing:
    parse_bool_strings: bool = True,
    bool_true_tokens: Optional[set[str]] = None,
    bool_false_tokens: Optional[set[str]] = None,
    infer_binary_01_as_bool: bool = True,
    # Diagnostics (auto-enabled by default):
    diag_enable: bool = True,
    diag_env_prefix: str = "PBM_TRAP",
    diag_kind: str = "DFWIN",
    diag_namespace: Optional[str] = None,
    diag_name: Optional[str] = None,
    diag_expected_rows: Optional[int] = 24,          # set None to disable rowcount check
    diag_time_col: Optional[str] = None,             # e.g. "cet_datetime" enables strict time-axis validation
    diag_time_freq: str = "H",
    diag_strict_hours_coverage: bool = False,
    diag_dump_df_on_alarm: bool = True,
    diag_dump_max_rows: int = 200,
    diag_dump_max_cols: int = 50,
    portfolio_env_var: Optional[str] = TRAP_PF_ENV,
    # Alert bridge (DEFAULT: ON when diag_enable=True; CAUT fanout to both portfolios on OZE)
    alert_bridge_enable: Optional[bool] = None,              # None -> defaults to diag_enable
    alert_bridge_level: str = "CAUT",                        # "CAUT" (default) or "ALRM"
    alert_bridge_kind_default: str = "OZE",                  # default kind used for safe fanout
    alert_bridge_include_default_fanout: bool = True,        # default: publish to both PCPOL/PCAGR
    alert_bridge_default_fanout_pfs: Sequence[str] = ("PCPOL", "PCAGR"),
    alert_bridge_include_env_pf: bool = True,                # additionally include env PF if present
    # Explicit routing (optional)
    alert_bridge_targets: Optional[Sequence[Tuple[Any, Any]]] = None,  # list of (pf, kind)
    alert_bridge_pfs: Optional[Sequence[Any]] = None,                 # pfs cross-product
    alert_bridge_kinds: Optional[Sequence[Any]] = None,               # kinds cross-product
    # Safety / decoupling semantics
    alert_bridge_known_good_pfs: Sequence[str] = ("PCPOL", "PCAGR"),
    alert_bridge_known_good_kinds: Sequence[str] = ("OZE", "RB"),
    alert_bridge_allow_unknown_only_routing: bool = False,   # if False, unknown-only routes ALSO publish to safe defaults
    alert_bridge_allow_nowhere: bool = False,                # if True, allow suppressing all safe fallbacks (NOT recommended)
    # Error policy:
    logger: Optional[logging.Logger] = None,
    raise_on_error: bool = False,
) -> List[Any]:
    """
    Extract a single column from a pandas DataFrame and return an ordered window list
    starting at `start_hour` for `num_hours` elements.

    Defaults:
      - OVERRIDE_TO_6HR=True clamps window to <=6
      - output="auto" preserves booleans and parses boolean strings; otherwise floats
      - diagnostics enabled -> alert bridge enabled -> CAUT published to BOTH portfolios for OZE if issues

    Bridge routing / decoupling:
      - By default, if diagnostics detect a problem, CAUT is published to:
            (PCPOL, OZE) and (PCAGR, OZE)
        guaranteeing the alert cannot "go nowhere" with the current any_alarm defaults.
      - If you provide explicit routing (targets or pfs/kinds), it will be used.
      - If your explicit routing appears unknown-only (not in known-good sets) and you do not
        set alert_bridge_allow_unknown_only_routing=True, the module will ALSO publish to safe defaults.

    Minimal example (default safe behavior):
    >>> import os
    >>> os.environ["PBM_TRAP_PORTFOLIO"] = "PCPOL"
    >>> lst = df_to_ordered_window_API(df=pozycja_oze, value_col="position", start_hour=0, num_hours=24)

    Decouple from default fanout and route ONLY to a new folio/kind (advanced):
    >>> lst = df_to_ordered_window_API(
    ...     df=pozycja_oze,
    ...     value_col="position",
    ...     start_hour=0,
    ...     num_hours=24,
    ...     alert_bridge_include_default_fanout=False,
    ...     alert_bridge_targets=[("NEWPF", "NEWKIND")],
    ...     alert_bridge_allow_unknown_only_routing=True,  # you accept that legacy any_alarm may not check this yet
    ... )

    Stable diagnostics envvar naming:
    >>> import os
    >>> os.environ["PBM_TRAP_PORTFOLIO"] = "PCPOL"
    >>> _ = df_to_ordered_window_API(
    ...     df=pozycja_oze,
    ...     value_col="position",
    ...     start_hour=0,
    ...     num_hours=24,
    ...     diag_namespace="OZE",
    ...     diag_name="POSITIONS",
    ...     diag_time_col="cet_datetime",
    ... )
    >>> os.getenv("PBM_TRAP_PCPOL_OZE_POSITIONS_DFWIN"), os.getenv("PBM_TRAP_PCPOL_OZE_POSITIONS_DFWIN_D")
    """

    lg = _get_logger(logger, "PBM_SUPPORT_DF_WINDOW_API")

    def _fail(msg: str) -> None:
        if raise_on_error:
            raise ValueError(msg)
        lg.error(msg)

    # Effective bridge toggle (defaults ON if diagnostics enabled)
    bridge_on = bool(diag_enable) if alert_bridge_enable is None else bool(alert_bridge_enable)

    # Resolve pf from env (for optional inclusion)
    env_pf = _env_get(portfolio_env_var or TRAP_PF_ENV, "").strip()
    env_pf = env_pf if env_pf else "UNKNOWN"

    # Resolve targets up-front so early failures still publish
    bridge_targets = _resolve_bridge_targets(
        diag_enable=diag_enable,
        alert_bridge_enable=alert_bridge_enable,
        explicit_targets=alert_bridge_targets,
        alert_bridge_pfs=alert_bridge_pfs,
        alert_bridge_kinds=alert_bridge_kinds,
        include_default_fanout=bool(alert_bridge_include_default_fanout),
        default_fanout_pfs=alert_bridge_default_fanout_pfs,
        default_fanout_kind=alert_bridge_kind_default,
        include_env_pf=bool(alert_bridge_include_env_pf),
        env_pf=env_pf,
        known_good_pfs=alert_bridge_known_good_pfs,
        known_good_kinds=alert_bridge_known_good_kinds,
        allow_unknown_only=bool(alert_bridge_allow_unknown_only_routing),
        allow_nowhere=bool(alert_bridge_allow_nowhere),
        logger=lg,
    )

    def _bridge_publish_if_needed(*, alarm: bool, desc: str, data: str) -> None:
        if not (diag_enable and bridge_on and alarm):
            return
        level = (alert_bridge_level or "CAUT").strip().upper()
        stage = "DFWIN_DIAGNOSTICS_CAUTION" if level != "ALRM" else "DFWIN_DIAGNOSTICS_ALARM"

        for pf_t, kind_t in (bridge_targets or []):
            pf_n = _norm_pf(pf_t)
            kind_n = _norm_kind(kind_t)

            trap_base = f"PBM_TRAP_{pf_n}_{kind_n}"
            trap_st = _env_get(trap_base, "")
            trap_stn = _trap_status_norm(trap_st)

            if level == "ALRM":
                # Escalate trap to ALRM (never downgrade)
                if trap_stn != "ALRM":
                    _env_set(trap_base, "ALRM")
                _env_set(trap_base + "_D", _trim(desc, 900))
                lg.warning(f"[ALERT_BRIDGE][ALRM] escalated {trap_base}=ALRM")
            else:
                # Default: publish CAUT via cache keys
                _publish_cache_state(
                    pf=pf_n,
                    kind=kind_n,
                    overall="CAUT",
                    trap_status=trap_stn,
                    desc=desc,
                    data=data,
                    stage=stage,
                    logger=lg,
                )
                # Fill trap descriptor (non-invasive)
                if not (_env_get(trap_base + "_D", "") or "").strip():
                    _env_set(trap_base + "_D", _trim(desc, 900))

    # Normalize hours and apply clamp
    try:
        start_hour_i = int(start_hour) % period
    except Exception:
        _fail(f"start_hour must be int-like; got {start_hour!r}")
        start_hour_i = 0

    try:
        num_hours_i = int(num_hours)
    except Exception:
        _fail(f"num_hours must be int-like; got {num_hours!r}")
        num_hours_i = period

    if OVERRIDE_TO_6HR and num_hours_i > max_override_hours:
        lg.warning(f"[{datetime.now()}] [* SYSTEM CONFIG *] [WINDOW] HOURS SET TO: {num_hours_i} limiting to <= {max_override_hours} AS OVERRIDE ACTIVE")
        num_hours_eff = max_override_hours
    else:
        num_hours_eff = num_hours_i

    if num_hours_eff < 1:
        _fail(f"num_hours (effective) must be >= 1; got {num_hours_eff}")
        num_hours_eff = 1
    if num_hours_eff > period:
        _fail(f"num_hours (effective) must be <= {period}; got {num_hours_eff}")
        num_hours_eff = period

    if use_index_as_hour is None:
        use_index_as_hour = _auto_detect_index_as_hour(df, period=period)

    # Diagnostic env key (fresh unless pinned)
    diag_ns = _fresh_diag_namespace(diag_namespace) if diag_enable else ""
    diag_nm = _fresh_diag_name(diag_name, value_col=value_col, hour_col=hour_col) if diag_enable else ""
    diag_base_key = _env_key_base(
        diag_env_prefix=diag_env_prefix,
        diag_namespace=diag_ns,
        diag_name=diag_nm,
        diag_kind=diag_kind,
        portfolio_env_var=portfolio_env_var,
    ) if diag_enable else ""

    # Pre diagnostics
    pre_ok = True
    pre_detail = "diag disabled"
    pre_meta: Dict[str, Any] = {}
    if diag_enable:
        try:
            ok_in, st_in, detail_in, meta_in = _diagnose_input_df(
                df,
                value_col=value_col,
                hour_col=hour_col,
                use_index_as_hour=bool(use_index_as_hour),
                start_hour=start_hour_i,
                num_hours_eff=num_hours_eff,
                period=period,
                output=output,
                infer_binary_01_as_bool=infer_binary_01_as_bool,
                parse_bool_strings=parse_bool_strings,
                bool_true_tokens=bool_true_tokens,
                bool_false_tokens=bool_false_tokens,
                coerce_float=coerce_float,
                expected_rows=diag_expected_rows,
                time_col=diag_time_col,
                time_freq=diag_time_freq,
                strict_hours_coverage=diag_strict_hours_coverage,
            )
            pre_ok = ok_in
            pre_detail = f"{st_in} | {detail_in}"
            pre_meta = meta_in

            _set_trap_env(diag_base_key, ok=ok_in, detail=f"{pre_detail} | meta={pre_meta}")

            if not ok_in:
                lg.warning(f"[{datetime.now()}] [DFWIN][DF_PRE] status=ALRM key={diag_base_key} {pre_detail}")
                if diag_dump_df_on_alarm:
                    prev = _safe_df_preview(df, max_rows=diag_dump_max_rows, max_cols=diag_dump_max_cols)
                    lg.warning(f"DF_STATUS_ALRM_DFWIN_DUMP_BEGIN key={diag_base_key}")
                    lg.warning(f"{prev}")
                    lg.warning(f"DF_STATUS_ALRM_DFWIN_DUMP_END key={diag_base_key}")
            else:
                lg.warning(f"[{datetime.now()}] [DFWIN][DF_PRE] status=OK key={diag_base_key} shape={getattr(df, 'shape', None)}")
        except Exception as e:
            lg.error(f"[DFWIN][DIAG_EXCEPTION_PRE] key={diag_base_key} exc={e}")
            pre_ok = False
            pre_detail = f"DIAG_EXCEPTION_PRE({type(e).__name__})"
            _set_trap_env(diag_base_key, ok=False, detail=pre_detail)

    # If pre diagnostics alarm, publish CAUT/ALRM immediately (guarantee visibility)
    if diag_enable and (not pre_ok):
        desc = f"DFWIN_BRIDGE | diag_key={diag_base_key} | PRE=ALRM:{_trim(pre_detail, 420)}"
        data = f"DFWIN: value_col={value_col!r} start_hour={start_hour_i} num_hours_eff={num_hours_eff} output={output} stage=PRE"
        _bridge_publish_if_needed(alarm=True, desc=desc, data=data)

    # Extract series (no mutation)
    try:
        ser = df.iloc[:, value_col] if isinstance(value_col, int) else df[value_col]
        ser = ser.dropna() if dropna else ser
    except Exception as e:
        msg = f"FAILED_VALUE_COL_ACCESS({value_col!r}): {e}"
        lg.error(msg)
        if diag_enable:
            _set_trap_env(diag_base_key, ok=False, detail=msg)
            desc = f"DFWIN_BRIDGE | diag_key={diag_base_key} | VALUE_COL_ACCESS_FAIL:{_trim(msg, 420)}"
            data = f"DFWIN: value_col={value_col!r} start_hour={start_hour_i} num_hours_eff={num_hours_eff} output={output} stage=ACCESS"
            _bridge_publish_if_needed(alarm=True, desc=desc, data=data)
        if raise_on_error:
            raise
        return []

    true_tokens, false_tokens = _default_bool_tokens(bool_true_tokens, bool_false_tokens)
    values_full = ser.tolist()

    binary_only_01 = False
    if infer_binary_01_as_bool and output == "auto":
        try:
            binary_only_01 = _infer_binary_only_01(
                values_full,
                parse_bool_strings=parse_bool_strings,
                true_tokens=true_tokens,
                false_tokens=false_tokens,
                coerce_float=coerce_float,
            )
        except Exception:
            binary_only_01 = False

    # Build mapping if hour mapping mode is used
    mapping: Optional[Dict[int, Any]] = None
    if hour_col is not None:
        try:
            mapping = {}
            vals_all = df.iloc[:, value_col].tolist() if isinstance(value_col, int) else df[value_col].tolist()
            for h_raw, v_raw in zip(df[hour_col].tolist(), vals_all):
                hh = _hour_to_int(h_raw, period=period)
                if hh is None:
                    continue
                mapping[hh] = v_raw
        except Exception as e:
            mapping = None
            lg.error(f"Failed to build hour_col mapping hour_col={hour_col!r}: {e}")

    elif use_index_as_hour:
        try:
            mapping = {}
            for idx_raw, v_raw in ser.items():
                hh = _hour_to_int(idx_raw, period=period)
                if hh is None:
                    continue
                mapping[hh] = v_raw
        except Exception as e:
            mapping = None
            lg.error(f"Failed to build index-as-hour mapping: {e}")

    if mapping is not None:
        raw_window = _ordered_from_mapping(
            mapping,
            start_hour=start_hour_i,
            num_hours_eff=num_hours_eff,
            period=period,
            fill_missing=fill_missing,
        )
    else:
        raw_window = _ordered_from_positional(
            values_full,
            start_hour=start_hour_i,
            num_hours_eff=num_hours_eff,
            base_hour=base_hour,
            period=period,
            fill_missing=fill_missing,
        )

    # Coerce output
    out: List[Any] = []
    for v in raw_window:
        try:
            if output == "raw":
                out.append(v)
            elif output == "float":
                out.append(float(v))
            else:
                out.append(
                    _coerce_value_auto(
                        v,
                        binary_only_01=binary_only_01,
                        parse_bool_strings=parse_bool_strings,
                        true_tokens=true_tokens,
                        false_tokens=false_tokens,
                        coerce_float=coerce_float,
                    )
                )
        except Exception as e:
            if invalid == "raise":
                raise
            if invalid == "keep":
                out.append(v)
            else:
                out.append(float("nan"))
            lg.warning(f"[{datetime.now()}] [DFWIN][COERCE] value={v!r} exc={e} invalid_policy={invalid}")

    # Post diagnostics: output integrity (light)
    post_ok = True
    post_detail = "POST_OK"
    if diag_enable:
        try:
            issues: List[str] = []
            if len(out) != num_hours_eff:
                issues.append(f"OUT_LEN({len(out)}!={num_hours_eff})")
            if (output == "float") or (output == "auto" and not binary_only_01):
                nan_out = 0
                for vv in out:
                    try:
                        if isinstance(vv, float) and pd.isna(vv):
                            nan_out += 1
                    except Exception:
                        pass
                if nan_out:
                    issues.append(f"OUT_NAN({nan_out})")
            if issues:
                post_ok = False
                post_detail = " | ".join(issues)

            prev_diag = (_env_get(diag_base_key, "") or "").strip().upper()
            final_ok_diag = (prev_diag != "ALRM") and post_ok
            _set_trap_env(
                diag_base_key,
                ok=final_ok_diag,
                detail=f"POST | {post_detail} | output_len={len(out)} binary_only_01={binary_only_01}",
            )
        except Exception as e:
            lg.error(f"[DFWIN][DIAG_EXCEPTION_POST] key={diag_base_key} exc={e}")
            post_ok = False
            post_detail = f"DIAG_EXCEPTION_POST({type(e).__name__})"
            _set_trap_env(diag_base_key, ok=False, detail=post_detail)

    # Final bridge publish if any alarm condition present
    if diag_enable and ((not pre_ok) or (not post_ok)):
        desc = (
            f"DFWIN_BRIDGE | diag_key={diag_base_key} | "
            f"PRE={'OK' if pre_ok else 'ALRM'}:{_trim(pre_detail, 300)} | "
            f"POST={'OK' if post_ok else 'ALRM'}:{_trim(post_detail, 300)}"
        )
        data = (
            f"DFWIN: value_col={value_col!r} start_hour={start_hour_i} num_hours_eff={num_hours_eff} "
            f"output={output} binary_only_01={binary_only_01} stage=POST"
        )
        _bridge_publish_if_needed(alarm=True, desc=desc, data=data)

    return out


__all__ = [
    "df_to_ordered_window_API",
]

