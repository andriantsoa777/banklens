"""Contrôles qualité de données exécutés APRÈS le silver, résultats stockés dans `dq_results`.

Six dimensions classiques : complétude, unicité, validité, intégrité référentielle, cohérence, réconciliation.
Sévérité :
  blocking  -> le pipeline s'arrête (on ne publie pas un gold faux)
  warning   -> publié, mais visible dans le rapport et sur le dashboard
"""
from __future__ import annotations

from dataclasses import dataclass

from .log import get_logger

log = get_logger()


@dataclass
class Rule:
    rule_id: str
    source: str
    table: str
    dimension: str
    description: str
    severity: str
    failed_sql: str
    checked_sql: str | None = None   # défaut : COUNT(*) de la table


TABLES = {"contact": "silver_marketing_contact", "credit": "silver_credit_application"}
R = Rule
RULES: list[Rule] = [
    # ---------------------------------------------------------------- COMPLÉTUDE : aucune ligne perdue entre bronze et silver
    R("C01", "berka", "transaction", "complétude", "bronze = silver + quarantaine (transactions)", "blocking",
      "SELECT ABS((SELECT COUNT(*) FROM bronze_berka_trans) - (SELECT COUNT(*) FROM silver_transaction) - (SELECT COUNT(*) FROM quarantine WHERE source='berka' AND tbl='trans'))",
      "SELECT COUNT(*) FROM bronze_berka_trans"),
    R("C02", "berka", "account", "complétude", "bronze = silver + quarantaine (comptes)", "blocking",
      "SELECT ABS((SELECT COUNT(*) FROM bronze_berka_account) - (SELECT COUNT(*) FROM silver_account) - (SELECT COUNT(*) FROM quarantine WHERE source='berka' AND tbl='account'))",
      "SELECT COUNT(*) FROM bronze_berka_account"),
    R("C03", "berka", "loan", "complétude", "bronze = silver + quarantaine (prêts)", "blocking",
      "SELECT ABS((SELECT COUNT(*) FROM bronze_berka_loan) - (SELECT COUNT(*) FROM silver_loan) - (SELECT COUNT(*) FROM quarantine WHERE source='berka' AND tbl='loan'))",
      "SELECT COUNT(*) FROM bronze_berka_loan"),
    R("C04", "fraud", "card_tx", "complétude", "bronze = silver + quarantaine (transactions carte)", "blocking",
      "SELECT ABS((SELECT COUNT(*) FROM bronze_fraud_card_tx) - (SELECT COUNT(*) FROM silver_card_tx) - (SELECT COUNT(*) FROM quarantine WHERE source='fraud'))",
      "SELECT COUNT(*) FROM bronze_fraud_card_tx"),
    R("C05", "berka", "transaction", "complétude", "chaque compte a au moins une transaction", "warning",
      "SELECT COUNT(*) FROM silver_account a WHERE NOT EXISTS (SELECT 1 FROM silver_transaction t WHERE t.account_id=a.account_id)",
      "SELECT COUNT(*) FROM silver_account"),
    R("C06", "berka", "district", "complétude", "indicateurs socio-économiques de district renseignés (chômage 1995, criminalité 1995)", "warning",
      "SELECT COUNT(*) FROM silver_district WHERE unemployment_1995 IS NULL OR crimes_1995 IS NULL", "SELECT COUNT(*) FROM silver_district"),
    # ---------------------------------------------------------------- UNICITÉ
    R("U01", "berka", "transaction", "unicité", "trans_id unique", "blocking",
      "SELECT COUNT(*) - COUNT(DISTINCT trans_id) FROM silver_transaction", None),
    R("U02", "berka", "transaction", "unicité", "(account_id, tx_seq) unique : l'ordre des opérations est total", "blocking",
      "SELECT COUNT(*) - COUNT(DISTINCT account_id || '-' || tx_seq) FROM silver_transaction", None),
    R("U03", "berka", "loan", "unicité", "au plus un prêt par compte", "warning",
      "SELECT COUNT(*) - COUNT(DISTINCT account_id) FROM silver_loan", "SELECT COUNT(*) FROM silver_loan"),
    R("U04", "berka", "disposition", "unicité", "un seul titulaire (OWNER) par compte", "blocking",
      "SELECT COUNT(*) FROM (SELECT account_id FROM silver_disposition WHERE disp_type='owner' GROUP BY account_id HAVING COUNT(*)<>1)",
      "SELECT COUNT(DISTINCT account_id) FROM silver_disposition"),
    R("U05", "fraud", "card_tx", "unicité", "aucune ligne carte en double après déduplication", "blocking",
      "SELECT COUNT(*) FROM (SELECT 1 FROM silver_card_tx GROUP BY time_s, amount, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, v25, v26, v27, v28 HAVING COUNT(*)>1)",
      "SELECT COUNT(*) FROM silver_card_tx"),
    # ---------------------------------------------------------------- INTÉGRITÉ RÉFÉRENTIELLE
    R("I01", "berka", "transaction", "intégrité", "transaction.account_id existe dans account", "blocking",
      "SELECT COUNT(*) FROM silver_transaction t LEFT JOIN silver_account a USING(account_id) WHERE a.account_id IS NULL", None),
    R("I02", "berka", "loan", "intégrité", "loan.account_id existe dans account", "blocking",
      "SELECT COUNT(*) FROM silver_loan l LEFT JOIN silver_account a USING(account_id) WHERE a.account_id IS NULL", None),
    R("I03", "berka", "account", "intégrité", "account.district_id existe dans district", "blocking",
      "SELECT COUNT(*) FROM silver_account a LEFT JOIN silver_district d USING(district_id) WHERE d.district_id IS NULL", None),
    R("I04", "berka", "disposition", "intégrité", "disposition -> client et compte existent", "blocking",
      "SELECT COUNT(*) FROM silver_disposition d LEFT JOIN silver_client c USING(client_id) LEFT JOIN silver_account a USING(account_id) WHERE c.client_id IS NULL OR a.account_id IS NULL",
      None),
    R("I05", "berka", "card", "intégrité", "card.disp_id existe dans disposition", "blocking",
      "SELECT COUNT(*) FROM silver_card c LEFT JOIN silver_disposition d USING(disp_id) WHERE d.disp_id IS NULL", None),
    R("I06", "berka", "standing_order", "intégrité", "standing_order.account_id existe dans account", "blocking",
      "SELECT COUNT(*) FROM silver_standing_order o LEFT JOIN silver_account a USING(account_id) WHERE a.account_id IS NULL", None),
    # ---------------------------------------------------------------- VALIDITÉ
    R("V01", "berka", "transaction", "validité", "dates de transaction comprises entre 1993-01-01 et 1998-12-31", "blocking",
      "SELECT COUNT(*) FROM silver_transaction WHERE tx_date < '1993-01-01' OR tx_date > '1998-12-31'", None),
    R("V02", "berka", "client", "validité", "âge à la date de référence entre 0 et 110 ans", "blocking",
      "SELECT COUNT(*) FROM silver_client WHERE (julianday('1998-12-31') - julianday(birth_date)) / 365.25 NOT BETWEEN 0 AND 110",
      "SELECT COUNT(*) FROM silver_client"),
    R("V03", "berka", "transaction", "validité", "signe cohérent : crédit => montant signé >= 0, débit => <= 0", "blocking",
      "SELECT COUNT(*) FROM silver_transaction WHERE (direction='credit' AND signed_amount<0) OR (direction='debit' AND signed_amount>0)", None),
    R("V04", "berka", "transaction", "validité", "contrepartie (banque/compte) uniquement sur les virements", "warning",
      "SELECT COUNT(*) FROM silver_transaction WHERE counterpart_bank IS NOT NULL AND operation NOT IN ('incoming_transfer','outgoing_transfer')", None),
    R("V05", "fraud", "card_tx", "validité", "montant carte <= 30 000 (un montant supérieur serait suspect de saisie)", "warning",
      "SELECT COUNT(*) FROM silver_card_tx WHERE amount > 30000", None),
    R("V06", "marketing", "contact", "validité", "âge d'un contact entre 18 et 100 ans", "blocking",
      "SELECT COUNT(*) FROM silver_marketing_contact WHERE age NOT BETWEEN 18 AND 100", None),
    # ---------------------------------------------------------------- COHÉRENCE MÉTIER
    R("K01", "berka", "loan", "cohérence", "mensualité x durée = montant du prêt (tolérance 1 %) : le prêt est amorti linéairement", "warning",
      "SELECT COUNT(*) FROM silver_loan WHERE ABS(monthly_payment * duration_months - amount) > 0.01 * amount", "SELECT COUNT(*) FROM silver_loan"),
    R("K02", "berka", "transaction", "cohérence", "aucune transaction antérieure à l'ouverture du compte", "warning",
      "SELECT COUNT(*) FROM silver_transaction t JOIN silver_account a USING(account_id) WHERE t.tx_date < a.opened_on", None),
    R("K03", "berka", "loan", "cohérence", "prêt accordé après l'ouverture du compte", "warning",
      "SELECT COUNT(*) FROM silver_loan l JOIN silver_account a USING(account_id) WHERE l.granted_on < a.opened_on", "SELECT COUNT(*) FROM silver_loan"),
    R("K04", "berka", "card", "cohérence", "carte émise après l'ouverture du compte", "warning",
      "SELECT COUNT(*) FROM silver_card c JOIN silver_disposition d USING(disp_id) JOIN silver_account a USING(account_id) WHERE c.issued_on < a.opened_on",
      "SELECT COUNT(*) FROM silver_card"),
    R("K07", "berka", "standing_order", "cohérence", "chaque ordre permanent de remboursement correspond à un prêt du fichier loan (constat source : 35 ordres sans prêt)", "warning",
      "SELECT COUNT(*) FROM silver_standing_order o WHERE o.purpose = 'loan_repayment' AND NOT EXISTS (SELECT 1 FROM silver_loan l WHERE l.account_id = o.account_id)",
      "SELECT COUNT(*) FROM silver_standing_order WHERE purpose = 'loan_repayment'"),
    R("K05", "german", "credit", "cohérence", "âge >= 18 et durée de crédit entre 1 et 72 mois", "warning",
      "SELECT COUNT(*) FROM silver_credit_application WHERE age < 18 OR duration_months NOT BETWEEN 1 AND 72", None),
    R("K06", "marketing", "contact", "cohérence", "previous_contacts > 0 => délai depuis la campagne précédente renseigné (constat source : 321 cas où pdays = 999 malgré des contacts antérieurs)", "warning",
      "SELECT COUNT(*) FROM silver_marketing_contact WHERE previous_contacts > 0 AND days_since_prev_campaign IS NULL", "SELECT COUNT(*) FROM silver_marketing_contact WHERE previous_contacts > 0"),
    # ---------------------------------------------------------------- RÉCONCILIATION COMPTABLE
    R("B01", "berka", "transaction", "réconciliation", "solde_précédent + montant = solde_après (±0,15 CZK) sur la chaîne reconstituée", "warning",
      "SELECT COUNT(*) FROM silver_transaction WHERE balance_chain_ok = 0", None),
    R("B02", "berka", "transaction", "réconciliation", "somme des montants signés = solde final par compte (tolérance : 0,10 CZK par intérêt crédité = arrondi bancaire)", "warning",
      """SELECT COUNT(*) FROM (
           SELECT t.account_id, SUM(t.signed_amount) AS s, SUM(t.operation='interest_credit') AS n_int, (SELECT balance_after FROM silver_transaction x WHERE x.account_id=t.account_id ORDER BY tx_seq DESC LIMIT 1) AS last_bal
           FROM silver_transaction t GROUP BY t.account_id) WHERE ABS(s - last_bal) > 0.1 * n_int + 1""",
      "SELECT COUNT(DISTINCT account_id) FROM silver_transaction"),
]


