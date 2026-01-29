import os
import logging
import html as _html
from datetime import datetime

TRAP_PF_ENV = "PBM_TRAP_PORTFOLIO"

COL_SPECS_RB = [
    ("CET Delivery Start", ("CET Delivery Start",)),
    ("RB Forecast", ("RB Forecast",)),
]

COL_SPECS_OZE = [
    ("cet_datetime", ("cet_datetime",)),
    ("position", ("position",)),
]


def utc_ts():
    import time as _time
    try:
        return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(_time.time()))
    except Exception:
        return "1970-01-01T00:00:00Z"


def _utc_ts():
    return utc_ts()


def _norm_iter_tag(tag):
    import time as _time
    try:
        s = str(tag).strip()
    except Exception:
        s = ""

    if not s:
        return utc_ts()

    s = s.replace(" ", "T", 1)
    if "." in s:
        s = s.split(".", 1)[0]

    if s.endswith("Z"):
        try:
            _time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
            return s
        except Exception:
            return utc_ts()

    try:
        _time.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return s + "Z"
    except Exception:
        return utc_ts()



def _safe_str(x):
    try:
        return str(x)
    except Exception:
        return "<unprintable>"


def _fmt_hhmm(v):
    try:
        if v is None:
            return "None"
        if hasattr(v, "strftime"):
            return v.strftime("%H:%M")
        s = str(v).strip()
        if "T" in s:
            s = s.split("T", 1)[1]
        elif " " in s:
            s = s.split(" ", 1)[1]
        return s[:5] if len(s) >= 5 else s
    except Exception:
        return _safe_str(v)


def _trim(s, n):
    try:
        s = (s or "").strip()
        if not s:
            return ""
        if n and len(s) > n:
            return s[:n] + "..."
        return s
    except Exception:
        return ""


def _env_get(key, default=""):
    try:
        return os.getenv(key, default)
    except Exception:
        return default


def _env_set(key, value):
    try:
        os.environ[key] = _safe_str(value)
    except Exception:
        pass


def _log_warn(msg):
    try:
        logging.warning(msg)
    except Exception:
        pass


def _norm_pf(pf):
    pf = (pf or "").strip()
    if pf:
        return pf
    pf = _env_get(TRAP_PF_ENV, "").strip()
    return pf if pf else "UNKNOWN"


def _norm_kind(kind):
    k = (kind or "").strip().upper()
    return k if k else "UNKNOWN"


def _trap_status_norm(st):
    s = (st or "").strip().upper()
    if s in ("OK", "ALRM"):
        return s
    return "UNKNOWN"


def _find_col(df, candidates):
    try:
        cols = list(getattr(df, "columns", []))
        if not cols:
            return None
        for c in candidates:
            if c in cols:
                return c
        lower_map = {}
        for col in cols:
            lower_map[_safe_str(col).strip().lower()] = col
        for c in candidates:
            key = _safe_str(c).strip().lower()
            if key in lower_map:
                return lower_map[key]
        return None
    except Exception:
        return None


def extract_cols_map(df, col_specs, max_items=120):
    cols_map = {}
    missing_any = False
    mode = (_env_get("PBM_DATA_TIME_MODE", "omit") or "omit").strip().lower()
    time_labels = set(("CET Delivery Start", "cet_datetime"))

    for label, candidates in (col_specs or []):
        try:
            if mode == "omit" and label in time_labels:
                continue

            if df is None:
                cols_map[label] = None
                missing_any = True
                continue
            if getattr(df, "empty", False):
                cols_map[label] = []
                continue

            col = _find_col(df, candidates)
            if col is None:
                cols_map[label] = None
                missing_any = True
                continue

            vals = df[col].tolist()
            if max_items and len(vals) > max_items:
                vals = vals[:max_items]

            if mode == "hm" and label in time_labels:
                cols_map[label] = [_fmt_hhmm(v) for v in vals]
            else:
                cols_map[label] = [_safe_str(v) for v in vals]

        except Exception:
            cols_map[label] = None
            missing_any = True

    return cols_map, missing_any


