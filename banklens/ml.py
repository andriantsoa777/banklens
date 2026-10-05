"""Modèles de risque et de ciblage, évalués honnêtement. Optionnel : nécessite scikit-learn.

Principes appliqués (et à expliquer en entretien) :
  * aucune fuite : variables disponibles AU MOMENT de la décision (pas de durée d'appel, pas de futur du compte) ;
  * découpage temporel pour la fraude (on entraîne sur le passé, on teste sur le futur) ;
  * validation croisée répétée + intervalle de confiance quand l'échantillon est petit (682 prêts, 76 défauts) ;
  * variables protégées (sexe) exclues des modèles de crédit ;
  * métriques adaptées au déséquilibre (PR-AUC pour la fraude), et traduction en euros/utilité métier, pas seulement en AUC.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .log import get_logger

log = get_logger()
SEED = 42

# Hypothèses économiques EXPLICITES (modifiables) pour traduire un score en décision.
REVIEW_COST_PER_ALERT = 5.0       # coût d'analyse d'une alerte fraude (EUR)
GERMAN_COST_BAD_ACCEPTED = 5.0    # coût d'accepter un mauvais payeur, relatif à refuser un bon (matrice de coût UCI)
GERMAN_COST_GOOD_REJECTED = 1.0


def _have_sklearn() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


def _ks(y, p) -> float:
    d = pd.DataFrame({"y": y, "p": p}).sort_values("p", ascending=False)
    cg = (d["y"] == 0).cumsum() / max((d["y"] == 0).sum(), 1)
    cb = (d["y"] == 1).cumsum() / max((d["y"] == 1).sum(), 1)
    return float((cb - cg).abs().max())


def _bootstrap_auc(y, p, n=400):
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(SEED)
    y, p = np.asarray(y), np.asarray(p)
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        vals.append(roc_auc_score(y[i], p[i]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def _cv_oof(model_factory, X, y, repeats=5, folds=5):
    """Prédictions hors-échantillon moyennées sur plusieurs répétitions de CV stratifiée."""
    from sklearn.model_selection import StratifiedKFold
    oof = np.zeros(len(y))
    for r in range(repeats):
        skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=SEED + r)
        for tr, te in skf.split(X, y):
            m = model_factory()
            m.fit(X.iloc[tr], y.iloc[tr])
            oof[te] += m.predict_proba(X.iloc[te])[:, 1] / repeats
    return oof


def _save(con, name, df):
    df.to_sql(name, con, if_exists="replace", index=False)


# ------------------------------------------------------------------ 1. Berka : défaut de prêt
def loan_default(con, metrics: list):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    df = pd.read_sql("""
        SELECT l.loan_key, l.is_default, l.amount, l.duration_months, l.monthly_payment, l.payment_to_inflow_ratio,
               l.pre_avg_balance_6m, l.pre_avg_monthly_inflow_6m, l.pre_overdraft_months_6m,
               d.unemployment_1996, d.avg_salary
        FROM fact_loan l JOIN dim_account a ON a.account_key = l.account_key
        JOIN dim_district d ON d.district_key = a.district_key""", con)
    df["unemployment_1996"] = df["unemployment_1996"].fillna(df["unemployment_1996"].median())
    y = df["is_default"]
    feats = ["amount", "duration_months", "payment_to_inflow_ratio", "pre_avg_balance_6m", "pre_overdraft_months_6m",
             "unemployment_1996", "avg_salary"]
    X = df[feats]
    mk = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, class_weight="balanced", max_iter=1000))
    oof = _cv_oof(mk, X, y)
    auc = roc_auc_score(y, oof)
    lo, hi = _bootstrap_auc(y, oof)
    base = _cv_oof(mk, df[["amount"]], y)
    auc_base = roc_auc_score(y, base)
    metrics += [("loan_default", "AUC (CV 5x5)", auc, f"IC95 % [{lo:.3f} ; {hi:.3f}]"),
                ("loan_default", "AUC baseline (montant seul)", auc_base, "référence naïve"),
                ("loan_default", "PR-AUC", average_precision_score(y, oof), f"taux de base = {y.mean():.3f}"),
                ("loan_default", "KS", _ks(y, oof), "écart max entre courbes cumulées"),
                ("loan_default", "Nb prêts / défauts", len(y), f"{int(y.sum())} défauts")]
    m = mk().fit(X, y)
    coef = pd.DataFrame({"variable": feats, "coefficient_standardise": m[-1].coef_[0]}).sort_values("coefficient_standardise", key=abs, ascending=False)
    _save(con, "ml_loan_coefficients", coef)
    df["score_defaut"] = oof
    df["decile_risque"] = pd.qcut(df["score_defaut"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    g = df.groupby("decile_risque").agg(prets=("is_default", "size"), defauts=("is_default", "sum"), taux_defaut=("is_default", "mean"),
                                         score_moyen=("score_defaut", "mean"), montant_moyen=("amount", "mean")).reset_index()
    g["taux_defaut"] = (g["taux_defaut"] * 100).round(1)
    _save(con, "ml_loan_risk_quintiles", g)
    _save(con, "ml_loan_scores", df[["loan_key", "score_defaut", "decile_risque"]])
    log.info("ml      prêts Berka : AUC=%.3f [%.3f ; %.3f] (baseline montant seul %.3f)", auc, lo, hi, auc_base)


# ------------------------------------------------------------------ 2. Fraude carte
def card_fraud(con, metrics: list):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    cols = ", ".join(f"p.v{i}" for i in range(1, 29))
    df = pd.read_sql(f"""SELECT f.transaction_key, f.time_s, f.hour_key, f.amount, f.is_fraud, {cols}
                         FROM fact_card_tx f JOIN fact_card_tx_features p USING(transaction_key) ORDER BY f.time_s""", con)
    df["log_amount"] = np.log1p(df["amount"])
    feats = [f"v{i}" for i in range(1, 29)] + ["log_amount"]
    cut = df["time_s"].quantile(0.75)                    # découpage TEMPOREL : train = passé, test = futur
    tr, te = df[df["time_s"] <= cut], df[df["time_s"] > cut]
    log.info("ml      fraude : train=%d (%d fraudes) test=%d (%d fraudes)", len(tr), tr.is_fraud.sum(), len(te), te.is_fraud.sum())
    models = {
        "Régression logistique": make_pipeline(StandardScaler(), LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000)),
        "Gradient boosting": HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=4, random_state=SEED,
                                                            class_weight="balanced"),
    }
    best_name, best_p, best_ap = None, None, -1
    for name, m in models.items():
        m.fit(tr[feats], tr["is_fraud"])
        p = m.predict_proba(te[feats])[:, 1]
        ap, auc = average_precision_score(te["is_fraud"], p), roc_auc_score(te["is_fraud"], p)
        metrics += [(f"fraude / {name}", "PR-AUC (test futur)", ap, f"taux de base = {te.is_fraud.mean():.4f}"),
                    (f"fraude / {name}", "ROC-AUC (test futur)", auc, "")]
        log.info("ml      fraude %-22s PR-AUC=%.3f ROC-AUC=%.3f", name, ap, auc)
        if ap > best_ap:
            best_name, best_p, best_ap = name, p, ap
    metrics.append(("fraude", "Modèle retenu", best_ap, best_name))
    te = te.assign(score=best_p).sort_values("score", ascending=False).reset_index(drop=True)
    total_f, total_amt = te["is_fraud"].sum(), te.loc[te["is_fraud"] == 1, "amount"].sum()
    rows = []
    for pct in (0.05, 0.1, 0.25, 0.5, 1, 2, 5):
        k = max(1, int(round(len(te) * pct / 100)))
        top = te.head(k)
        caught = int(top["is_fraud"].sum())
        saved = float(top.loc[top["is_fraud"] == 1, "amount"].sum())
        cost = k * REVIEW_COST_PER_ALERT
        rows.append(dict(taux_alertes_pct=pct, alertes=k, fraudes_captees=caught, rappel_pct=round(100 * caught / total_f, 1),
                         precision_pct=round(100 * caught / k, 1), montant_fraude_evite=round(saved, 0),
                         cout_revue=round(cost, 0), gain_net=round(saved - cost, 0)))
    gains = pd.DataFrame(rows)
    gains["modele"] = best_name
    _save(con, "ml_fraud_gains", gains)
    metrics.append(("fraude", "Fraudes dans le test / montant", total_f, f"{total_amt:,.0f} EUR au total"))
    # importance simple : coefficients du modèle linéaire standardisé
    lr = models["Régression logistique"]
    coef = pd.DataFrame({"variable": feats, "coefficient": lr[-1].coef_[0]}).sort_values("coefficient", key=abs, ascending=False).head(12)
    _save(con, "ml_fraud_coefficients", coef)


# ------------------------------------------------------------------ 3. Scoring crédit (German)
def german_scorecard(con, metrics: list):
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    df = pd.read_sql("SELECT * FROM fact_credit_application", con)
    y = df["is_default"]
    cat = ["checking_balance", "credit_history", "savings_balance", "purpose", "employment_length", "property", "other_installment_plans", "housing"]
    num = ["duration_months", "amount_dm", "installment_rate", "age"]
    # personal_status (contient le sexe), foreign_worker : exclus volontairement (non-discrimination)
    X = df[cat + num]
    pre = ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"), cat), ("n", StandardScaler(), num)])
    mk = lambda: make_pipeline(pre, LogisticRegression(C=0.3, max_iter=2000))
    oof = _cv_oof(mk, X, y)
    auc = roc_auc_score(y, oof)
    lo, hi = _bootstrap_auc(y, oof)
    metrics += [("credit_allemand", "AUC (CV 5x5)", auc, f"IC95 % [{lo:.3f} ; {hi:.3f}]"),
                ("credit_allemand", "Gini", 2 * auc - 1, "2 x AUC - 1 (convention banque)"),
                ("credit_allemand", "KS", _ks(y, oof), "")]
    d = pd.DataFrame({"y": y, "p": oof}).sort_values("p").reset_index(drop=True)
    rows = []
    for appr in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):   # on accepte les appr% dossiers les moins risqués
        k = int(len(d) * appr)
        acc, rej = d.head(k), d.tail(len(d) - k)
        cost = GERMAN_COST_BAD_ACCEPTED * acc["y"].sum() + GERMAN_COST_GOOD_REJECTED * (1 - rej["y"]).sum()
        rows.append(dict(taux_acceptation_pct=int(appr * 100), dossiers_acceptes=k,
                         taux_defaut_parmi_acceptes_pct=round(100 * acc["y"].mean(), 1) if k else 0.0,
                         defauts_evites_pct=round(100 * rej["y"].sum() / d["y"].sum(), 1), cout_total=round(cost, 0)))
    pol = pd.DataFrame(rows)
    _save(con, "ml_credit_policy", pol)
    best = pol.loc[pol["cout_total"].idxmin()]
    metrics.append(("credit_allemand", "Taux d'acceptation optimal (coût 5:1)", float(best["taux_acceptation_pct"]), f"coût {best['cout_total']:.0f} vs {pol.loc[pol['taux_acceptation_pct']==100,'cout_total'].iloc[0]:.0f} sans score"))
    log.info("ml      crédit allemand : AUC=%.3f Gini=%.3f", auc, 2 * auc - 1)


# ------------------------------------------------------------------ 4. Marketing
def marketing(con, metrics: list):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score

    df = pd.read_sql("SELECT * FROM fact_marketing_contact", con)
    y = df["subscribed"]
    cat = ["job", "marital_status", "education", "contact_channel", "previous_outcome", "contact_weekday"]
    num = ["age", "campaign_contacts", "previous_contacts", "euribor3m", "emp_var_rate", "cons_conf_idx", "contact_month"]
    X = pd.get_dummies(df[cat + num], columns=cat, dummy_na=True).astype(float)
    mk = lambda: HistGradientBoostingClassifier(max_iter=120, learning_rate=0.06, max_depth=3, random_state=SEED)
    oof = _cv_oof(mk, X, y, repeats=2)
    auc = roc_auc_score(y, oof)
    Xl = X.copy()
    Xl["call_duration_s"] = df["call_duration_s"].astype(float)       # variable INTERDITE : sert à montrer la fuite
    auc_leak = roc_auc_score(y, _cv_oof(mk, Xl, y, repeats=2))
    metrics += [("marketing", "AUC sans durée d'appel (utilisable)", auc, "CV 5x2"),
                ("marketing", "AUC AVEC durée d'appel (fuite)", auc_leak, "irréaliste : la durée est connue après l'appel")]
    d = pd.DataFrame({"y": y, "p": oof}).sort_values("p", ascending=False).reset_index(drop=True)
    d["decile"] = (np.arange(len(d)) * 10 // len(d)) + 1
    g = d.groupby("decile").agg(contacts=("y", "size"), souscriptions=("y", "sum")).reset_index()
    g["taux_conversion_pct"] = (100 * g["souscriptions"] / g["contacts"]).round(1)
    g["souscriptions_cumulees_pct"] = (100 * g["souscriptions"].cumsum() / g["souscriptions"].sum()).round(1)
    g["lift"] = (g["taux_conversion_pct"] / (100 * y.mean())).round(2)
    _save(con, "ml_marketing_deciles", g)
    log.info("ml      marketing : AUC=%.3f (avec fuite %.3f)", auc, auc_leak)


def run_ml(con) -> bool:
    if not _have_sklearn():
        log.warning("scikit-learn absent : étape ML ignorée (pip install scikit-learn)")
        return False
    metrics: list[tuple] = []
    for fn in (loan_default, card_fraud, german_scorecard, marketing):
        fn(con, metrics)
    m = pd.DataFrame(metrics, columns=["modele", "metrique", "valeur", "detail"])
    m["valeur"] = m["valeur"].astype(float).round(4)
    _save(con, "ml_metrics", m)
    con.commit()
    return True
