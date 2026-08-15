"""Smoke test: every project module imports cleanly.

Would have caught the campaign_automation.py:86 SyntaxError regression
that the verification audit found on 2026-07-15.
"""
import importlib
import sys
import unittest


PROJECT_MODULES = [
    "account_database",
    "api_dashboard",
    "campaign_automation",
    "main",
    "multi_account_manager",
    "profile_generator",
    "proxy_manager",
]


class SmokeImportTests(unittest.TestCase):
    def setUp(self):
        # Make sure the working tree is on the import path; the project
        # is laid out as a flat module directory, not a package.
        sys.path.insert(0, ".")

    def test_each_module_imports(self):
        for name in PROJECT_MODULES:
            with self.subTest(module=name):
                # import_module is enough — if this raises, the syntax
                # or top-level dependency is broken.
                importlib.import_module(name)


if __name__ == "__main__":
    unittest.main()