def _cols_map_to_inline(cols_map):
    try:
        if not cols_map:
            return "(missing)"
        parts = []
        for k, v in cols_map.items():
            if v is None:
                parts.append("%s=(missing)" % _safe_str(k))
            else:
                parts.append("%s=%s" % (_safe_str(k), _safe_str(v)))
        return " | ".join(parts) if parts else "(missing)"
    except Exception:
        return "(missing)"


def _kv(label, value):
    return "%s: %s" % (_safe_str(label), _safe_str(value))


def _line(prefix, fields):
    return prefix + "  " + "  ".join(fields) if fields else prefix


def read_trap_state(pf, kind):
    pf = _norm_pf(pf)
    kind = _norm_kind(kind)
    base = "PBM_TRAP_%s_%s" % (pf, kind)
    st = _env_get(base, "").strip()
    desc = _env_get(base + "_D", "").strip()
    return st, desc


def compute_overall(trap_status, desc_missing, cols_missing):
    ts = _trap_status_norm(trap_status)
    if ts == "ALRM":
        return "ALRM", []
    reasons = []
    if ts == "UNKNOWN":
        reasons.append("trap status missing/unknown")
    if desc_missing:
        reasons.append("checks descriptor missing")
    if cols_missing:
        reasons.append("expected column(s) missing")
    if ts == "OK" and not reasons:
        return "OK", []
    return "CAUT", reasons


def build_status_text(pf, kind, trap_status, desc, overall, reasons, cols_map):
    pf = _norm_pf(pf)
    kind = _norm_kind(kind)
    ts = _trap_status_norm(trap_status)
    d = (desc or "").strip()
    head = "SYSTEM STATUS REPORT" if overall == "OK" else "SYSTEM ALARM"
    lines = [
        head,
        _kv("UTC", _utc_ts()),
        _kv("FOLIO", pf),
        _kv("KIND", kind),
        _kv("TRAP_STATUS", ts),
        _kv("STATUS", overall),
        _kv("CHECKS", (d if d else "(missing)")),
        _kv("DATA", _cols_map_to_inline(cols_map)),
    ]
    if overall == "CAUT" and reasons:
        lines.append(_kv("CAUT_REASONS", reasons))
    return "\n".join(lines)


def _cache_keys(pf, kind):
    pf = _norm_pf(pf)
    kind = _norm_kind(kind)
    base = "PBM_CACHE_%s_%s" % (pf, kind)
    return {
        "BASE": base,
        "TS": base + "_TS",
        "OVERALL": base + "_OVERALL",
        "TRAP": base + "_TRAP",
        "DESC": base + "_DESC",
        "DATA": base + "_DATA",
        "TEXT": "PBM_LAST_%s_%s_TEXT" % (pf, kind),
        "TEXT_TS": "PBM_LAST_%s_%s_TS" % (pf, kind),
        "HELPER_TEXT": "PBM_HELPER_LAST_%s_%s_TEXT" % (pf, kind),
        "HELPER_TS": "PBM_HELPER_LAST_%s_%s_TS" % (pf, kind),
    }


def cache_snapshot_text(pf, kind, text, max_chars=12000):
    try:
        ks = _cache_keys(pf, kind)
        t = (text or "").strip()
        if not t:
            return
        if len(t) > max_chars:
            t = t[:max_chars] + "\n...(truncated)"
        _env_set(ks["TEXT"], t)
        _env_set(ks["TEXT_TS"], _utc_ts())
    except Exception:
        pass


def read_cached_snapshot_text(pf, kind, default="(missing)"):
    ks = _cache_keys(pf, kind)
    return _env_get(ks["TEXT"], default)


def read_cached_snapshot_ts(pf, kind, default="(unset)"):
    ks = _cache_keys(pf, kind)
    return _env_get(ks["TEXT_TS"], default)


def cache_helper_alarm_text(pf, kind, text, max_chars=12000):
    try:
        ks = _cache_keys(pf, kind)
        t = (text or "").strip()
        if not t:
            return
        if len(t) > max_chars:
            t = t[:max_chars] + "\n...(truncated)"
        _env_set(ks["HELPER_TEXT"], t)
        _env_set(ks["HELPER_TS"], _utc_ts())
    except Exception:
        pass


def read_cached_helper_alarm_text(pf, kind, default=""):
    ks = _cache_keys(pf, kind)
    return _env_get(ks["HELPER_TEXT"], default)


