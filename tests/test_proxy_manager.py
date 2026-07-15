"""ProxyDatabase and ProxyChecker tests, all without network I/O."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, ".")

from proxy_manager import ProxyDatabase, ProxyChecker


class ProxyDatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self._tmp, "proxies.db")
        self.db = ProxyDatabase(db_path=self.db_path)

    def tearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
        os.rmdir(self._tmp)

    def test_init_creates_proxies_table(self):
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='proxies'"
            ).fetchone()
        self.assertEqual(row[0], "proxies")

    def test_add_then_get_proxy_roundtrip(self):
        self.db.add_proxy("1.2.3.4:8080", country_code="US", protocol="http")
        proxy = self.db.get_proxy(country_code="US")
        self.assertEqual(proxy, "1.2.3.4:8080")


class ProxyCheckerFormatTests(unittest.TestCase):
    def setUp(self):
        self.checker = ProxyChecker(db=None)

    def test_valid_ipv4_port_formats(self):
        for valid in ["1.2.3.4:80", "10.0.0.1:65535", "255.255.255.255:1"]:
            with self.subTest(proxy=valid):
                self.assertTrue(self.checker.validate_proxy_format(valid))

    def test_invalid_formats(self):
        for bad in ["not-a-proxy", "1.2.3.4", "1.2.3.4:abc", "", "1.2.3:80"]:
            with self.subTest(proxy=bad):
                self.assertFalse(self.checker.validate_proxy_format(bad))


if __name__ == "__main__":
    unittest.main()