def run_rules(con) -> list[tuple]:
    con.execute("DROP TABLE IF EXISTS dq_results")
    con.execute("""CREATE TABLE dq_results(rule_id TEXT, source TEXT, tbl TEXT, dimension TEXT, description TEXT,
                   severity TEXT, checked INTEGER, failed INTEGER, pass_rate REAL, status TEXT)""")
    rows, blocking_fail = [], []
    for r in RULES:
        failed = con.execute(r.failed_sql).fetchone()[0] or 0
        checked_sql = r.checked_sql or f"SELECT COUNT(*) FROM {TABLES.get(r.table, 'silver_' + r.table)}"
        checked = con.execute(checked_sql).fetchone()[0] or 0
        rate = 1.0 if checked == 0 else max(0.0, 1 - failed / checked)
        status = "PASS" if failed == 0 else ("FAIL" if r.severity == "blocking" else "WARN")
        rows.append((r.rule_id, r.source, r.table, r.dimension, r.description, r.severity, checked, failed, round(rate, 6), status))
        (log.info if status == "PASS" else log.warning)("dq      %-4s %-5s %s -> %s (%d/%d)", r.rule_id, r.severity[:5], r.description[:70], status, failed, checked)
        if status == "FAIL":
            blocking_fail.append(r.rule_id)
    con.executemany("INSERT INTO dq_results VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    if blocking_fail:
        raise RuntimeError(f"Contrôles bloquants en échec : {blocking_fail}. Gold non construit.")
    return rows
