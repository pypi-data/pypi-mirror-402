"""
Compatibility shim.

Allows:
- import genutcstamp
- python -m genutcstamp

Re-exports the public API from the canonical package GenUTCStamp.
"""

from __future__ import annotations

import GenUTCStamp as _g
from GenUTCStamp import *  # noqa: F401,F403  (exports names in _g.__all__)
from GenUTCStamp.cli import main as _main

__all__ = _g.__all__


if __name__ == "__main__":
    raise SystemExit(_main())

