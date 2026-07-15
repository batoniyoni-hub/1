"""AccountDatabase round-trip and init tests using a tempfile-based DB."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, ".")

from account_database import AccountDatabase, AccountStatus, PlatformType


class AccountDatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self._tmp, "accounts.db")
        self.db = AccountDatabase(db_path=self.db_path)

    def tearDown(self):
        # AccountDatabase opens fresh connections per call, so we just
        # need to release the file lock by removing the DB file.
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
        os.rmdir(self._tmp)

    def test_init_creates_accounts_table(self):
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            ).fetchone()
        self.assertEqual(row[0], "accounts")

    def test_add_then_get_account_roundtrip(self):
        account_id = self.db.add_account({
            "platform": PlatformType.FACEBOOK.value,
            "account_id": "fb-001",
            "username": "alice",
            "email": "alice@example.com",
            "email_password": "epw",
            "account_password": "apw",
            "status": AccountStatus.VALID.value,
            "country": "US",
        })
        self.assertIsInstance(account_id, int)
        fetched = self.db.get_account(account_id=account_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["email"], "alice@example.com")
        self.assertEqual(fetched["platform"], "facebook")
        self.assertEqual(fetched["status"], "valid")

    def test_get_account_by_email(self):
        self.db.add_account({
            "platform": PlatformType.FACEBOOK.value,
            "email": "bob@example.com",
            "email_password": "x",
            "account_password": "y",
            "status": AccountStatus.PENDING.value,
        })
        fetched = self.db.get_account(email="bob@example.com")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["account_id"], None)  # not provided


if __name__ == "__main__":
    unittest.main()