def snapshot_cache_log(pf, kind, df, col_specs, max_items=120, prefer_env=True, status=None, desc=None, log_always=True):
    pf = _norm_pf(pf)
    kind = _norm_kind(kind)
    st_env, desc_env = read_trap_state(pf, kind)
    st_in = status if status is not None else (st_env if prefer_env else "")
    desc_in = desc if desc is not None else (desc_env if prefer_env else "")
    cols_map, cols_missing = extract_cols_map(df, col_specs, max_items=max_items)
    desc_missing = not (desc_in or "").strip()
    overall, reasons = compute_overall(st_in, desc_missing, cols_missing)
    msg = build_status_text(pf, kind, st_in, desc_in, overall, reasons, cols_map)

    ks = _cache_keys(pf, kind)
    _env_set(ks["TS"], _utc_ts())
    _env_set(ks["OVERALL"], overall)
    _env_set(ks["TRAP"], _trap_status_norm(st_in))
    _env_set(ks["DESC"], _trim(desc_in if desc_in else "(missing)", 600))
    _env_set(ks["DATA"], _cols_map_to_inline(cols_map))

    cache_snapshot_text(pf, kind, msg)
    if log_always:
        _log_warn(msg)
    return msg, overall


def emit_helper_alarm(pf, kind, stage, exc):
    try:
        pf = _norm_pf(pf)
        kind = _norm_kind(kind)
        st, d = read_trap_state(pf, kind)
        lines = [
            "SYSTEM ALARM",
            _kv("UTC", _utc_ts()),
            _kv("FOLIO", pf),
            _kv("KIND", kind),
            _kv("STAGE", stage),
            _kv("TRAP_STATUS", _trap_status_norm(st)),
            _kv("CHECKS", (d if d else "(missing)")),
            _kv("EXC", "%s: %s" % (type(exc).__name__, _safe_str(exc))),
        ]
        msg = "\n".join(lines)
        cache_helper_alarm_text(pf, kind, msg)
        _log_warn(msg)
        return msg
    except Exception:
        return ""


class alarm_passthru(object):
    """
    Hard backstop: ignore all args/kwargs and route exceptions to external_passthru
    with a static stage string.
    """

    _STAGE = "HELPER_PASSTHRU_STATIC"

    def __init__(self, *args, **kwargs):
        

        self._delegate = external_passthru(self._STAGE)

    def __enter__(self):
        return self._delegate.__enter__()

    def __exit__(self, exc_type, exc, tb):
        return self._delegate.__exit__(exc_type, exc, tb)



def _external_env_get(key, default=""):
    v = _env_get(key, "")
    if v:
        return v
    if key.startswith("PBM_EXTERNAL_"):
        legacy = "PBM_DRIVEBY_" + key[len("PBM_EXTERNAL_"):]
        v2 = _env_get(legacy, "")
        return v2 if v2 else default
    return default


def _external_env_set(key, value):
    _env_set(key, value)
    if key.startswith("PBM_EXTERNAL_"):
        legacy = "PBM_DRIVEBY_" + key[len("PBM_EXTERNAL_"):]
        _env_set(legacy, value)

def _ensure_external_iter_tag(iter_tag=None):
    try:
        raw = iter_tag if iter_tag is not None else _external_env_get("PBM_EXTERNAL_ITER", "")
    except Exception:
        raw = iter_tag
    it = _norm_iter_tag(raw)
    _external_env_set("PBM_EXTERNAL_ITER", it)
    return it


def external_reset(iter_tag=None, pfs=("PCPOL", "PCAGR"), kinds=("RB", "OZE"), clear_helper=True):
    try:
        it = _ensure_external_iter_tag(iter_tag)

        prev_state = (_external_env_get("PBM_EXTERNAL_STATE", "") or "").strip().upper()

        # Always reset state/iter for the new iteration
        _external_env_set("PBM_EXTERNAL_STATE", "OK")
        _external_env_set("PBM_EXTERNAL_ITER", it)

        # Clear helper alarms to prevent stickiness across healthy iterations
        if clear_helper:
            for pf in (pfs or ()):
                for kind in (kinds or ()):
                    ks = _cache_keys(pf, kind)
                    _env_set(ks["HELPER_TEXT"], "")
                    _env_set(ks["HELPER_TS"], "")

        if prev_state == "ALRM":
            rec_lines = [
                "EXTERNAL EXCEPTION RECOVERED",
                "note: recovered after exception - check logs or prior alerts",
            ]
            _external_env_set("PBM_EXTERNAL_LAST_TEXT", "\n".join(rec_lines))
            _external_env_set("PBM_EXTERNAL_LAST_TS", _utc_ts())
        else:
            _external_env_set("PBM_EXTERNAL_LAST_TEXT", "")
            _external_env_set("PBM_EXTERNAL_LAST_TS", "")
    except Exception:
        pass
 


