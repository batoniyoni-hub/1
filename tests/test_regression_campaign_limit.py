"""Regression for the campaign_automation.py:86 SyntaxError.

The original line was:

    account_ids = [acc['id'] for acc in filtered_accounts[:limit] if limit else filtered_accounts]

which is not valid Python (an `if limit else X` expression cannot sit
inside the comprehension's `for ... in ...` clause). The file failed
to import, blocking every consumer of CampaignAutomation. The fix
splits the selection into a conditional expression and a comprehension.

This test exercises both branches (limit given, limit absent) of the
selection logic on a minimal in-memory dataset, so a future regression
on the same line would fail here.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, ".")

from account_database import AccountDatabase, AccountStatus, PlatformType
from campaign_automation import CampaignAutomation


def _seed_accounts(db, n):
    ids = []
    for i in range(n):
        ids.append(db.add_account({
            "platform": PlatformType.FACEBOOK.value,
            "email": f"u{i}@example.com",
            "email_password": "x",
            "account_password": "y",
            "status": AccountStatus.VALID.value,
            "country": "US",
            "trust_score": 0.9,
        }))
    # After seeding, update trust_score because the schema default may be 0.
    for aid in ids:
        db.update_account(aid, {"trust_score": 0.9})
    return ids


class CampaignAssignLimitRegression(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self._tmp, "accounts.db")
        self.db = AccountDatabase(db_path=self.db_path)
        _seed_accounts(self.db, 5)
        self.campaign = CampaignAutomation(db=self.db)
        self.cid = self.campaign.create_campaign(
            campaign_name="regression",
            campaign_type="engagement",
            platform="facebook",
            strategy="default",
        )

    def tearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass
        os.rmdir(self._tmp)

    def test_assign_with_limit(self):
        """When `limit=2` is passed, only two account IDs are returned."""
        result = self.campaign.assign_accounts_to_campaign(
            campaign_id=self.cid,
            country="US",
            min_trust_score=0.5,
            limit=2,
        )
        # Implementation chooses valid accounts in 'US'; with limit=2 we
        # expect at most 2 IDs back.
        self.assertLessEqual(len(result), 2)

    def test_assign_without_limit(self):
        """When `limit=None` is passed (default), all matching IDs are returned."""
        result = self.campaign.assign_accounts_to_campaign(
            campaign_id=self.cid,
            country="US",
            min_trust_score=0.5,
            limit=None,
        )
        self.assertEqual(len(result), 5)


if __name__ == "__main__":
    unittest.main()
