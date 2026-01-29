# GenUTCStamp

A tiny, dependency-free Python utility that returns a UTC timestamp string in the form:

```
YYYY-MM-DDTHH:MM:SSZ
```

This format is ISO 8601 compatible and commonly accepted as an RFC 3339-style timestamp (UTC “Zulu” suffix `Z`). The implementation uses only the Python standard library `time` module.

## Why this package exists

You often may need a stable UTC timestamp string for:

- log lines and structured logs
- environment-variable status markers
- lightweight monitoring / alerting breadcrumbs
- file naming or report identifiers

When the goal is “a portable UTC timestamp string with no dependencies,” this package provides that.

## Installation

```bash
python -m pip install --upgrade pip
python -m pip install GenUTCStamp
```

## Quick usage

Note: Python imports are case-sensitive on Linux. `pip install GenUTCStamp` works regardless of casing, but `import GenUTCStamp` and `import genutcstamp` are different names. This project supports both.


```python
import genutcstamp as utc

print(utc.utc_ts())
# 2026-01-17T18:41:47Z
```

## API surface (aliases)

All public functions return the exact same value format and are simple aliases for convenience:

- `GenerateUTCTimestampPortable()`
- `utc_ts()`
- `GenerateUTCTimestamp()`
- `GenerateTimestamp()`
- `gen_ts()`
- `GenTs()`
- `gen_utc()`
- `GenerUTC()`
- `GenUTC()`
- `GenUTCToString()`
- `gen_utc_str()`
- `UTCToString()`
- `utc_to_str_threadsafe()`
- `GenUTCStamp()`



```python
import genutcstamp as utc2
print(utc2.utc_ts())
```


## Output guarantees

- Always returns a **string**.
- Normal path returns UTC time formatted as `YYYY-MM-DDTHH:MM:SSZ`.
- On unexpected runtime failures, returns a defensive fallback string: `1970-01-01T00:00:00Z`.

## Command line

This package optionally provides a small CLI:

```bash
utc-ts
utc-ts -n 5
utc-ts --n 5   # backward compatible with v1.0.0
```

## License

MIT
