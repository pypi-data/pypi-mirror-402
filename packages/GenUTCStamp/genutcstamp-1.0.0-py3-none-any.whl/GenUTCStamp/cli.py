"""Command-line entry points."""

from __future__ import annotations

import argparse

from . import utc_ts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Print a UTC timestamp in YYYY-MM-DDTHH:MM:SSZ format.")
    p.add_argument("--n", type=int, default=1, help="How many timestamps to print (default: 1).")
    args = p.parse_args(argv)

    n = args.n if args.n and args.n > 0 else 1
    for _ in range(n):
        print(utc_ts())
    return 0
