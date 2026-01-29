"""
Command-line interface for GenUTCStamp.

Examples:
  utc-ts
  utc-ts -n 5
  utc-ts --n 5   # backward compatible with v1.0.0
  python -m GenUTCStamp -n 3
  python -m genutcstamp -n 3
"""

from __future__ import annotations

import argparse

from . import utc_ts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="utc-ts",
        description="Print UTC timestamps formatted as YYYY-MM-DDTHH:MM:SSZ.",
    )
    p.add_argument(
        "-n",
        "--count",
        "--n",  # backward compatibility with v1.0.0
        dest="count",
        type=int,
        default=1,
        help="Number of timestamps to print (default: 1).",
    )
    args = p.parse_args(argv)

    if args.count < 1:
        p.error("count must be >= 1")

    for _ in range(args.count):
        print(utc_ts())

    return 0
