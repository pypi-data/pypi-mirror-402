import re
import time
import unittest

import GenUTCStamp as utc


ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class TestUtcTimestampPortable(unittest.TestCase):
    def test_format(self):
        s = utc.utc_ts()
        self.assertIsInstance(s, str)
        self.assertRegex(s, ISO_Z_RE)

    def test_parseable(self):
        s = utc.utc_ts()
        # Must be parseable by strptime with the same layout.
        time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

    def test_aliases_match_format(self):
        fns = [
            utc.GenerateUTCTimestampPortable,
            utc.utc_ts,
            utc.GenerateUTCTimestamp,
            utc.GenerateTimestamp,
            utc.gen_ts,
            utc.GenTs,
            utc.gen_utc,
            utc.GenerUTC,
            utc.GenUTC,
            utc.GenUTCStamp,
            utc.GenUTCToString,
            utc.gen_utc_str,
            utc.UTCToString,
            utc.utc_to_str_threadsafe,
        ]
        for fn in fns:
            out = fn()
            self.assertIsInstance(out, str)
            self.assertRegex(out, ISO_Z_RE)

    def test_internal_callable(self):
        # Not part of __all__, but explicitly callable.
        self.assertTrue(callable(getattr(utc, "_utc_ts")))
        self.assertRegex(utc._utc_ts(), ISO_Z_RE)


if __name__ == "__main__":
    unittest.main()