def external_state():
    try:
        return (_external_env_get("PBM_EXTERNAL_STATE", "") or "").strip().upper()
    except Exception:
        return "ALRM"


def external_alarm(stage, exc, iter_tag=None):
    try:
        it = _ensure_external_iter_tag(iter_tag)
        lines = [
            "EXTERNAL EXCEPTION ALARM",
            _kv("UTC", _utc_ts()),
            _kv("ITER", (it if it else "(unset)")),
            _kv("STAGE", stage),
            _kv("EXC", "%s: %s" % (type(exc).__name__, _safe_str(exc))),
        ]
        msg = "\n".join(lines)
        _external_env_set("PBM_EXTERNAL_STATE", "ALRM")
        _external_env_set("PBM_EXTERNAL_LAST_TEXT", msg)
        _external_env_set("PBM_EXTERNAL_LAST_TS", _utc_ts())
        _log_warn(msg)
        return msg
    except Exception:
        return ""


def read_external_text(default=""):
    return _external_env_get("PBM_EXTERNAL_LAST_TEXT", default)


def read_external_ts(default="(unset)"):
    return _external_env_get("PBM_EXTERNAL_LAST_TS", default)


class external_passthru(object):
    def __init__(self, stage, iter_tag=None):
        self.stage = _safe_str(stage)
        self.iter_tag = _ensure_external_iter_tag(iter_tag)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            external_alarm(self.stage, exc, iter_tag=self.iter_tag)
        return False
 


def driveby_reset(iter_tag=None):
    return external_reset(iter_tag=iter_tag)


def driveby_state():
    return external_state()


def driveby_alarm(stage, exc, iter_tag=None):
    return external_alarm(stage=stage, exc=exc, iter_tag=iter_tag)


def read_driveby_text(default=""):
    return read_external_text(default=default)


class driveby_passthru(external_passthru):
    pass


def any_alarm(pfs=("PCPOL", "PCAGR"), kinds=("RB", "OZE"), include_caut=True):
    try:
        # External path
        ext = external_state()
        if include_caut:
            if ext != "OK":
                return True
        else:
            if ext == "ALRM":
                return True

        # Per-folio/kind path
        for pf in pfs:
            for kind in kinds:
                kd = _kind_cache(pf, kind, include_caut=include_caut)
                if kd.get("STATUS", "CAUT") != "OK":
                    return True

        return False
    except Exception:
        return True



def _kind_cache(pf, kind, include_caut):
    pf = _norm_pf(pf)
    kind = _norm_kind(kind)
    ks = _cache_keys(pf, kind)

    trap_st, trap_desc = read_trap_state(pf, kind)
    trap = _trap_status_norm(trap_st)
    desc = _env_get(ks["DESC"], "").strip() or (trap_desc.strip() if trap_desc else "")
    data = _env_get(ks["DATA"], "").strip()
    overall = _env_get(ks["OVERALL"], "").strip().upper()
    ts = _env_get(ks["TS"], "").strip()

    cache_present = bool(ts) and bool(data) and bool(overall)
    if not cache_present and include_caut:
        overall = "CAUT"

    if overall not in ("OK", "CAUT", "ALRM"):
        overall = "CAUT" if include_caut else "OK"

    if trap == "ALRM":
        overall = "ALRM"

    if not desc:
        desc = "(missing)"
        if include_caut and overall == "OK":
            overall = "CAUT"

    if not data:
        data = "(missing)"
        if include_caut and overall == "OK":
            overall = "CAUT"

    if not ts:
        ts = "(unset)"

    helper = read_cached_helper_alarm_text(pf, kind, default="").strip()

    return {
        "FOLIO": pf,
        "KIND": kind,
        "STATUS": overall,
        "TRAP": trap,
        "CHECKS": _trim(desc, 600),
        "DATA": data,
        "TS": ts,
        "HELPER": helper,
    }


