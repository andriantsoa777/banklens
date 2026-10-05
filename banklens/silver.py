"""Couche SILVER : typage, normalisation, traduction des codes, quarantaine des lignes invalides.

Règles de conduite :
  * on ne supprime jamais silencieusement : tout rejet va dans `quarantine` avec sa raison ;
  * toute correction est comptée dans `dq_fixes` (ce qui a été changé, sur combien de lignes) ;
  * on n'invente pas de valeur : un manquant reste NULL (pas d'imputation en silver).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .db import connect, run_sql_file
from .ledger import sequence_transactions
from .log import get_logger

log = get_logger()

# ---------------------------------------------------------------- dictionnaires de traduction (tchèque -> métier)
FREQ = {"POPLATEK MESICNE": "monthly", "POPLATEK TYDNE": "weekly", "POPLATEK PO OBRATU": "after_transaction"}
OPERATION = {"VYBER KARTOU": "card_withdrawal", "VKLAD": "cash_deposit", "PREVOD Z UCTU": "incoming_transfer",
             "VYBER": "cash_withdrawal", "PREVOD NA UCET": "outgoing_transfer"}
CATEGORY = {"POJISTNE": "insurance", "SLUZBY": "statement_fee", "UROK": "interest_credited",
            "SANKC. UROK": "overdraft_interest", "SIPO": "household_payment", "DUCHOD": "pension",
            "UVER": "loan_repayment", "LEASING": "leasing"}
LOAN_STATUS = {"A": "finished_ok", "B": "finished_not_paid", "C": "running_ok", "D": "running_in_debt"}


class Ctx:
    """Petit contexte partagé : connexion + journaux de corrections/rejets."""

    def __init__(self, con):
        self.con = con
        self.fixes: list[tuple] = []
        self.quar: list[tuple] = []

    def fix(self, source, tbl, fix_id, desc, n):
        self.fixes.append((source, tbl, fix_id, desc, int(n)))
        if n:
            log.info("fix     %-10s %-20s %-6s %s (%s)", source, tbl, fix_id, desc, f"{int(n):,}".replace(",", " "))

    def reject(self, source, tbl, df_bad: pd.DataFrame, rule_id, detail, key):
        for _, r in df_bad.iterrows():
            self.quar.append((source, tbl, str(r[key]), rule_id, detail, json.dumps(r.to_dict(), default=str, ensure_ascii=False)))
        if len(df_bad):
            log.warning("QUARANT %-10s %-20s %-6s %s (%d)", source, tbl, rule_id, detail, len(df_bad))

    def flush(self):
        self.con.executemany("INSERT INTO dq_fixes VALUES (?,?,?,?,?)", self.fixes)
        self.con.executemany("INSERT INTO quarantine VALUES (?,?,?,?,?,?)", self.quar)
        self.con.commit()


def _bronze(con, name) -> pd.DataFrame:
    df = pd.read_sql(f"SELECT * FROM {name}", con)
    return df.drop(columns=["_source_file", "_batch_id", "_loaded_at"], errors="ignore")


def _yymmdd(s: pd.Series) -> pd.Series:
    """'930101' -> 1993-01-01 (le siècle est toujours 19 dans Berka : 1993-1998)."""
    s = s.astype(str).str.strip().str.slice(0, 6)
    return pd.to_datetime("19" + s, format="%Y%m%d", errors="coerce")


def _iso(s: pd.Series) -> pd.Series:
    return s.dt.strftime("%Y-%m-%d")


def _insert(con, table, df):
    df.to_sql(table, con, if_exists="append", index=False, chunksize=50_000)


# ------------------------------------------------------------------------------------------------ BERKA
def clean_berka(ctx: Ctx):
    con = ctx.con

    # ---- district : A1..A16 sont des codes opaques, on les renomme d'après la doc officielle
    d = _bronze(con, "bronze_berka_district")
    d = d.rename(columns={"A1": "district_id", "A2": "district_name", "A3": "region", "A4": "inhabitants",
                          "A5": "municipalities_lt_500", "A6": "municipalities_500_1999",
                          "A7": "municipalities_2000_9999", "A8": "municipalities_gt_10000", "A9": "cities",
                          "A10": "urban_ratio", "A11": "avg_salary", "A12": "unemployment_1995",
                          "A13": "unemployment_1996", "A14": "entrepreneurs_per_1000",
                          "A15": "crimes_1995", "A16": "crimes_1996"})
    n_q = int((d[["unemployment_1995", "crimes_1995"]] == "?").sum().sum())
    ctx.fix("berka", "district", "D01", "valeur '?' -> NULL (aucune imputation : on ne devine pas un taux de chômage)", n_q)
    d = d.replace("?", np.nan)
    for c in d.columns.drop(["_row_num", "district_name", "region"]):
        d[c] = pd.to_numeric(d[c])
    for c in ("district_id", "inhabitants", "municipalities_lt_500", "municipalities_500_1999",
              "municipalities_2000_9999", "municipalities_gt_10000", "cities", "avg_salary",
              "entrepreneurs_per_1000"):
        d[c] = d[c].astype("Int64")
    for c in ("crimes_1995", "crimes_1996"):
        d[c] = d[c].astype("Int64")
    d["region"] = d["region"].str.strip().str.lower()   # "Prague" -> "prague"
    _insert(con, "silver_district", d.drop(columns="_row_num"))
    district_ids = set(d["district_id"].astype(int))

    # ---- account
    a = _bronze(con, "bronze_berka_account")
    a["opened_on_dt"] = _yymmdd(a["date"])
    a["statement_frequency"] = a["frequency"].map(FREQ)
    a["district_id"] = a["district_id"].astype(int)
    bad = a[a["opened_on_dt"].isna() | a["statement_frequency"].isna() | ~a["district_id"].isin(district_ids)]
    ctx.reject("berka", "account", bad, "A_BAD", "date, fréquence ou district invalide", "account_id")
    a = a.drop(bad.index)
    ctx.fix("berka", "account", "A01", "date yymmdd (ex. 930101) -> ISO 1993-01-01", len(a))
    ctx.fix("berka", "account", "A02", "fréquence de relevé tchèque -> monthly / weekly / after_transaction", len(a))
    a_out = pd.DataFrame({"account_id": a["account_id"].astype(int), "district_id": a["district_id"],
                          "statement_frequency": a["statement_frequency"], "opened_on": _iso(a["opened_on_dt"])})
    _insert(con, "silver_account", a_out)
    account_ids = set(a_out["account_id"])

    # ---- client : le sexe et la date de naissance sont encodés dans birth_number (AAMMJJ, mois+50 = femme)
    c = _bronze(con, "bronze_berka_client")
    bn = c["birth_number"].str.zfill(6)
    month = bn.str[2:4].astype(int)
    is_f = month > 50
    real_month = np.where(is_f, month - 50, month)
    c["birth_date_dt"] = pd.to_datetime("19" + bn.str[:2] + pd.Series(real_month, index=c.index).astype(str).str.zfill(2) + bn.str[4:6],
                                        format="%Y%m%d", errors="coerce")
    c["gender"] = np.where(is_f, "F", "M")
    c["district_id"] = c["district_id"].astype(int)
    bad = c[c["birth_date_dt"].isna() | ~c["district_id"].isin(district_ids)]
    ctx.reject("berka", "client", bad, "C_BAD", "date de naissance impossible ou district inconnu", "client_id")
    c = c.drop(bad.index)
    ctx.fix("berka", "client", "C01", "birth_number AAMMJJ décodé : mois > 50 => femme, mois-50 => vrai mois", len(c))
    _insert(con, "silver_client", pd.DataFrame({"client_id": c["client_id"].astype(int), "district_id": c["district_id"],
                                                "birth_date": _iso(c["birth_date_dt"]), "gender": c["gender"]}))
    client_ids = set(c["client_id"].astype(int))

    # ---- disposition
    dp = _bronze(con, "bronze_berka_disp")
    dp[["disp_id", "client_id", "account_id"]] = dp[["disp_id", "client_id", "account_id"]].astype(int)
    dp["disp_type"] = dp["type"].str.lower()
    bad = dp[~dp["client_id"].isin(client_ids) | ~dp["account_id"].isin(account_ids) | ~dp["disp_type"].isin(["owner", "disponent"])]
    ctx.reject("berka", "disp", bad, "DP_FK", "client ou compte inconnu", "disp_id")
    dp = dp.drop(bad.index)
    _insert(con, "silver_disposition", dp[["disp_id", "client_id", "account_id", "disp_type"]])
    disp_ids = set(dp["disp_id"])

    # ---- card
    ca = _bronze(con, "bronze_berka_card")
    ca["issued_dt"] = _yymmdd(ca["issued"])
    ca[["card_id", "disp_id"]] = ca[["card_id", "disp_id"]].astype(int)
    bad = ca[ca["issued_dt"].isna() | ~ca["disp_id"].isin(disp_ids) | ~ca["type"].isin(["junior", "classic", "gold"])]
    ctx.reject("berka", "card", bad, "CA_BAD", "date, type ou disposition invalide", "card_id")
    ca = ca.drop(bad.index)
    ctx.fix("berka", "card", "CA01", "'931107 00:00:00' -> date ISO (l'heure est toujours 00:00:00, supprimée)", len(ca))
    _insert(con, "silver_card", pd.DataFrame({"card_id": ca["card_id"], "disp_id": ca["disp_id"],
                                              "card_type": ca["type"], "issued_on": _iso(ca["issued_dt"])}))

    # ---- loan
    l = _bronze(con, "bronze_berka_loan")
    l["granted_dt"] = _yymmdd(l["date"])
    for col in ("loan_id", "account_id", "duration"):
        l[col] = l[col].astype(int)
    l["amount"] = l["amount"].astype(float)
    l["payments"] = l["payments"].astype(float)
    bad = l[l["granted_dt"].isna() | ~l["account_id"].isin(account_ids) | ~l["status"].isin(list(LOAN_STATUS))]
    ctx.reject("berka", "loan", bad, "L_BAD", "date, compte ou statut invalide", "loan_id")
    l = l.drop(bad.index)
    ctx.fix("berka", "loan", "L01", "statut A/B/C/D -> libellé + indicateur is_default (B ou D)", len(l))
    _insert(con, "silver_loan", pd.DataFrame({
        "loan_id": l["loan_id"], "account_id": l["account_id"], "granted_on": _iso(l["granted_dt"]),
        "amount": l["amount"].astype(int), "duration_months": l["duration"], "monthly_payment": l["payments"],
        "status_code": l["status"], "status_label": l["status"].map(LOAN_STATUS),
        "is_default": l["status"].isin(["B", "D"]).astype(int)}))

    # ---- order (ordres permanents)
    o = _bronze(con, "bronze_berka_order")
    o["order_id"] = o["order_id"].astype(int)
    o["account_id"] = o["account_id"].astype(int)
    o["amount"] = o["amount"].astype(float)
    blank = o["k_symbol"].str.strip() == ""
    ctx.fix("berka", "order", "O01", "k_symbol vide ou ' ' -> 'unspecified'", blank.sum())
    o["purpose"] = o["k_symbol"].str.strip().map(CATEGORY).fillna("unspecified")
    bad = o[~o["account_id"].isin(account_ids) | (o["amount"] <= 0)]
    ctx.reject("berka", "order", bad, "O_BAD", "compte inconnu ou montant <= 0", "order_id")
    o = o.drop(bad.index)
    _insert(con, "silver_standing_order", o[["order_id", "account_id", "bank_to", "account_to", "amount", "purpose"]])

    # ---- trans : 1 056 320 lignes, le cœur
    t = _bronze(con, "bronze_berka_trans")
    t["tx_dt"] = _yymmdd(t["date"])
    for col in ("trans_id", "account_id"):
        t[col] = t[col].astype(int)
    t["amount"] = t["amount"].astype(float)
    t["balance"] = t["balance"].astype(float)
    bad = t[t["tx_dt"].isna() | ~t["account_id"].isin(account_ids) | (t["amount"] < 0) | ~t["type"].isin(["PRIJEM", "VYDAJ", "VYBER"])]
    ctx.reject("berka", "trans", bad, "T_BAD", "date, compte, montant ou type invalide", "trans_id")
    t = t.drop(bad.index)
    dup = t["trans_id"].duplicated(keep="first")
    ctx.reject("berka", "trans", t[dup], "T_DUP", "trans_id en double", "trans_id")
    t = t[~dup]

    n_vyber = (t["type"] == "VYBER").sum()
    ctx.fix("berka", "trans", "T01", "type 'VYBER' (retrait) rangé dans 'VYDAJ' : le champ type ne doit avoir que 2 sens (credit/debit)", n_vyber)
    t["direction"] = np.where(t["type"] == "PRIJEM", "credit", "debit")
    t["signed_amount"] = np.where(t["direction"] == "credit", t["amount"], -t["amount"])

    ksym = t["k_symbol"].str.strip()
    ctx.fix("berka", "trans", "T02", "k_symbol '' ou ' ' (deux façons d'écrire 'vide') -> 'none'", (ksym == "").sum())
    t["category"] = ksym.map(CATEGORY).fillna("none")

    n_op_blank = (t["operation"] == "").sum()
    t["operation_c"] = t["operation"].map(OPERATION)
    mask_interest = t["operation_c"].isna() & (ksym == "UROK")
    ctx.fix("berka", "trans", "T03", "operation vide : toujours des intérêts crédités (k_symbol=UROK) -> 'interest_credit'", n_op_blank)
    t.loc[mask_interest, "operation_c"] = "interest_credit"
    leftover = t[t["operation_c"].isna()]
    ctx.reject("berka", "trans", leftover, "T_OP", "operation inconnue", "trans_id")
    t = t[t["operation_c"].notna()]

    ctx.fix("berka", "trans", "T04", "bank/account vides -> NULL (renseignés uniquement pour les virements)", ((t["bank"] == "") | (t["account"] == "")).sum())
    t["counterpart_bank"] = t["bank"].replace("", np.nan)
    t["counterpart_account"] = t["account"].replace("", np.nan)
    t["is_zero_amount"] = (t["amount"] == 0).astype(int)
    t["is_negative_balance"] = (t["balance"] < 0).astype(int)
    ctx.fix("berka", "trans", "T05", "montant = 0 conservé mais marqué is_zero_amount (intérêts nuls réels)", t["is_zero_amount"].sum())
    ctx.fix("berka", "trans", "T06", "solde négatif conservé mais marqué is_negative_balance (découvert réel)", t["is_negative_balance"].sum())
    ctx.fix("berka", "trans", "T07", "date yymmdd -> ISO", len(t))
    out = pd.DataFrame({
        "trans_id": t["trans_id"], "account_id": t["account_id"], "tx_date": _iso(t["tx_dt"]),
        "direction": t["direction"], "operation": t["operation_c"], "category": t["category"],
        "amount": t["amount"], "signed_amount": t["signed_amount"], "balance_after": t["balance"],
        "counterpart_bank": t["counterpart_bank"], "counterpart_account": t["counterpart_account"],
        "is_zero_amount": t["is_zero_amount"], "is_negative_balance": t["is_negative_balance"]})
    out = sequence_transactions(out)
    ctx.fix("berka", "trans", "T08", "ordre réel des opérations reconstitué par chaînage des soldes (trans_id n'est pas chronologique)", len(out))
    ctx.fix("berka", "trans", "T09", "ruptures de chaîne résiduelles (opération manquante à la source) : marquées balance_chain_ok=0", (out["balance_chain_ok"] == 0).sum())
    out = out[["trans_id", "account_id", "tx_seq", "tx_date", "direction", "operation", "category", "amount", "signed_amount",
               "balance_after", "counterpart_bank", "counterpart_account", "is_zero_amount", "is_negative_balance",
               "balance_chain_ok", "balance_drift"]]
    _insert(con, "silver_transaction", out)


# ------------------------------------------------------------------------------------------------ FRAUDE (Kaggle / ULB)
def clean_fraud(ctx: Ctx):
    con = ctx.con
    f = _bronze(con, "bronze_fraud_card_tx")
    f["tx_id"] = f["_row_num"]
    num_cols = [c for c in f.columns if c not in ("_row_num", "tx_id")]
    for c in num_cols:
        f[c] = pd.to_numeric(f[c], errors="coerce")
    bad = f[f[num_cols].isna().any(axis=1) | (f["Amount"] < 0) | ~f["Class"].isin([0, 1])]
    ctx.reject("fraud", "card_tx", bad, "F_BAD", "valeur manquante, montant négatif ou classe invalide", "tx_id")
    f = f.drop(bad.index)
    # Doublons exacts (31 colonnes identiques) : le jeu public en contient 1 081, dont 19 fraudes.
    # Politique : on garde la 1re occurrence, on met les suivantes en quarantaine (elles gonflent le volume et fuient entre train/test).
    dup = f.duplicated(subset=num_cols, keep="first")
    dup_fraud = int(f.loc[dup, "Class"].sum())
    ctx.reject("fraud", "card_tx", f[dup], "F_DUP", "ligne identique à une ligne précédente (31 colonnes)", "tx_id")
    ctx.fix("fraud", "card_tx", "F01", f"doublons exacts mis en quarantaine (dont {dup_fraud} fraudes)", dup.sum())
    f = f[~dup]
    f["time_s"] = f["Time"].astype(int)
    f["day_index"] = f["time_s"] // 86400
    f["hour_of_day"] = (f["time_s"] // 3600) % 24
    ctx.fix("fraud", "card_tx", "F02", "Time (secondes depuis la 1re transaction) -> day_index + hour_of_day", len(f))
    f["is_zero_amount"] = (f["Amount"] == 0).astype(int)
    ctx.fix("fraud", "card_tx", "F03", "montant = 0 conservé mais marqué (vérifications de carte)", f["is_zero_amount"].sum())
    out = pd.DataFrame({"tx_id": f["tx_id"].astype(int), "time_s": f["time_s"], "day_index": f["day_index"],
                        "hour_of_day": f["hour_of_day"], "amount": f["Amount"], "is_zero_amount": f["is_zero_amount"],
                        "is_fraud": f["Class"].astype(int)})
    for i in range(1, 29):
        out[f"v{i}"] = f[f"V{i}"].values
    _insert(con, "silver_card_tx", out)


# ------------------------------------------------------------------------------------------------ CRÉDIT ALLEMAND (UCI)
def clean_german(ctx: Ctx):
    con = ctx.con
    g = _bronze(con, "bronze_german_credit")
    n_typo = (g["job"] == "mangement self-employed").sum()
    ctx.fix("german", "credit", "G01", "faute de frappe source 'mangement self-employed' corrigée", n_typo)
    g["job"] = g["job"].replace({"mangement self-employed": "management / self-employed"})
    for c in ("months_loan_duration", "amount", "installment_rate", "residence_history", "age", "existing_credits", "default", "dependents"):
        g[c] = pd.to_numeric(g[c], errors="coerce")
    bad = g[g[["months_loan_duration", "amount", "age", "default"]].isna().any(axis=1) | ~g["default"].isin([1, 2])]
    ctx.reject("german", "credit", bad, "G_BAD", "valeur numérique manquante ou cible invalide", "_row_num")
    g = g.drop(bad.index)
    ctx.fix("german", "credit", "G02", "cible 'default' 1/2 (1=bon, 2=mauvais, codage UCI) -> is_default 0/1", len(g))
    ctx.fix("german", "credit", "G03", "'unknown' conservé comme modalité (l'absence d'information est elle-même informative en scoring)", (g["checking_balance"] == "unknown").sum())
    out = pd.DataFrame({
        "application_id": g["_row_num"], "checking_balance": g["checking_balance"], "duration_months": g["months_loan_duration"].astype(int),
        "credit_history": g["credit_history"], "purpose": g["purpose"], "amount_dm": g["amount"].astype(int),
        "savings_balance": g["savings_balance"], "employment_length": g["employment_length"],
        "installment_rate": g["installment_rate"].astype(int), "personal_status": g["personal_status"],
        "other_debtors": g["other_debtors"], "residence_years": g["residence_history"].astype(int), "property": g["property"],
        "age": g["age"].astype(int), "other_installment_plans": g["installment_plan"], "housing": g["housing"],
        "existing_credits": g["existing_credits"].astype(int), "dependents": g["dependents"].astype(int),
        "has_telephone": (g["telephone"] == "yes").astype(int), "foreign_worker": (g["foreign_worker"] == "yes").astype(int),
        "job": g["job"], "is_default": (g["default"] == 2).astype(int)})
    _insert(con, "silver_credit_application", out)


# ------------------------------------------------------------------------------------------------ MARKETING (UCI)
MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def clean_marketing(ctx: Ctx):
    con = ctx.con
    m = _bronze(con, "bronze_marketing_contact")
    num = ["age", "duration", "campaign", "pdays", "previous", "emp_var_rate", "cons_price_idx", "cons_conf_idx", "euribor3m", "nr_employed"]
    for c in num:
        m[c] = pd.to_numeric(m[c], errors="coerce")
    bad = m[m[num].isna().any(axis=1) | ~m["month"].isin(MONTHS) | ~m["y"].isin(["yes", "no"])]
    ctx.reject("marketing", "contact", bad, "M_BAD", "valeur numérique manquante, mois ou cible invalide", "_row_num")
    m = m.drop(bad.index)
    unk = int((m[["job", "marital", "education", "default", "housing", "loan"]] == "unknown").sum().sum())
    ctx.fix("marketing", "contact", "M01", "'unknown' -> NULL sur job/marital/education/default/housing/loan", unk)
    for c in ("job", "marital", "education", "default", "housing", "loan"):
        m[c] = m[c].replace("unknown", np.nan)
    n999 = (m["pdays"] == 999).sum()
    ctx.fix("marketing", "contact", "M02", "pdays = 999 (code « pas de contact lors d'une campagne précédente ») -> NULL : sinon la moyenne de pdays n'a aucun sens", n999)
    m["pdays"] = m["pdays"].where(m["pdays"] != 999)
    ctx.fix("marketing", "contact", "M03", "mois texte (may) -> numéro (5)", len(m))
    ctx.fix("marketing", "contact", "M04", "'duration' conservée (analyse) mais marquée call_duration_s : inconnue avant l'appel, donc interdite comme variable prédictive (fuite)", len(m))
    yn = lambda s: s.map({"yes": 1, "no": 0}).astype("Int64")
    out = pd.DataFrame({
        "contact_id": m["_row_num"], "age": m["age"].astype(int), "job": m["job"], "marital_status": m["marital"], "education": m["education"],
        "has_credit_default": yn(m["default"]), "has_housing_loan": yn(m["housing"]), "has_personal_loan": yn(m["loan"]),
        "contact_channel": m["contact"], "contact_month": m["month"].map(MONTHS), "contact_weekday": m["day_of_week"],
        "call_duration_s": m["duration"].astype(int), "campaign_contacts": m["campaign"].astype(int),
        "days_since_prev_campaign": m["pdays"].astype("Int64"), "previous_contacts": m["previous"].astype(int),
        "previous_outcome": m["poutcome"], "emp_var_rate": m["emp_var_rate"], "cons_price_idx": m["cons_price_idx"],
        "cons_conf_idx": m["cons_conf_idx"], "euribor3m": m["euribor3m"], "nr_employed": m["nr_employed"],
        "subscribed": (m["y"] == "yes").astype(int)})
    _insert(con, "silver_marketing_contact", out)


def build_silver(con=None):
    own = con is None
    con = con or connect()
    run_sql_file(con, "silver/00_ddl.sql")
    ctx = Ctx(con)
    for fn in (clean_berka, clean_fraud, clean_german, clean_marketing):
        fn(ctx)
    ctx.flush()
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'silver_%' ORDER BY 1").fetchall():
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        log.info("silver  %-28s %9s lignes", t, f"{n:,}".replace(",", " "))
    nq = con.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
    log.info("quarantaine : %d ligne(s)", nq)
    if own:
        con.close()
