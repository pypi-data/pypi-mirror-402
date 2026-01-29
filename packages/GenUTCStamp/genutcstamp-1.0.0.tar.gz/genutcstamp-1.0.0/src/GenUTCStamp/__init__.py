"""utc_timestamp_portable

A tiny, dependency-free helper for generating an RFC 3339 / ISO 8601-style UTC timestamp
string in the form: ``YYYY-MM-DDTHH:MM:SSZ``.

Public API (all are aliases of the same implementation):

- GenerateUTCTimestampPortable
- utc_ts
- GenerateUTCTimestamp
- GenerateTimestamp
- gen_ts
- GenTs
- gen_utc
- GenerUTC
- GenUTC
- GenUTCToString
- gen_utc_str
- UTCToString
- utc_to_str_threadsafe
- GenUTCStamp


This package is intentionally minimal: it uses only the standard library ``time`` module.
"""

from __future__ import annotations


def GenerateUTCTimestampPortable() -> str:
    import time as _time
    try:
        return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(_time.time()))
    except Exception:
        return "1970-01-01T00:00:00Z"

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



def _utc_ts() -> str:
    return utc_ts()


def _utc_ts() -> str:
    return utc_ts()


def _utc_ts() -> str:
    return utc_ts()

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

#if __name__ == "__main__":
#    ts = GenerateUTCTimestampPortable()
#    import logging
#    logging.warning(ts)
