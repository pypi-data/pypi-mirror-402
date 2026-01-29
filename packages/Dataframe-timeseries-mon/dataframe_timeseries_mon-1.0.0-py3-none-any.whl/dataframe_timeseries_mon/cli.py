"""CLI helpers.

This module is intentionally thin and side-effect free. It only reads envvars and prints.
"""

from __future__ import annotations

import argparse
import sys

from alerting_subsystem import build_post_text_from_cache


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dfmon-post",
        description="Render a monitoring post from PBM_CACHE/PBM_EXTERNAL envvars.",
    )
    p.add_argument("--text", action="store_true", help="Force plain-text output (no HTML).")
    p.add_argument("--html", action="store_true", help="Force HTML output.")
    p.add_argument("--html-doc", action="store_true", help="Wrap output in a full HTML document.")
    p.add_argument("--no-html-doc", action="store_true", help="Disable HTML document wrapping.")
    p.add_argument("--include-ok", action="store_true", default=False, help="Include OK folios in output.")
    p.add_argument("--no-external", action="store_true", help="Exclude external exception channel section.")
    p.add_argument("--no-helper", action="store_true", help="Exclude helper alarm section.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    as_html = None
    if args.text and args.html:
        print("ERROR: choose only one of --text / --html", file=sys.stderr)
        return 2
    if args.text:
        as_html = False
    if args.html:
        as_html = True

    html_doc = None
    if args.html_doc and args.no_html_doc:
        print("ERROR: choose only one of --html-doc / --no-html-doc", file=sys.stderr)
        return 2
    if args.html_doc:
        html_doc = True
    if args.no_html_doc:
        html_doc = False

    txt = build_post_text_from_cache(
        include_ok=bool(args.include_ok),
        include_external=not bool(args.no_external),
        include_helper=not bool(args.no_helper),
        as_html=as_html,
        html_doc=html_doc,
    )
    sys.stdout.write(txt)
    if not txt.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
