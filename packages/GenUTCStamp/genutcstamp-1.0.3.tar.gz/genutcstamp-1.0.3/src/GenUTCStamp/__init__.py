"""
GenUTCStamp — dependency-free UTC timestamp helper.

Returns a UTC timestamp string formatted as:

    YYYY-MM-DDTHH:MM:SSZ

This is ISO 8601 compatible and commonly accepted as an RFC 3339-style timestamp
("Zulu" suffix Z). Implementation uses only the Python standard library `time` module.

Canonical import:
    import GenUTCStamp as utc

Compatibility import (v1.0.1+):
    import genutcstamp as utc

All public functions are convenience aliases returning the same formatted string.
On unexpected runtime failures, returns: 1970-01-01T00:00:00Z
"""

from __future__ import annotations

import time as _time


def GenerateUTCTimestampPortable() -> str:
    try:
        return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
    except Exception:
        # Defensive fallback (should not happen under normal conditions)
        return "1970-01-01T00:00:00Z"


# Public aliases (intentionally redundant for ergonomics)
def utc_ts() -> str:
    return GenerateUTCTimestampPortable()


def GenerateUTCTimestamp() -> str:
    return GenerateUTCTimestampPortable()


def GenerateTimestamp() -> str:
    return GenerateUTCTimestampPortable()


def gen_ts() -> str:
    return GenerateUTCTimestampPortable()


def GenTs() -> str:
    return GenerateUTCTimestampPortable()


def gen_utc() -> str:
    return GenerateUTCTimestampPortable()


def GenerUTC() -> str:
    return GenerateUTCTimestampPortable()


def GenUTC() -> str:
    return GenerateUTCTimestampPortable()


def GenUTCToString() -> str:
    return GenerateUTCTimestampPortable()


def gen_utc_str() -> str:
    return GenerateUTCTimestampPortable()


def UTCToString() -> str:
    return GenerateUTCTimestampPortable()


def utc_to_str_threadsafe() -> str:
    return GenerateUTCTimestampPortable()


def GenUTCStamp() -> str:
    return GenerateUTCTimestampPortable()


__all__ = [
    "GenerateUTCTimestampPortable",
    "utc_ts",
    "GenerateUTCTimestamp",
    "GenerateTimestamp",
    "gen_ts",
    "GenTs",
    "gen_utc",
    "GenerUTC",
    "GenUTC",
    "GenUTCToString",
    "gen_utc_str",
    "UTCToString",
    "utc_to_str_threadsafe",
    "GenUTCStamp",
]
