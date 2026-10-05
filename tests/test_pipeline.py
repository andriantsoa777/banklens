"""Tests de l'entrepôt : réconciliation, clés, intégrité référentielle, chiffres clés.

Usage :  python -m unittest discover -s tests -v      (après `make all`)
"""
import sqlite3
import unittest

from banklens.config import DB_PATH


class WarehouseCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise unittest.SkipTest("entrepôt absent : lancer `make all` d'abord")
        cls.con = sqlite3.connect(DB_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def one(self, sql):
        return self.con.execute(sql).fetchone()[0]


class TestReconciliation(WarehouseCase):
    """Aucune ligne ne disparaît sans trace : bronze = silver + quarantaine."""

    PAIRS = [("bronze_berka_trans", "silver_transaction", "berka", "transaction"),
             ("bronze_berka_account", "silver_account", "berka", "account"),
             ("bronze_berka_loan", "silver_loan", "berka", "loan"),
             ("bronze_berka_client", "silver_client", "berka", "client"),
             ("bronze_fraud_card_tx", "silver_card_tx", "fraud", "card_tx"),
             ("bronze_german_credit", "silver_credit_application", "german", "credit"),
             ("bronze_marketing_contact", "silver_marketing_contact", "marketing", "contact")]

    def test_bronze_equals_silver_plus_quarantine(self):
        for bronze, silver, src, tbl in self.PAIRS:
            with self.subTest(table=silver):
                b, s = self.one(f"SELECT COUNT(*) FROM {bronze}"), self.one(f"SELECT COUNT(*) FROM {silver}")
                q = self.one(f"SELECT COUNT(*) FROM quarantine WHERE source='{src}' AND tbl='{tbl}'")
                self.assertEqual(b, s + q)

    def test_load_log_matches_bronze(self):
        batch = self.one("SELECT MAX(batch_id) FROM meta_load_log")
        for src, tbl, rows in self.con.execute("SELECT source, tbl, rows_loaded FROM meta_load_log WHERE batch_id=?", (batch,)).fetchall():
            with self.subTest(table=f"{src}.{tbl}"):
                self.assertEqual(rows, self.one(f"SELECT COUNT(*) FROM bronze_{src}_{tbl}"))


class TestKeys(WarehouseCase):
    def test_primary_keys_are_unique(self):
        for table, key in [("dim_account", "account_key"), ("dim_client", "client_key"), ("dim_district", "district_key"),
                           ("dim_date", "date_key"), ("fact_loan", "loan_key"), ("fact_transaction", "transaction_key"),
                           ("fact_card_tx", "transaction_key"), ("dim_card", "card_key")]:
            with self.subTest(table=table):
                self.assertEqual(self.one(f"SELECT COUNT(*) FROM {table}"), self.one(f"SELECT COUNT(DISTINCT {key}) FROM {table}"))

    def test_account_month_grain(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM (SELECT account_key, year_month FROM fact_account_month GROUP BY 1,2 HAVING COUNT(*)>1)"), 0)

    def test_no_orphan_foreign_keys(self):
        for child, col, parent, pkey in [("fact_transaction", "account_key", "dim_account", "account_key"),
                                         ("fact_transaction", "date_key", "dim_date", "date_key"),
                                         ("fact_transaction", "tx_type_key", "dim_tx_type", "tx_type_key"),
                                         ("fact_account_month", "account_key", "dim_account", "account_key"),
                                         ("fact_loan", "account_key", "dim_account", "account_key"),
                                         ("fact_card_tx", "hour_key", "dim_hour", "hour_key"),
                                         ("dim_account", "district_key", "dim_district", "district_key"),
                                         ("bridge_account_client", "client_key", "dim_client", "client_key"),
                                         ("dim_card", "account_key", "dim_account", "account_key")]:
            with self.subTest(fk=f"{child}.{col}"):
                orphans = self.one(f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON c.{col}=p.{pkey} WHERE c.{col} IS NOT NULL AND p.{pkey} IS NULL")
                self.assertEqual(orphans, 0)


class TestQuality(WarehouseCase):
    def test_no_blocking_rule_failed(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM dq_results WHERE status='FAIL'"), 0)

    def test_balance_chain_rate(self):
        rate = self.one("SELECT AVG(balance_chain_ok) FROM silver_transaction")
        self.assertGreaterEqual(rate, 0.999)

    def test_no_negative_amounts(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM fact_transaction WHERE amount < 0"), 0)

    def test_signed_amount_consistent(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM fact_transaction WHERE ABS(ABS(signed_amount) - amount) > 0.001"), 0)


class TestKeyFigures(WarehouseCase):
    """Chiffres de référence du jeu : un écart signale une régression du nettoyage ou du modèle."""

    def test_counts(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM dim_account"), 4500)
        self.assertEqual(self.one("SELECT COUNT(*) FROM fact_loan"), 682)
        self.assertEqual(self.one("SELECT COUNT(*) FROM fact_transaction"), 1056320)
        self.assertEqual(self.one("SELECT COUNT(*) FROM dim_district"), 77)

    def test_loan_defaults(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM fact_loan WHERE status_code IN ('B','D')"), 76)

    def test_fraud(self):
        self.assertEqual(self.one("SELECT SUM(is_fraud) FROM fact_card_tx"), 473)
        self.assertEqual(self.one("SELECT COUNT(*) FROM quarantine WHERE rule_id='F_DUP'"), 1081)

    def test_models_beat_naive_baseline(self):
        auc = self.one("SELECT valeur FROM ml_metrics WHERE modele='loan_default' AND metrique LIKE 'AUC (CV%'")
        base = self.one("SELECT valeur FROM ml_metrics WHERE modele='loan_default' AND metrique LIKE 'AUC baseline%'")
        self.assertGreater(auc, base)

    def test_every_question_has_an_answer(self):
        import json
        from banklens.config import REPORTS, SQL
        ans = json.loads((REPORTS / "answers.json").read_text(encoding="utf-8"))
        ids = {p.name.split("_")[0] for p in (SQL / "analysis").glob("*.sql")}
        self.assertTrue(ids <= set(ans), f"questions sans réponse : {ids - set(ans)}")


if __name__ == "__main__":
    unittest.main()
