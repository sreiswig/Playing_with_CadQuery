"""In-memory tests for the fetch URL allow/deny core. No network."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS, model_url
from cq_artifacts.fetch_policy import (
    ALLOWED_RAW_PREFIX,
    AllowedFetch,
    FetchDeny,
    FetchDenyCode,
    check_fetch_url,
    fetch_deny_message,
)
from cq_artifacts.outcome import Err, Ok


class FetchPolicyTests(unittest.TestCase):
    def test_allows_catalog_raw_urls(self):
        for row in MODELS:
            for relpath in row["files"].values():
                url = model_url(relpath)
                with self.subTest(url=url):
                    found = check_fetch_url(url)
                    self.assertIsInstance(found, Ok)
                    self.assertIsInstance(found.value, AllowedFetch)
                    self.assertEqual(found.value.url, url)
                    self.assertTrue(url.startswith(ALLOWED_RAW_PREFIX))

    def test_allows_branch_ref_and_dot_segment(self):
        url = (
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            "some-branch/./artifacts/box/box.stl"
        )
        found = check_fetch_url(url)
        self.assertIsInstance(found, Ok)
        self.assertEqual(found.value.url, url)

    def test_query_string_on_allowed_path_stays_allowed(self):
        url = model_url("cat.step") + "?raw=1"
        found = check_fetch_url(url)
        self.assertIsInstance(found, Ok)
        self.assertEqual(found.value.url, url)

    def test_deny_codes(self):
        cases = (
            (None, FetchDenyCode.NOT_A_URL),
            ("", FetchDenyCode.NOT_A_URL),
            (
                "http://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step",
                FetchDenyCode.NOT_HTTPS,
            ),
            (
                "https://user:secret@raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step",
                FetchDenyCode.EMBEDDED_CREDENTIALS,
            ),
            ("https://evil.example/cat.step", FetchDenyCode.BAD_HOST),
            (
                "https://github.com/sreiswig/Playing_with_CadQuery/raw/main/cat.step",
                FetchDenyCode.BAD_HOST,
            ),
            (
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/../other-repo/main/x",
                FetchDenyCode.PATH_ESCAPE,
            ),
            (
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/%2e%2e/other-repo/main/x",
                FetchDenyCode.PATH_ESCAPE,
            ),
            (
                "https://raw.githubusercontent.com/sreiswig/other-repo/main/cat.step",
                FetchDenyCode.OFF_PREFIX,
            ),
            (
                "https://RAW.GITHUBUSERCONTENT.COM/sreiswig/Playing_with_CadQuery/main/cat.step",
                FetchDenyCode.BAD_HOST,
            ),
        )
        for url, code in cases:
            with self.subTest(url=url):
                found = check_fetch_url(url)
                self.assertIsInstance(found, Err)
                self.assertIsInstance(found.error, FetchDeny)
                self.assertIs(found.error.code, code)
                self.assertEqual(found.error.url, url)

    def test_deny_message_matches_edge_wording(self):
        url = "https://evil.example/cat.step"
        found = check_fetch_url(url)
        self.assertIsInstance(found, Err)
        self.assertEqual(
            fetch_deny_message(found.error),
            f"refusing fetch: {url!r} is not under {ALLOWED_RAW_PREFIX}",
        )

    def test_allowed_fetch_is_frozen(self):
        found = check_fetch_url(model_url("box.step"))
        self.assertIsInstance(found, Ok)
        with self.assertRaises(AttributeError):
            setattr(found.value, "url", "https://evil.example/box.step")
