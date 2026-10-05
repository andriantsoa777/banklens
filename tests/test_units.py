"""Tests unitaires sans entrepôt : le chaînage des soldes retrouve l'ordre réel des opérations d'un même jour."""
import unittest

import pandas as pd

from banklens.ledger import sequence_transactions


class TestLedger(unittest.TestCase):
    def test_recovers_intraday_order(self):
        # même jour, identifiants volontairement dans le désordre ; l'ordre réel est 12 -> 10 -> 11
        df = pd.DataFrame({
            "trans_id": [10, 11, 12],
            "account_id": [1, 1, 1],
            "tx_date": ["1995-01-01"] * 3,
            "signed_amount": [-50.0, +20.0, +100.0],
            "balance_after": [50.0, 70.0, 100.0],
        })
        out = sequence_transactions(df)
        self.assertEqual(out["trans_id"].tolist(), [12, 10, 11])
        self.assertEqual(out["tx_seq"].tolist(), [1, 2, 3])
        self.assertTrue(out["balance_chain_ok"].all())

    def test_real_break_is_flagged_not_hidden(self):
        df = pd.DataFrame({"trans_id": [1, 2], "account_id": [1, 1], "tx_date": ["1995-01-01", "1995-01-02"],
                           "signed_amount": [100.0, 10.0], "balance_after": [100.0, 500.0]})  # 100 + 10 != 500
        out = sequence_transactions(df)
        self.assertEqual(out["balance_chain_ok"].tolist(), [1, 0])
        self.assertAlmostEqual(out["balance_drift"].iloc[1], -390.0)

    def test_interest_rounding_tolerated(self):
        df = pd.DataFrame({"trans_id": [1, 2], "account_id": [1, 1], "tx_date": ["1995-01-01", "1995-01-02"],
                           "signed_amount": [100.0, 5.0], "balance_after": [100.0, 105.1]})
        self.assertTrue(sequence_transactions(df)["balance_chain_ok"].all())


if __name__ == "__main__":
    unittest.main()
