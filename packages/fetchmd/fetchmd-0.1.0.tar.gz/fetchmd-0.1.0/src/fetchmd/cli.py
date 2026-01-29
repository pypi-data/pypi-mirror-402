"""CLI entrypoint for fetchmd."""

from __future__ import annotations

import argparse
import sys

from .core import _fetchmd, html_to_markdown


def main(argv: list[str] | None = None) -> int:
    """Run the fetchmd CLI and print Markdown to stdout.

    Returns:
        Exit code.

    """
    parser = argparse.ArgumentParser(prog="fetchmd")
    parser.add_argument("url", help="URL or '-' to read HTML from stdin")
    parser.add_argument("--raw", action="store_true", help="Skip readability and convert full HTML")
    args = parser.parse_args(argv)

    if args.url == "-":
        html = sys.stdin.read()
        md = html_to_markdown(html, base_url=None, raw=args.raw)
        print(md)
        return 0

    md = _fetchmd(args.url, raw=args.raw)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
