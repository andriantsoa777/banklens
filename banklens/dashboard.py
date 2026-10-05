"""Dashboard HTML autonome (un seul fichier, sans CDN) généré depuis la couche gold.

Cinq vues : Banque, Risque de prêt, Fraude carte, Scoring & marketing, Qualité & lineage.
Chaque graphique porte un titre-conclusion calculé, sa source (table gold + question) et une vue tableau.
"""
from __future__ import annotations

import pandas as pd

from .answers import n, pct
from .charts import bars, grouped_bars, hbars, line, table_html, esc
from .config import DASH, SQL
from .log import get_logger

log = get_logger()
_cache: dict = {}


def R(con, qid: str) -> pd.DataFrame:
    if qid not in _cache:
        f = next((SQL / "analysis").glob(f"{qid}_*.sql"))
        _cache[qid] = pd.read_sql(f.read_text(encoding="utf-8"), con)
    return _cache[qid]


def Q(con, sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, con)


def has(con, table: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone() is not None


# ------------------------------------------------------------------------------------------------ éléments d'interface
def kpi(label, value, sub="", tone=""):
    return f'<div class="kpi {tone}"><div class="kl">{esc(label)}</div><div class="kv">{value}</div><div class="ks">{esc(sub)}</div></div>'


def card(title, sub, svg, headers, rows, src, wide=False, note=""):
    tbl = table_html(headers, rows)
    return (f'<figure class="card{" wide" if wide else ""}"><figcaption><h3>{title}</h3><p class="sub">{sub}</p></figcaption>'
            f'<div class="plot">{svg}</div>'
            f'{f"<p class=note>{note}</p>" if note else ""}'
            f'<details class="dv"><summary>Voir les données</summary>{tbl}</details>'
            f'<p class="src">Source : {esc(src)}</p></figure>')


def section(sid, kicker, title, lead, kpis, cards):
    return (f'<section id="{sid}" class="view" role="tabpanel"><header class="vh"><p class="kick">{esc(kicker)}</p><h2>{title}</h2><p class="lead">{lead}</p></header>'
            f'<div class="kpis">{"".join(kpis)}</div><div class="grid">{"".join(cards)}</div></section>')


# ------------------------------------------------------------------------------------------------ vue BANQUE
def view_bank(con):
    q1, q2, q7, q16 = R(con, "Q01"), R(con, "Q02"), R(con, "Q07"), R(con, "Q16")
    q5, q4, q3, q17 = R(con, "Q05"), R(con, "Q04"), R(con, "Q03"), R(con, "Q17")
    q3 = pd.concat([q3[q3["tranche_age"] == "<25"], q3[q3["tranche_age"] != "<25"]])
    g = lambda ind: float(q1.loc[q1["indicateur"].str.startswith(ind), "valeur"].iloc[0])
    loans = R(con, "Q09")
    nb, tot = int(loans[loans["statut"].isin(["B", "D"])]["prets"].sum()), int(loans["prets"].sum())
    od = 100 - float(q7[q7["profil"].str.startswith("0")]["part_pct"].iloc[0])
    kpis = [kpi("Comptes", n(g("Comptes ouverts")), "4 500 titulaires, 5 369 clients"),
            kpi("Encours de dépôts", n(g("Encours"), 1) + " M", "au 31/12/1998 · CZK"),
            kpi("Transactions", n(g("Transactions") / 1e6, 2) + " M", "1993-1998"),
            kpi("Prêts accordés", n(g("Prêts accordés")), f"{n(g('Montant total prêté'), 1)} M CZK"),
            kpi("Défaut de prêt", pct(100 * nb / tot), f"{nb} sur {tot} prêts", "warn"),
            kpi("Comptes déjà à découvert", pct(od), "au moins un mois", "warn")]
    d = q2.copy()
    labels = list(d["year_month"])
    jan_idx = [(i, "janv.") for i, x in enumerate(labels) if x.endswith("-01") and x >= "1995-01"][:3]
    c1 = card(f"L'encours atteint {n(d['encours_m'].iloc[-1], 0)} M CZK fin 1998, avec un creux chaque janvier",
              "Encours de dépôts en fin de mois, M CZK (somme des soldes de tous les comptes)",
              line(labels, [("Encours", list(d["encours_m"]))], title="Encours mensuel", unit=" M", tick_every=12, note=jan_idx, w=1120, h=300),
              ["Mois", "Encours (M CZK)", "Flux net (M CZK)"], [[a, n(b, 1), n(c, 1)] for a, b, c in zip(d["year_month"], d["encours_m"], d["flux_net_m"])],
              "gold.fact_account_month · Q02", wide=True)
    c2 = card("Janvier et décembre : jusqu'à 34 % d'activité en plus qu'un mois moyen",
              "Indice d'activité par mois calendaire, 1994-1997 (100 = mois moyen)",
              bars([(str(m), float(v)) for m, v in zip(q16["mois"], q16["indice_activite_100"])], title="Indice d'activité", hi={"1", "12"}, xwrap=4),
              ["Mois", "Indice", "Retraits guichet"], [[a, n(b, 0), n(c, 0)] for a, b, c in zip(q16["mois"], q16["indice_activite_100"], q16["retraits_guichet"])],
              "gold.fact_transaction · Q16", note="Cause : retraits au guichet (52 % des opérations en janvier contre 22 % en moyenne).")
    cats = list(q5["canal"].unique())
    ops = [float(q5[q5["canal"] == c]["part_operations_pct"].sum()) for c in cats]
    amt = [float(q5[q5["canal"] == c]["part_montant_pct"].sum()) for c in cats]
    c3 = card("Une banque de guichet : 41 % des opérations et 76 % des montants en espèces",
              "Part des opérations et des montants par canal, %",
              grouped_bars(cats, [("Opérations", ops), ("Montants", amt)], title="Canaux", unit=" %", xwrap=14, fmt=lambda v: n(v, 0)),
              ["Canal", "% opérations", "% montants"], [[c, n(a, 1), n(b, 1)] for c, a, b in zip(cats, ops, amt)], "gold.fact_transaction × dim_tx_type · Q05")
    c4 = card(f"{pct(od)} des comptes ont déjà été à découvert, {n(int(q7[q7['profil'].str.startswith('3')]['comptes'].iloc[0]))} de façon chronique",
              "Nombre de comptes par profil de découvert (mois en négatif sur la période)",
              hbars([(p[2:], float(c)) for p, c in zip(q7["profil"], q7["comptes"])], title="Profils de découvert", hi={x[2:] for x in q7["profil"] if x[0] in "23"}, left=190, fmt=lambda v: n(v, 0)),
              ["Profil", "Comptes", "% prêt"], [[p[2:], n(c, 0), n(l, 1)] for p, c, l in zip(q7["profil"], q7["comptes"], q7["pct_avec_pret"])], "gold.fact_account_month · Q07",
              note="Les découverts récurrents s'accompagnent d'un crédit 2 à 3 fois plus souvent.")
    c5 = card("Les 65 ans et plus : peu de cartes, aucun prêt, des soldes plus bas",
              "Équipement par tranche d'âge du titulaire (% des comptes)",
              grouped_bars(list(q3["tranche_age"]), [("Carte", list(q3["pct_avec_carte"])), ("Prêt", list(q3["pct_avec_pret"]))], title="Équipement par âge", unit=" %", xwrap=6, fmt=lambda v: n(v, 0)),
              ["Âge", "Comptes", "% carte", "% prêt", "Solde moyen"], [[a, n(b, 0), n(c, 1), n(dd, 1), n(e, 0)] for a, b, c, dd, e in zip(q3["tranche_age"], q3["comptes"], q3["pct_avec_carte"], q3["pct_avec_pret"], q3["solde_moyen_1998"])],
              "gold.dim_account × fact_account_month · Q03")
    seg = q17.copy()
    c6 = card("Segmentation : 11 % de comptes Premium portent près d'un quart des dépôts",
              "Part de l'encours par segment (règles métier lisibles)",
              hbars([(s[2:].split(" (")[0], float(100 * e / seg["encours_m"].sum())) for s, e in zip(seg["segment"], seg["encours_m"])], title="Encours par segment", unit=" %", left=130, fmt=lambda v: n(v, 1)),
              ["Segment", "Comptes", "% comptes", "Encours M", "Solde moyen"], [[s, n(c, 0), n(p, 1), n(e, 1), n(sm, 0)] for s, c, p, e, sm in zip(seg["segment"], seg["comptes"], seg["part_comptes_pct"], seg["encours_m"], seg["solde_moyen"])],
              "gold.dim_account × fact_account_month · Q17")
    r = q4.sort_values("part_encours_pct", ascending=False)
    c7 = card("Les dépôts se répartissent comme les comptes : la géographie explique peu les soldes",
              "Part de l'encours par région, % (solde moyen quasi identique : 41,8 à 44,9 k CZK)",
              hbars([(x.title(), float(v)) for x, v in zip(r["region"], r["part_encours_pct"])], title="Encours par région", unit=" %", left=130, fmt=lambda v: n(v, 1)),
              ["Région", "Comptes", "Encours M", "Solde moyen", "Salaire district"], [[a, n(b, 0), n(c, 1), n(dd, 0), n(e, 0)] for a, b, c, dd, e in zip(r["region"], r["comptes"], r["encours_m"], r["solde_moyen"], r["salaire_moyen_district"])],
              "gold.dim_district × fact_account_month · Q04")
    return section("banque", "Berka · banque tchèque, 1993-1998", "Banque de détail : activité, dépôts et comportements",
                   "4 500 comptes, plus d'un million d'opérations. Ce que la banque fait, pour qui, et où se logent les risques.", kpis, [c1, c2, c3, c4, c5, c6, c7])


# ------------------------------------------------------------------------------------------------ vue RISQUE DE PRÊT
def view_loans(con):
    q9, q10, q11, q12 = R(con, "Q09"), R(con, "Q10"), R(con, "Q11"), R(con, "Q12")
    bad = q9[q9["statut"].isin(["B", "D"])]
    nb, tot = int(bad["prets"].sum()), int(q9["prets"].sum())
    kp = [kpi("Prêts", n(tot), f"{n(q9['montant_m'].sum(), 1)} M CZK"),
          kpi("Défaut en nombre", pct(100 * nb / tot), f"{nb} prêts B ou D", "warn"),
          kpi("Défaut en montant", pct(100 * bad["montant_m"].sum() / q9["montant_m"].sum()), f"{n(bad['montant_m'].sum(), 1)} M CZK exposés", "warn")]
    metrics = Q(con, "SELECT * FROM ml_metrics") if has(con, "ml_metrics") else None
    quint = Q(con, "SELECT * FROM ml_loan_risk_quintiles") if has(con, "ml_loan_risk_quintiles") else None
    if metrics is not None:
        m = metrics[(metrics["modele"] == "loan_default") & (metrics["metrique"] == "AUC (CV 5x5)")].iloc[0]
        kp.append(kpi("Pouvoir de discrimination (AUC)", n(m["valeur"], 2), str(m["detail"]), "good"))
        if quint is not None:
            top = quint[quint["decile_risque"] == 5].iloc[0]
            kp.append(kpi("Quintile le plus risqué", pct(top["taux_defaut"], 0) + " de défaut", f"{n(100 * top['defauts'] / quint['defauts'].sum(), 0)} % des défauts dans 20 % des prêts", "good"))
    amt = q10[q10["dimension"] == "Montant"]
    order = ["<50k", "50-100k", "100-200k", "200k+"]
    amt = amt.set_index("modalite").loc[order].reset_index()
    c1 = card("Au-dessus de 200 k CZK, un prêt sur cinq fait défaut : 4,7 fois plus que sous 50 k",
              "Taux de défaut par tranche de montant, %",
              bars([(a, float(b)) for a, b in zip(amt["modalite"], amt["taux_defaut_pct"])], title="Défaut par montant", unit=" %", hi={"200k+"}, fmt=lambda v: n(v, 1)),
              ["Tranche", "Prêts", "Défauts", "Taux %"], [[a, n(b, 0), n(c, 0), n(dd, 1)] for a, b, c, dd in zip(amt["modalite"], amt["prets"], amt["defauts"], amt["taux_defaut_pct"])], "gold.fact_loan · Q10")
    c2 = card("Le taux d'effort avant octroi prédit le défaut : 5 % sous 10 %, 27 % au-delà de 35 %",
              "Taux de défaut selon mensualité / entrées mensuelles des 6 mois précédant le prêt, %",
              bars([(t[2:], float(v)) for t, v in zip(q12["taux_effort"], q12["taux_defaut_pct"])], title="Défaut par taux d'effort", unit=" %", hi={q12["taux_effort"].iloc[-1][2:]}, fmt=lambda v: n(v, 1), xwrap=12),
              ["Taux d'effort", "Prêts", "Défauts", "Taux %", "Solde moyen avant"], [[t[2:], n(p, 0), n(d, 0), n(x, 1), n(s, 0)] for t, p, d, x, s in zip(q12["taux_effort"], q12["prets"], q12["defauts"], q12["taux_defaut_pct"], q12["solde_moyen_avant"])],
              "gold.fact_loan (variables pre_loan_*) · Q12", note="Signal calculé uniquement sur des données antérieures à l'octroi : utilisable en production.")
    c3 = card("1998 « s'améliore » seulement parce que ses prêts sont encore en cours",
              "Taux de défaut et part de prêts encore en cours, par année d'octroi, %",
              grouped_bars([str(int(a)) for a in q11["annee_octroi"]], [("Défaut", list(q11["taux_defaut_pct"])), ("Encore en cours", list(q11["pct_encore_en_cours"]))], title="Vintage", unit=" %", fmt=lambda v: n(v, 0)),
              ["Année", "Prêts", "Défaut %", "En cours %"], [[int(a), n(b, 0), n(c, 1), n(dd, 1)] for a, b, c, dd in zip(q11["annee_octroi"], q11["prets"], q11["taux_defaut_pct"], q11["pct_encore_en_cours"])],
              "gold.fact_loan × dim_date · Q11", note="Censure à droite : comparer des millésimes à âge égal, pas à date égale.")
    cards = [c1, c2, c3]
    if quint is not None:
        c4 = card("Le modèle isole 31 % de défaut dans son quintile le plus risqué, contre 5 % dans les trois premiers",
                  "Taux de défaut observé par quintile de score (prédictions hors-échantillon, validation croisée 5×5), %",
                  bars([(f"Q{int(a)}", float(b)) for a, b in zip(quint["decile_risque"], quint["taux_defaut"])], title="Quintiles de risque", unit=" %", hi={"Q5"}, fmt=lambda v: n(v, 1)),
                  ["Quintile", "Prêts", "Défauts", "Taux %", "Montant moyen"], [[int(a), n(b, 0), n(c, 0), n(dd, 1), n(e, 0)] for a, b, c, dd, e in zip(quint["decile_risque"], quint["prets"], quint["defauts"], quint["taux_defaut"], quint["montant_moyen"])],
                  "ml_loan_risk_quintiles (régression logistique)", note="Variables exclues volontairement : sexe et âge. 76 défauts seulement : l'intervalle de confiance de l'AUC est large (0,69 à 0,84).")
        co = Q(con, "SELECT * FROM ml_loan_coefficients")
        c5 = card("Les mois de découvert avant octroi et le montant pèsent le plus dans le score",
                  "Coefficients standardisés (positif = augmente le risque)",
                  hbars([(v.replace("_", " "), float(c)) for v, c in zip(co["variable"], co["coefficient_standardise"])], title="Coefficients", signed=True, left=200, fmt=lambda v: n(v, 2), xmax=1.4),
                  ["Variable", "Coefficient"], [[v, n(c, 3)] for v, c in zip(co["variable"], co["coefficient_standardise"])], "ml_loan_coefficients",
                  note="Lecture prudente : colinéarité montant / durée / mensualité ; un coefficient n'est pas une cause.")
        cards += [c4, c5]
    return section("pret", "Berka · portefeuille de 682 prêts", "Risque de crédit : qui fait défaut, et quand le voit-on ?",
                   "Du constat (taux de défaut) à la prévention (signaux avant octroi) puis au score, avec l'honnêteté statistique que l'échantillon impose.", kp, cards)


# ------------------------------------------------------------------------------------------------ vue FRAUDE
def view_fraud(con):
    f1, f2, f3 = R(con, "F01"), R(con, "F02"), R(con, "F03")
    fr = f1[f1["classe"] == "Fraude"].iloc[0]
    kp = [kpi("Transactions carte", n(f1["transactions"].sum()), "48 h, porteurs européens"),
          kpi("Fraudes", n(fr["transactions"]), f"{pct(fr['part_transactions_pct'], 3)} · 1 sur 599", "warn"),
          kpi("Montant moyen d'une fraude", n(fr["montant_moyen"], 0), f"contre {n(f1[f1['classe']=='Légitime']['montant_moyen'].iloc[0], 0)} en légitime")]
    gains = Q(con, "SELECT * FROM ml_fraud_gains") if has(con, "ml_fraud_gains") else None
    mt = Q(con, "SELECT * FROM ml_metrics") if has(con, "ml_metrics") else None
    if gains is not None:
        row = gains[gains["taux_alertes_pct"] == 0.25].iloc[0]
        kp.append(kpi("Fraudes captées avec 0,25 % d'alertes", pct(row["rappel_pct"], 0), f"{n(row['fraudes_captees'])} sur 93 · précision {pct(row['precision_pct'], 0)}", "good"))
        ap = mt[(mt["modele"] == "fraude / Gradient boosting") & (mt["metrique"].str.startswith("PR-AUC"))].iloc[0]["valeur"]
        kp.append(kpi("PR-AUC (test sur le futur)", n(ap, 2), "taux de base 0,13 %", "good"))
    c1 = card("De 0 h à 5 h : 8 % des transactions mais 24 % des fraudes, jusqu'à 9 fois le taux moyen",
              "Fraudes pour 10 000 transactions, par heure (48 h cumulées)",
              bars([(str(int(h)), float(v)) for h, v in zip(f2["heure"], f2["fraudes_pour_10000"])], title="Fraude par heure", hi={str(i) for i in range(0, 6)}, label_all=False, fmt=lambda v: n(v, 0), xwrap=3, w=1120, h=280),
              ["Heure", "Transactions", "Fraudes", "Pour 10 000"], [[int(a), n(b, 0), n(c, 0), n(dd, 1)] for a, b, c, dd in zip(f2["heure"], f2["transactions"], f2["fraudes"], f2["fraudes_pour_10000"])],
              "gold.fact_card_tx × dim_hour · F02", wide=True, note="Barres en couleur d'alerte : fenêtre 0 h – 5 h. Heure relative au début du jeu (pas de fuseau).")
    c2 = card("Les montants nuls et les micro-montants : un signe de test de carte",
              "Part des fraudes et des transactions légitimes par tranche de montant, %",
              grouped_bars(list(f3["tranche_montant"]), [("Fraudes", list(f3["part_des_fraudes_pct"])), ("Légitimes", list(f3["part_des_legitimes_pct"]))], title="Montants", unit=" %", xwrap=8, fmt=lambda v: n(v, 0)),
              ["Tranche", "Transactions", "Fraudes", "% fraudes", "% légitimes", "Pour 10 000"], [[a, n(b, 0), n(c, 0), n(d, 1), n(e, 1), n(f, 1)] for a, b, c, d, e, f in zip(f3["tranche_montant"], f3["transactions"], f3["fraudes"], f3["part_des_fraudes_pct"], f3["part_des_legitimes_pct"], f3["fraudes_pour_10000"])],
              "gold.fact_card_tx · F03")
    cards = [c1]
    if gains is not None:
        c3 = card("Examiner 0,25 % des transactions suffit à capter 76 % des fraudes en valeur nette maximale",
                  "Gain net (fraude évitée − coût de revue) selon le taux d'alertes, EUR — hypothèse : 5 EUR par alerte examinée",
                  line([n(a, 2) + " %" for a in gains["taux_alertes_pct"]], [("Gain net", list(gains["gain_net"]))], title="Gain net", tick_every=1, unit="", fmt=lambda v: n(v, 0), w=1120, h=280),
                  ["Alertes %", "Alertes", "Fraudes captées", "Rappel %", "Précision %", "Fraude évitée", "Coût revue", "Gain net"],
                  [[n(a, 2), n(b, 0), n(c, 0), n(d, 1), n(e, 1), n(f, 0), n(g, 0), n(h, 0)] for a, b, c, d, e, f, g, h in zip(gains["taux_alertes_pct"], gains["alertes"], gains["fraudes_captees"], gains["rappel_pct"], gains["precision_pct"], gains["montant_fraude_evite"], gains["cout_revue"], gains["gain_net"])],
                  "ml_fraud_gains (jeu de test = derniers 25 % du temps)", wide=True,
                  note="Au-delà d'environ 0,5 % d'alertes, chaque revue coûte plus qu'elle ne rapporte : c'est le vrai critère de choix du seuil, pas l'AUC.")
        cards.append(c3)
        cards.append(c2)
        co = Q(con, "SELECT * FROM ml_fraud_coefficients")
        top3 = ", ".join(v.upper() for v in co["variable"].head(3))
        cards.append(card(f"{top3} pèsent le plus dans le modèle linéaire",
                  "Coefficients standardisés des 12 variables les plus fortes",
                  hbars([(v.upper(), float(c)) for v, c in zip(co["variable"], co["coefficient"])], title="Coefficients fraude", signed=True, left=80, fmt=lambda v: n(v, 2), xmax=2.5),
                  ["Variable", "Coefficient"], [[v, n(c, 3)] for v, c in zip(co["variable"], co["coefficient"])], "ml_fraud_coefficients"))
    if gains is None:
        cards.append(c2)
    return section("fraude", "Kaggle / ULB · transactions de cartes européennes, sept. 2013", "Fraude carte : repérer 1 transaction sur 600",
                   "Un problème où l'exactitude ne veut rien dire : tout se joue sur le tri, le coût d'une alerte et le moment (nuit).", kp, cards)


# ------------------------------------------------------------------------------------------------ vue SCORING & MARKETING
def view_scoring(con):
    g01, g02 = R(con, "G01"), R(con, "G02")
    m01, m02, m03, m04 = R(con, "M01"), R(con, "M02"), R(con, "M03"), R(con, "M04")
    mt = Q(con, "SELECT * FROM ml_metrics") if has(con, "ml_metrics") else None
    glob = m01[m01["dimension"] == "Global"].iloc[0]
    kp = [kpi("Dossiers de crédit", "1 000", "UCI Statlog German Credit"), kpi("Défaut", "30 %", "300 mauvais payeurs", "warn")]
    if mt is not None:
        a = mt[(mt["modele"] == "credit_allemand") & (mt["metrique"] == "AUC (CV 5x5)")].iloc[0]
        kp.append(kpi("Scorecard : Gini", n(2 * a["valeur"] - 1, 2), f"AUC {n(a['valeur'], 2)} · {a['detail']}", "good"))
    kp += [kpi("Contacts marketing", n(glob["contacts"]), "échantillon UCI Bank Marketing"), kpi("Conversion globale", pct(glob["taux_conversion_pct"]), f"{int(glob['souscriptions'])} souscriptions")]
    iv = g02.copy()
    c1 = card("Le statut du compte courant écrase toutes les autres variables (IV 0,66)",
              "Information Value par variable (> 0,3 = forte, 0,1 – 0,3 = moyenne, < 0,1 = faible)",
              hbars([(v, float(x)) for v, x in zip(iv["variable"], iv["information_value"])], title="Information value", hi={iv["variable"].iloc[0]}, left=150, fmt=lambda v: n(v, 2)),
              ["Variable", "IV", "Force"], [[v, n(x, 3), f] for v, x, f in zip(iv["variable"], iv["information_value"], iv["force"])], "gold.fact_credit_application · G02")
    chk = g01[g01["variable"] == "Compte courant"].sort_values("taux_defaut_pct", ascending=False)
    c2 = card("Un compte à découvert : 49 % de défaut. Aucun compte connu : 12 %",
              "Taux de défaut par statut du compte courant, %",
              bars([(m.replace(" DM", ""), float(v)) for m, v in zip(chk["modalite"], chk["taux_defaut_pct"])], title="Défaut par compte courant", unit=" %", hi={chk["modalite"].iloc[0].replace(" DM", "")}, fmt=lambda v: n(v, 1), xwrap=8),
              ["Statut", "Dossiers", "Défauts", "Taux %"], [[m, n(d, 0), n(f, 0), n(t, 1)] for m, d, f, t in zip(chk["modalite"], chk["dossiers"], chk["defauts"], chk["taux_defaut_pct"])], "gold.fact_credit_application · G01",
              note="Contre-intuitif : « pas de compte courant » est le profil le plus sûr. Biais de sélection : on ne voit que les crédits accordés.")
    cards = [c1, c2]
    if has(con, "ml_credit_policy"):
        pol = Q(con, "SELECT * FROM ml_credit_policy")
        cards.append(card(f"Avec un coût 5 pour 1, le score divise le coût de décision par {n(float(pol.loc[pol['taux_acceptation_pct'] == 100, 'cout_total'].iloc[0]) / float(pol['cout_total'].min()), 1)}",
                          "Coût total selon le taux d'acceptation (accepter un mauvais payeur coûte 5 fois refuser un bon, matrice UCI)",
                          line([str(int(x)) + " %" for x in pol["taux_acceptation_pct"]], [("Coût", list(pol["cout_total"]))], title="Coût par taux d'acceptation", tick_every=1, fmt=lambda v: n(v, 0)),
                          ["Acceptation %", "Acceptés", "Défaut parmi acceptés %", "Défauts évités %", "Coût"], [[int(a), n(b, 0), n(c, 1), n(d, 1), n(e, 0)] for a, b, c, d, e in zip(pol["taux_acceptation_pct"], pol["dossiers_acceptes"], pol["taux_defaut_parmi_acceptes_pct"], pol["defauts_evites_pct"], pol["cout_total"])],
                          "ml_credit_policy (prédictions hors-échantillon)", note="Le ratio 5:1 est une hypothèse de la source UCI ; la politique réelle dépend de la marge et du coût de refus."))
    eu = m03.sort_values("contexte_taux")
    c3 = card("Marketing : la conversion s'effondre quand l'Euribor monte (42 % → 5 %)",
              "Taux de souscription selon l'Euribor 3 mois au moment de l'appel, %",
              bars([(c[2:].replace("euribor ", ""), float(v)) for c, v in zip(eu["contexte_taux"], eu["taux_conversion_pct"])], title="Conversion par Euribor", unit=" %", fmt=lambda v: n(v, 1), xwrap=10),
              ["Contexte", "Contacts", "Souscriptions", "Taux %"], [[c, n(a, 0), n(b, 0), n(d, 1)] for c, a, b, d in zip(eu["contexte_taux"], eu["contacts"], eu["souscriptions"], eu["taux_conversion_pct"])], "gold.fact_marketing_contact · M03",
              note="Effet de période, pas causal : l'Euribor est confondu avec la date de la campagne (2008-2010).")
    c4 = card("Insister ne paie pas : au-delà de 6 appels, la conversion est divisée par 5,6",
              "Taux de souscription selon le nombre de contacts de la campagne, %",
              bars([(p, float(v)) for p, v in zip(m02["pression"], m02["taux_conversion_pct"])], title="Conversion par pression", unit=" %", hi={m02["pression"].iloc[-1]}, fmt=lambda v: n(v, 1), xwrap=10),
              ["Pression", "Contacts", "Souscriptions", "Taux %"], [[p, n(a, 0), n(b, 0), n(d, 1)] for p, a, b, d in zip(m02["pression"], m02["contacts"], m02["souscriptions"], m02["taux_conversion_pct"])], "gold.fact_marketing_contact · M02")
    cards += [c3, c4]
    if has(con, "ml_marketing_deciles"):
        dec = Q(con, "SELECT * FROM ml_marketing_deciles")
        cards.append(card("Appeler les 10 % de contacts les mieux scorés capte 42 % des souscriptions",
                          "Souscriptions cumulées selon la part de contacts appelés (classés par score), %",
                          line([str(int(d)) + "0 %" for d in dec["decile"]], [("Modèle", list(dec["souscriptions_cumulees_pct"]))], title="Courbe de gain", tick_every=1, fmt=lambda v: n(v, 0), unit=" %"),
                          ["Décile", "Contacts", "Souscriptions", "Conversion %", "Cumul %", "Lift"], [[int(a), n(b, 0), n(c, 0), n(d, 1), n(e, 1), n(f, 2)] for a, b, c, d, e, f in zip(dec["decile"], dec["contacts"], dec["souscriptions"], dec["taux_conversion_pct"], dec["souscriptions_cumulees_pct"], dec["lift"])],
                          "ml_marketing_deciles (variables disponibles AVANT l'appel)"))
        a1 = mt[(mt["modele"] == "marketing") & (mt["metrique"].str.startswith("AUC sans"))].iloc[0]["valeur"]
        a2 = mt[(mt["modele"] == "marketing") & (mt["metrique"].str.startswith("AUC AVEC"))].iloc[0]["valeur"]
        cards.append(card("La durée d'appel gonfle l'AUC de 0,75 à 0,93 : une fuite de données à écarter",
                          "AUC du même modèle avec et sans la durée de l'appel",
                          bars([("Sans durée (utilisable)", float(a1)), ("Avec durée (fuite)", float(a2))], title="Effet de la fuite", hi={"Avec durée (fuite)"}, fmt=lambda v: n(v, 2), ymax=1.0, xwrap=14),
                          ["Modèle", "AUC"], [["Sans durée", n(a1, 3)], ["Avec durée", n(a2, 3)]], "ml_metrics", note="La durée n'est connue qu'à la fin de l'appel : elle ne peut pas servir à choisir qui appeler."))
    return section("scoring", "UCI · German Credit & Bank Marketing", "Scoring de crédit et marketing : les pièges de la modélisation",
                   "Deux petits jeux classiques, traités avec les règles d'un vrai projet : pas de fuite, validation croisée, décision chiffrée.", kp, cards)


# ------------------------------------------------------------------------------------------------ vue QUALITÉ
def view_quality(con):
    dq = Q(con, "SELECT * FROM dq_results")
    fixes = Q(con, "SELECT source, tbl, fix_id, description, rows_affected FROM dq_fixes WHERE rows_affected > 0 ORDER BY rows_affected DESC")
    quar = Q(con, "SELECT source, tbl, rule_id, detail, COUNT(*) AS lignes FROM quarantine GROUP BY 1,2,3,4")
    log = Q(con, "SELECT source, tbl, source_file, rows_in_file, rows_loaded, sha256 FROM meta_load_log")
    npass, nwarn, nfail = (dq["status"] == "PASS").sum(), (dq["status"] == "WARN").sum(), (dq["status"] == "FAIL").sum()
    kp = [kpi("Règles de qualité", str(len(dq)), "6 dimensions"), kpi("Réussies", str(npass), "PASS", "good"), kpi("Avertissements", str(nwarn), "publiés, visibles", "warn"),
          kpi("Bloquantes en échec", str(nfail), "le pipeline s'arrête"), kpi("Lignes en quarantaine", n(quar["lignes"].sum()) if len(quar) else "0", "doublons exacts carte")]
    chips = {"PASS": "ok", "WARN": "warn", "FAIL": "ko"}
    rows = "".join(f'<tr><td class="mono">{r.rule_id}</td><td>{esc(r.dimension)}</td><td>{esc(r.description)}</td><td class="r">{n(r.checked)}</td><td class="r">{n(r.failed)}</td><td><span class="chip {chips[r.status]}">{r.status}</span></td></tr>' for r in dq.itertuples())
    t_dq = f'<div class="tw"><table><thead><tr><th>Règle</th><th>Dimension</th><th>Contrôle</th><th class="r">Vérifié</th><th class="r">Échecs</th><th>Statut</th></tr></thead><tbody>{rows}</tbody></table></div>'
    dims = dq.groupby("dimension").agg(regles=("rule_id", "count"), ok=("status", lambda s: (s == "PASS").sum())).reset_index()
    c0 = f'<figure class="card wide"><figcaption><h3>{npass} règles sur {len(dq)} passent ; {nwarn} avertissements sont de vrais constats sur la source</h3><p class="sub">Contrôles exécutés après le silver, résultat stocké dans la table <code>dq_results</code></p></figcaption>{t_dq}<p class="src">Source : banklens/dq.py</p></figure>'
    fx = fixes.head(14)
    c1 = card("Ce que le nettoyage a corrigé, et sur combien de lignes",
              "Corrections tracées dans <code>dq_fixes</code> (14 plus importantes)",
              hbars([(f"{r.fix_id} · {r.tbl}", float(r.rows_affected)) for r in fx.itertuples()], title="Corrections", left=120, fmt=lambda v: n(v, 0), xmax=1_100_000, w=1100),
              ["Code", "Source", "Table", "Correction", "Lignes"], [[r.fix_id, r.source, r.tbl, r.description, n(r.rows_affected)] for r in fixes.itertuples()], "silver.py → dq_fixes", wide=True)
    lin = Q(con, """SELECT 'berka.trans' AS flux, (SELECT COUNT(*) FROM bronze_berka_trans) AS bronze, (SELECT COUNT(*) FROM silver_transaction) AS silver, (SELECT COUNT(*) FROM fact_transaction) AS gold
                    UNION ALL SELECT 'berka.account', (SELECT COUNT(*) FROM bronze_berka_account), (SELECT COUNT(*) FROM silver_account), (SELECT COUNT(*) FROM dim_account)
                    UNION ALL SELECT 'berka.loan', (SELECT COUNT(*) FROM bronze_berka_loan), (SELECT COUNT(*) FROM silver_loan), (SELECT COUNT(*) FROM fact_loan)
                    UNION ALL SELECT 'fraude.card_tx', (SELECT COUNT(*) FROM bronze_fraud_card_tx), (SELECT COUNT(*) FROM silver_card_tx), (SELECT COUNT(*) FROM fact_card_tx)
                    UNION ALL SELECT 'german.credit', (SELECT COUNT(*) FROM bronze_german_credit), (SELECT COUNT(*) FROM silver_credit_application), (SELECT COUNT(*) FROM fact_credit_application)
                    UNION ALL SELECT 'marketing.contact', (SELECT COUNT(*) FROM bronze_marketing_contact), (SELECT COUNT(*) FROM silver_marketing_contact), (SELECT COUNT(*) FROM fact_marketing_contact)""")
    rows = "".join(f'<tr><td class="mono">{r.flux}</td><td class="r">{n(r.bronze)}</td><td class="r">{n(r.silver)}</td><td class="r">{n(r.gold)}</td><td class="r">{n(r.bronze - r.silver)}</td></tr>' for r in lin.itertuples())
    c2 = (f'<figure class="card wide"><figcaption><h3>Réconciliation bronze → silver → gold : aucune ligne ne disparaît sans trace</h3>'
          f'<p class="sub">Nombre de lignes à chaque couche ; l\'écart bronze − silver est exactement la quarantaine</p></figcaption>'
          f'<div class="tw"><table><thead><tr><th>Flux</th><th class="r">Bronze</th><th class="r">Silver</th><th class="r">Gold</th><th class="r">Écart (quarantaine)</th></tr></thead><tbody>{rows}</tbody></table></div><p class="src">Source : meta_load_log, tables silver_* et gold</p></figure>')
    rows = "".join(f'<tr><td>{esc(r.source)}</td><td class="mono">{esc(r.source_file)}</td><td class="r">{n(r.rows_in_file)}</td><td class="mono sha">{r.sha256[:16]}…</td></tr>' for r in log.itertuples())
    c3 = (f'<figure class="card wide"><figcaption><h3>Fichiers sources et empreintes SHA-256</h3><p class="sub">Un fichier modifié sans bruit changerait son empreinte : le chargement est reproductible et vérifiable</p></figcaption>'
          f'<div class="tw"><table><thead><tr><th>Source</th><th>Fichier</th><th class="r">Lignes</th><th>SHA-256 (début)</th></tr></thead><tbody>{rows}</tbody></table></div><p class="src">Source : data/MANIFEST.json, meta_load_log</p></figure>')
    return section("qualite", "Gouvernance des données", "Qualité et traçabilité : prouver que les chiffres sont fiables",
                   "Le tableau de bord ne vaut que par la confiance qu'on peut lui accorder. Voici ce qui a été vérifié, corrigé, mis de côté.", kp, [c0, c1, c2, c3])


# ------------------------------------------------------------------------------------------------ page


def build_dashboard(con):
    from pathlib import Path
    css = (Path(__file__).parent / "dashboard.css").read_text(encoding="utf-8")
    js = (Path(__file__).parent / "dashboard.js").read_text(encoding="utf-8")
    views = [view_bank(con), view_loans(con), view_fraud(con), view_scoring(con), view_quality(con)]
    tabs = [("banque", "Banque"), ("pret", "Risque de prêt"), ("fraude", "Fraude carte"), ("scoring", "Scoring & marketing"), ("qualite", "Qualité & lineage")]
    nav = "".join(f'<button class="tab" role="tab" data-t="{i}" aria-controls="{i}">{l}</button>' for i, l in tabs)
    batch = con.execute("SELECT MAX(batch_id) FROM meta_load_log").fetchone()[0]
    html_ = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BankLens - tableau de bord</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style></head><body>
<header class="top"><div class="brand"><span class="logo">B</span><div><b>BankLens</b><small>Plateforme BI bancaire · bronze → silver → gold</small></div></div>
<nav class="tabs" role="tablist">{nav}</nav>
<div class="tools"><a class="btn" href="architecture.html">Architecture</a><button class="btn" id="theme" aria-label="Changer de thème">Mode sombre</button></div></header>
<main>{"".join(views)}</main>
<footer><p>Données publiques réelles : <b>Berka</b> (PKDD'99, banque tchèque), <b>Kaggle / ULB</b> (fraude carte), <b>UCI</b> (German Credit, Bank Marketing). Chargement du lot {esc(batch)}.
Les valeurs sont recalculées par le pipeline ; aucune n'est saisie à la main.</p></footer>
<div id="tip" role="tooltip" hidden></div><script>{js}</script></body></html>'''
    DASH.mkdir(parents=True, exist_ok=True)
    (DASH / "index.html").write_text(html_, encoding="utf-8")
    log.info("dashboard %s (%d Ko)", DASH / "index.html", len(html_) // 1024)