def _default_post_html():
    v = (_env_get("PBM_POST_FORMAT", "html") or "html").strip().lower()
    return v in ("1", "true", "yes", "y", "html", "htm")


def _default_html_doc():
    v = (_env_get("PBM_POST_HTML_DOC", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _html_document_from_lines(lines, title=None):
    t = _html.escape((title or "PowerBot Alert").strip() or "PowerBot Alert")
    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>%s</title>" % t,
        "</head>",
        "<body>",
        '<div style="font-family:Consolas,Menlo,Monaco,monospace;font-size:12px;line-height:1.35">',
    ]

    for line in (lines or []):
        s = _safe_str(line)
        if s == "":
            parts.append("<br>")
        else:
            parts.append(_html.escape(s) + "<br>")

    parts.extend(["</div>", "</body>", "</html>"])
    return "".join(parts)


def _render(lines, as_html, html_doc, title=None):
    if as_html:
        if html_doc:
            return _html_document_from_lines(lines, title=title)
        esc = []
        for line in (lines or []):
            s = _safe_str(line)
            esc.append("<br>" if s == "" else (_html.escape(s) + "<br>"))
        return "".join(esc).strip()
    return "\n".join([_safe_str(x) for x in (lines or [])]).strip()


def build_post_text_from_cache(
    pfs=("PCPOL", "PCAGR"),
    kinds=("RB", "OZE"),
    include_ok=True,
    include_caut=True,
    include_external=True,
    include_helper=True,
    as_html=None,
    html_doc=None,
    html_title=None,
):
    time_mode = (_env_get("PBM_DATA_TIME_MODE", "omit") or "omit").strip().lower()
    try:
        kinds = tuple(_norm_kind(k) for k in (kinds or ()))
        if not kinds:
            kinds = ("RB", "OZE")

        if as_html is None:
            as_html = _default_post_html()
        if html_doc is None:
            html_doc = _default_html_doc()

        pf_blocks = []
        folio_ok_n = 0
        folio_caut_n = 0
        folio_alrm_n = 0

        ext_state = "OK"
        ext_text = ""
        ext_ts = "(unset)"
        if include_external:
            ext_state = external_state()
            ext_text = read_external_text(default="").strip()
            ext_ts = read_external_ts(default="(unset)")
            if ext_state not in ("OK", "ALRM", "CAUT"):
                ext_state = "CAUT" if include_caut else "OK"

        for pf in pfs:
            pf = _norm_pf(pf)
            kmap = {}
            pf_state = "OK"
            for kind in kinds:
                kd = _kind_cache(pf, kind, include_caut)
                kmap[kind] = kd
                if kd["STATUS"] == "ALRM":
                    pf_state = "ALRM"
                elif kd["STATUS"] == "CAUT" and pf_state != "ALRM":
                    pf_state = "CAUT"
            pf_blocks.append((pf, pf_state, kmap))
            if pf_state == "ALRM":
                folio_alrm_n += 1
            elif pf_state == "CAUT":
                folio_caut_n += 1
            else:
                folio_ok_n += 1

        overall = "OK"
        if folio_alrm_n or (include_external and ext_state == "ALRM"):
            overall = "ALRM"
        elif folio_caut_n or (include_external and ext_state == "CAUT"):
            overall = "CAUT"

        lines = []
        lines.append("SYSTEM STATUS REPORT" if overall == "OK" else "SYSTEM ALARM")
        lines.append(_kv("UTC", _utc_ts()))
        lines.append(
            _line(
                "SUMMARY",
                [
                    _kv("STATUS", overall),
                    _kv("folios_ok", folio_ok_n),
                    _kv("folios_caut", folio_caut_n),
                    _kv("folios_alrm", folio_alrm_n),
                    (_kv("external", ext_state) if include_external else _kv("external", "(disabled)")),
                    _kv("time_mode", time_mode),
                ],
            )
        )
        lines.append("")

        if include_external:
            if ext_state == "OK" and not ext_text:
                lines.append(_line("EXTERNAL", [_kv("STATUS", "OK"), "note: no external exception recorded"]))
            elif ext_state == "OK" and ext_text:
                lines.append(_line("EXTERNAL", [_kv("STATUS", "OK"), _kv("TS", ext_ts), "note: text present"]))
            elif ext_state == "ALRM":
                lines.append(_line("EXTERNAL", [_kv("STATUS", "ALRM"), _kv("TS", ext_ts), "note: external exception recorded"]))
            else:
                lines.append(_line("EXTERNAL", [_kv("STATUS", ext_state), _kv("TS", ext_ts)]))

            if ext_text and (include_ok or ext_state != "OK"):
                lines.append("EXTERNAL_DETAIL: " + _trim(ext_text.replace("\n", " | "), 1200))
            lines.append("")

        for pf, pf_state, kmap in pf_blocks:
            rb = kmap.get("RB")
            oze = kmap.get("OZE")

            if rb and oze:
                lines.append(
                    _line(
                        "FOLIO",
                        [
                            _kv("name", pf),
                            _kv("STATUS", pf_state),
                            "RB: %s (trap: %s  ts: %s)" % (rb["STATUS"], rb["TRAP"], rb["TS"]),
                            "OZE: %s (trap: %s  ts: %s)" % (oze["STATUS"], oze["TRAP"], oze["TS"]),
                        ],
                    )
                )
                lines.append(_line("CHECKS", [_kv("FOLIO", pf), "RB: %s" % rb["CHECKS"]]))
                lines.append(_line("CHECKS", [_kv("FOLIO", pf), "OZE: %s" % oze["CHECKS"]]))
                lines.append(_line("DATA", [_kv("FOLIO", pf), "RB: %s" % rb["DATA"]]))
                lines.append(_line("DATA", [_kv("FOLIO", pf), "OZE: %s" % oze["DATA"]]))

                if include_helper:
                    hb = (rb.get("HELPER") or "").strip()
                    ho = (oze.get("HELPER") or "").strip()
                    if hb and (include_ok or pf_state != "OK"):
                        lines.append(_line("HELPER", [_kv("FOLIO", pf), "KIND: RB", _trim(hb.replace("\n", " | "), 900)]))
                    if ho and (include_ok or pf_state != "OK"):
                        lines.append(_line("HELPER", [_kv("FOLIO", pf), "KIND: OZE", _trim(ho.replace("\n", " | "), 900)]))
            else:
                parts = [_kv("name", pf), _kv("STATUS", pf_state)]
                for kind in kinds:
                    kd = kmap.get(kind)
                    if not kd:
                        parts.append("%s: CAUT" % _norm_kind(kind))
                    else:
                        parts.append("%s: %s" % (kd["KIND"], kd["STATUS"]))
                lines.append(_line("FOLIO", parts))
                for kind in kinds:
                    kd = kmap.get(kind)
                    if kd:
                        lines.append(_line("CHECKS", [_kv("FOLIO", pf), "%s: %s" % (kd["KIND"], kd["CHECKS"])]))
                        lines.append(_line("DATA", [_kv("FOLIO", pf), "%s: %s" % (kd["KIND"], kd["DATA"])]))

            lines.append("")

        out = _render(lines, as_html=as_html, html_doc=html_doc, title=(html_title or "PowerBot Alert Package"))
        if out:
            return out

        fallback_lines = [
            "SYSTEM ALARM",
            _kv("UTC", _utc_ts()),
            _line(
                "SUMMARY",
                [
                    _kv("STATUS", "ALRM"),
                    _kv("folios_ok", 0),
                    _kv("folios_caut", 0),
                    _kv("folios_alrm", 1),
                    (_kv("external", "(unknown)") if include_external else _kv("external", "(disabled)")),
                    _kv("time_mode", time_mode),
                ],
            ),
        ]
        return _render(fallback_lines, as_html=as_html, html_doc=html_doc, title=(html_title or "PowerBot Alert Package"))
    except Exception as e:
        if as_html is None:
            as_html = _default_post_html()
        if html_doc is None:
            html_doc = _default_html_doc()
        err_lines = [
            "SYSTEM ALARM",
            _kv("UTC", _utc_ts()),
            _line(
                "SUMMARY",
                [
                    _kv("STATUS", "ALRM"),
                    _kv("folios_ok", 0),
                    _kv("folios_caut", 0),
                    _kv("folios_alrm", 1),
                    (_kv("external", "ALRM") if include_external else _kv("external", "(disabled)")),
                    _kv("time_mode", time_mode),
                ],
            ),
            "HELPER: builder_exception %s: %s" % (type(e).__name__, _safe_str(e)),
        ]
        return _render(err_lines, as_html=as_html, html_doc=html_doc, title=(html_title or "PowerBot Alert Package"))


def build_system_exception_text(exc, pfs=("PCPOL", "PCAGR"), kinds=("RB", "OZE"), as_html=True, html_doc=True, html_title=None):
    time_mode = (_env_get("PBM_DATA_TIME_MODE", "omit") or "omit").strip().lower()
    try:
        kinds = tuple(_norm_kind(k) for k in (kinds or ()))
        if not kinds:
            kinds = ("RB", "OZE")

        if as_html is None:
            as_html = _default_post_html()
        if html_doc is None:
            html_doc = _default_html_doc()

        lines = [
            "SYSTEM ALARM",
            _kv("UTC", _utc_ts()),
            _kv("TIME_MODE", time_mode),
            "ERR: %s: %s" % (type(exc).__name__, _safe_str(exc)),
            "",
        ]

        ex = read_external_text(default="").strip()
        if ex:
            lines.append(_line("EXTERNAL", [_kv("STATUS", external_state()), _kv("TS", read_external_ts(default="(unset)")), "note: external exception recorded"]))
            lines.append("EXTERNAL_DETAIL: " + _trim(ex.replace("\n", " | "), 1200))
        else:
            lines.append(_line("EXTERNAL", [_kv("STATUS", external_state()), "note: no external exception recorded"]))
        lines.append("")

        for pf in pfs:
            pf = _norm_pf(pf)
            rb = _kind_cache(pf, "RB", include_caut=True) if "RB" in kinds else None
            oze = _kind_cache(pf, "OZE", include_caut=True) if "OZE" in kinds else None

            pf_state = "OK"
            for kd in (rb, oze):
                if not kd:
                    continue
                if kd["STATUS"] == "ALRM":
                    pf_state = "ALRM"
                elif kd["STATUS"] == "CAUT" and pf_state != "ALRM":
                    pf_state = "CAUT"

            if rb and oze:
                lines.append(
                    _line(
                        "FOLIO",
                        [
                            _kv("name", pf),
                            _kv("STATUS", pf_state),
                            "RB: %s (trap: %s  ts: %s)" % (rb["STATUS"], rb["TRAP"], rb["TS"]),
                            "OZE: %s (trap: %s  ts: %s)" % (oze["STATUS"], oze["TRAP"], oze["TS"]),
                        ],
                    )
                )
                lines.append(_line("CHECKS", [_kv("FOLIO", pf), "RB: %s" % rb["CHECKS"]]))
                lines.append(_line("CHECKS", [_kv("FOLIO", pf), "OZE: %s" % oze["CHECKS"]]))
                lines.append(_line("DATA", [_kv("FOLIO", pf), "RB: %s" % rb["DATA"]]))
                lines.append(_line("DATA", [_kv("FOLIO", pf), "OZE: %s" % oze["DATA"]]))
            else:
                parts = [_kv("name", pf), _kv("STATUS", pf_state)]
                for kind in kinds:
                    kd = _kind_cache(pf, kind, include_caut=True)
                    parts.append("%s: %s" % (kd["KIND"], kd["STATUS"]))
                lines.append(_line("FOLIO", parts))

            lines.append("")

        return _render(lines, as_html=as_html, html_doc=html_doc, title=(html_title or "PowerBot System Alarm"))
    except Exception:
        if as_html is None:
            as_html = _default_post_html()
        if html_doc is None:
            html_doc = _default_html_doc()
        return _render(
            [
                "SYSTEM ALARM",
                _kv("UTC", _utc_ts()),
                _kv("TIME_MODE", time_mode),
                "ERR: (unknown)",
            ],
            as_html=as_html,
            html_doc=html_doc,
            title=(html_title or "PowerBot System Alarm"),
        )

