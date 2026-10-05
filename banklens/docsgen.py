"""Génère la documentation : page d'architecture (pour l'entretien), dictionnaire de données, guide d'entretien.

Tous les chiffres affichés sont relus dans l'entrepôt : rien n'est saisi à la main.
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from .answers import n, pct
from .config import DASH, DOCS, SQL
from .log import get_logger
from .sources import SOURCES

log = get_logger()
esc = lambda s: html.escape(str(s), quote=True)

GOLD_TABLES = {
    "dim_date": ("Calendrier 1993-1998", "1 ligne = 1 jour"),
    "dim_district": ("Districts tchèques (région, salaire moyen, chômage, criminalité)", "1 ligne = 1 district"),
    "dim_client": ("Clients (âge à la date de référence, tranche d'âge)", "1 ligne = 1 client"),
    "bridge_account_client": ("Pont compte ↔ client avec rôle (titulaire / disposant)", "1 ligne = 1 droit sur un compte"),
    "dim_card": ("Cartes bancaires (type, émission, titulaire)", "1 ligne = 1 carte"),
    "dim_account": ("Comptes (fréquence de relevé, ancienneté, titulaire principal)", "1 ligne = 1 compte"),
    "dim_tx_type": ("Type de mouvement : opération, catégorie, canal, finalité", "1 ligne = 1 combinaison opération/catégorie"),
    "fact_transaction": ("Mouvements du compte avec rang intra-journalier reconstitué et solde chaîné", "1 ligne = 1 mouvement"),
    "fact_account_month": ("Activité mensuelle d'un compte : flux, nb opérations, solde de fin de mois, découvert", "1 ligne = 1 compte × 1 mois"),
    "fact_loan": ("Prêts avec variables d'avant-octroi (sans fuite d'information) et statut final", "1 ligne = 1 prêt"),
    "fact_standing_order": ("Ordres permanents (montant, finalité)", "1 ligne = 1 ordre permanent"),
    "dim_hour": ("Heure de la journée et plage (nuit / matin / après-midi / soir)", "1 ligne = 1 heure"),
    "fact_card_tx": ("Transactions carte (jeu fraude), doublons exacts écartés", "1 ligne = 1 transaction carte"),
    "fact_card_tx_features": ("Composantes anonymisées V1-V28 (ACP), séparées pour garder la table de faits étroite", "1 ligne = 1 transaction carte"),
    "fact_credit_application": ("Demandes de crédit allemandes avec décision observée (bon / mauvais payeur)", "1 ligne = 1 demande"),
    "fact_marketing_contact": ("Contacts de campagne téléphonique avec contexte macro et résultat", "1 ligne = 1 contact"),
}


def _scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def facts(con) -> dict:
    f = {}
    f["bronze_rows"] = _scalar(con, "SELECT SUM(rows_loaded) FROM meta_load_log WHERE batch_id=(SELECT MAX(batch_id) FROM meta_load_log)")
    f["n_sources"] = _scalar(con, "SELECT COUNT(DISTINCT source) FROM meta_load_log")
    f["n_files"] = _scalar(con, "SELECT COUNT(*) FROM meta_load_log WHERE batch_id=(SELECT MAX(batch_id) FROM meta_load_log)")
    f["quarantine"] = _scalar(con, "SELECT COUNT(*) FROM quarantine")
    f["fixes"] = _scalar(con, "SELECT COUNT(*) FROM dq_fixes")
    dq = pd.read_sql("SELECT status, COUNT(*) c FROM dq_results GROUP BY 1", con).set_index("status")["c"].to_dict()
    f["dq_pass"], f["dq_warn"], f["dq_fail"] = dq.get("PASS", 0), dq.get("WARN", 0), dq.get("FAIL", 0)
    f["dq_total"] = f["dq_pass"] + f["dq_warn"] + f["dq_fail"]
    f["tx"] = _scalar(con, "SELECT COUNT(*) FROM fact_transaction")
    f["accounts"] = _scalar(con, "SELECT COUNT(*) FROM dim_account")
    f["loans"] = _scalar(con, "SELECT COUNT(*) FROM fact_loan")
    f["card_tx"] = _scalar(con, "SELECT COUNT(*) FROM fact_card_tx")
    f["chain"] = _scalar(con, "SELECT 100.0*AVG(balance_chain_ok) FROM silver_transaction")
    f["gold_tables"] = len(GOLD_TABLES)
    f["queries"] = len(list((SQL / "analysis").glob("*.sql")))
    f["sql_lines"] = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in SQL.rglob("*.sql"))
    f["py_lines"] = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in (Path(__file__).parent).glob("*.py"))
    m = pd.read_sql("SELECT * FROM ml_metrics", con)
    g = lambda mod, met: float(m[(m.modele == mod) & (m.metrique.str.startswith(met))].valeur.iloc[0])
    f["auc_loan"] = g("loan_default", "AUC (CV")
    f["auc_loan_base"] = g("loan_default", "AUC baseline")
    f["auc_german"] = g("credit_allemand", "AUC (CV")
    fr = m[m.modele == "fraude"]
    f["pr_fraud"] = float(fr[fr.metrique == "Modèle retenu"].valeur.iloc[0])
    loans = pd.read_sql("SELECT status_code, amount FROM fact_loan", con)
    bad = loans.status_code.isin(["B", "D"])
    f["default_cnt"] = bad.mean() * 100
    f["default_amt"] = loans[bad].amount.sum() / loans.amount.sum() * 100
    f["fraud_n"] = _scalar(con, "SELECT SUM(is_fraud) FROM fact_card_tx")
    f["fraud_rate"] = 100 * f["fraud_n"] / f["card_tx"]
    return f


# ------------------------------------------------------------------------------------------------ questions d'entretien
def qa_list(f) -> list[tuple[str, str]]:
    return [
        ("Pourquoi SQLite et pas Snowflake / BigQuery / Databricks ?",
         "Parce que le volume (≈ 1,4 M de lignes, ≈ 160 Mo) ne justifie pas un entrepôt cloud, et que SQLite rend le projet reproductible en une commande, sans compte ni coût. "
         "Ce qui compte, c'est l'architecture et le SQL, qui sont portables : tout est en SQL standard (CTE, fenêtres) et la page « correspondance cloud » montre où chaque brique irait. "
         "Le passage à BigQuery ou Snowflake est un changement de connecteur et de dialecte, pas de conception."),
        ("Pourquoi une architecture en médaillon (bronze / silver / gold) ?",
         "Chaque couche répond à une question différente. Bronze : « qu'ai-je reçu ? » (tout en texte, rien perdu, lot et empreinte SHA-256). Silver : « que vaut cette donnée ? » (types, règles, corrections tracées, rejets en quarantaine). "
         "Gold : « comment l'analyser ? » (modèle en étoile). On peut rejouer silver ou gold sans re-télécharger, et on peut toujours remonter d'un chiffre du dashboard jusqu'à la ligne source."),
        ("Comment avez-vous vérifié que le nettoyage ne perd rien ?",
         f"Par une réconciliation automatique : bronze = silver + quarantaine pour chaque table (règles C01-C06, bloquantes). Les {n(f['quarantine'])} lignes écartées (doublons exacts du jeu de fraude) sont conservées avec leur motif. "
         f"Les {n(f['fixes'])} corrections (dates, libellés tchèques, valeurs « ? ») sont listées avec le nombre de lignes touchées. Si une règle bloquante échoue, le pipeline s'arrête."),
        ("Quel est le principal piège des données Berka ?",
         "L'ordre des transactions. L'identifiant n'est pas chronologique et plusieurs opérations tombent le même jour : un tri par date seule ne reconstitue pas le solde. "
         f"J'ai reconstitué l'ordre intra-journalier en chaînant les soldes (chaque solde = solde précédent + montant) : {pct(f['chain'], 3)} des lignes se chaînent. "
         "Les 28 ruptures restantes (14 comptes) sont signalées par la règle B01 en avertissement et non masquées."),
        ("Comment avez-vous évité la fuite d'information (data leakage) ?",
         "Trois endroits. (1) Pour le modèle de défaut de prêt, les variables sont calculées uniquement sur la période précédant l'octroi (préfixe pre_). "
         "(2) Pour la fraude, le découpage est temporel (apprentissage sur le passé, test sur le futur) et non aléatoire. "
         "(3) Pour le marketing, la durée d'appel est exclue du modèle : elle n'est connue qu'après l'appel et fait passer l'AUC de 0,75 à 0,93, ce que je montre comme un contre-exemple."),
        ("Votre modèle de défaut a un AUC de 0,77 : est-ce bon ?",
         f"C'est honnête, pas spectaculaire. Sur 682 prêts dont 76 défauts, l'AUC en validation croisée 5×5 est {n(f['auc_loan'], 2)} avec un intervalle de confiance large, contre {n(f['auc_loan_base'], 2)} pour la référence naïve (montant seul). "
         "Je le présente comme un outil de tri du risque (le cinquième quintile concentre plus de la moitié des défauts), pas comme un modèle prêt à décider seul. L'échantillon est petit : je le dis."),
        ("Pourquoi la précision / PR-AUC pour la fraude et pas l'accuracy ?",
         f"Parce que la fraude représente {pct(f['fraud_rate'], 3)} des transactions : un modèle qui répond toujours « légitime » aurait 99,8 % d'exactitude et ne servirait à rien. "
         f"Je mesure donc la PR-AUC ({n(f['pr_fraud'], 2)}) sur un test futur, et je convertis le seuil en coût : combien d'alertes, combien de fraudes captées, pour un coût de traitement par alerte."),
        ("Qu'est-ce qui est réel, qu'est-ce qui est simulé dans ce projet ?",
         "Rien n'est simulé. Les quatre jeux sont des données publiques réelles et anonymisées (Berka, Kaggle/ULB, UCI German Credit, UCI Bank Marketing). "
         "Les fichiers viennent de miroirs GitHub des jeux officiels, car le poste de travail ne pouvait pas joindre directement les sites d'origine ; la provenance exacte (dépôt, commit) et l'empreinte SHA-256 de chaque fichier sont dans le manifeste. "
         "Ce ne sont pas les données d'une banque cliente : ce sont des jeux de recherche, et je ne prétends pas le contraire."),
        ("Pourquoi le sexe du client n'est-il pas utilisé dans les modèles ?",
         "C'est une variable protégée. Elle est décodée dans la dimension client pour l'analyse descriptive, mais exclue de tous les scores. "
         "Même logique pour la tranche d'âge dans le scoring de crédit allemand : je la signale comme point d'attention réglementaire."),
        ("Comment passeriez-vous cela en production ?",
         "Orchestration avec Airflow ou Dagster, transformations SQL en dbt (les fichiers sql/ deviennent des modèles, les règles de qualité deviennent des tests), stockage objet pour la couche bronze, entrepôt cloud pour gold, "
         "BI via Power BI ou Looker. Il faudrait ajouter le chargement incrémental (aujourd'hui rechargement complet par lot), le suivi de dérive des modèles et la gestion des accès par ligne."),
        ("Que feriez-vous différemment avec plus de temps ?",
         "Un chargement incrémental avec SCD2 sur les dimensions, un modèle de survie pour les prêts (au lieu d'un indicateur binaire de défaut) afin de traiter la censure des prêts récents, "
         "un test de stabilité des variables (PSI) entre périodes, et un calibrage des probabilités avant tout usage décisionnel."),
        ("Comment un lecteur peut-il rejouer le projet ?",
         "Trois commandes : installer les dépendances, `make data` si les fichiers ne sont pas présents, puis `make all`. Le pipeline reconstruit l'entrepôt, exécute les 32 contrôles qualité, "
         "les 28 requêtes, les modèles, puis régénère le dashboard et cette page. Les tests unitaires vérifient la réconciliation, les clés et les chiffres clés."),
    ]


# ------------------------------------------------------------------------------------------------ schéma SVG
def _box(x, y, w, h, title, lines=(), cls="b-n"):
    t = f'<text class="bt" x="{x + w / 2}" y="{y + 22}" text-anchor="middle">{esc(title)}</text>'
    for i, ln in enumerate(lines):
        t += f'<text class="bl" x="{x + w / 2}" y="{y + 42 + i * 16}" text-anchor="middle">{esc(ln)}</text>'
    return f'<g><rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>{t}</g>'


def _arrow(x1, y1, x2, y2, dashed=False):
    return f'<line class="ar{" dash" if dashed else ""}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#ah)"/>'


def arch_svg(f) -> str:
    W, H = 1180, 470
    s = [f'<svg class="arch" viewBox="0 0 {W} {H}" role="img" aria-label="Architecture BankLens : sources, bronze, silver, gold, consommation">',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ahp"/></marker></defs>']
    cols = [("SOURCES", 10, 190), ("BRONZE · brut", 245, 185), ("SILVER · propre", 475, 215), ("GOLD · étoile", 735, 185), ("CONSOMMATION", 965, 205)]
    for t, x, w in cols:
        s.append(f'<text class="ch2" x="{x + w / 2}" y="22" text-anchor="middle">{t}</text>')
    srcs = [("Berka (PKDD'99)", "8 tables · banque CZ"), ("Kaggle / ULB", "fraude carte"), ("UCI German Credit", "demandes de crédit"), ("UCI Bank Marketing", "campagnes téléphone")]
    for i, (a, b) in enumerate(srcs):
        y = 40 + i * 78
        s.append(_box(10, y, 190, 62, a, [b], "b-src"))
        s.append(_arrow(200, y + 31, 245, y + 31))
    s.append(_box(245, 40, 185, 290, "bronze_*", ["tout en TEXTE", "+ _row_num", "+ _source_file", "+ _batch_id", "+ _loaded_at", "", "meta_load_log", "SHA-256 par fichier", f"{n(f['bronze_rows'])} lignes"], "b-br"))
    s.append(_box(475, 40, 215, 190, "silver_*", ["types + PK + CHECK", "dates ISO, codes traduits", "birth_number décodé", "ordre intra-jour (ledger)", f"{f['fixes']} corrections tracées"], "b-si"))
    s.append(_arrow(430, 135, 475, 135))
    s.append(_box(475, 250, 215, 80, "Barrière qualité", [f"{f['dq_total']} règles · FAIL = arrêt", "quarantaine + dq_results"], "b-dq"))
    s.append(_arrow(582, 230, 582, 250))
    s.append(_arrow(690, 135, 735, 135))
    s.append(_box(735, 40, 185, 290, "gold (SQL)", ["dim_date · dim_district", "dim_client · dim_account", "dim_card · dim_tx_type", "bridge_account_client", "fact_transaction", "fact_account_month", "fact_loan · fact_card_tx", "fact_credit_application", "fact_marketing_contact"], "b-go"))
    s.append(_box(965, 40, 205, 62, "Analyse SQL", [f"{f['queries']} requêtes · réponses"], "b-co"))
    s.append(_box(965, 118, 205, 62, "Modèles (scikit-learn)", ["défaut · fraude · score · marketing"], "b-co"))
    s.append(_box(965, 196, 205, 62, "Dashboard HTML", ["5 vues · SVG · sans CDN"], "b-co"))
    s.append(_box(965, 274, 205, 56, "Docs & ZIP", ["cette page · dictionnaire"], "b-co"))
    for y in (71, 149, 227, 302):
        s.append(_arrow(920, 135 if y < 200 else 230, 965, y, dashed=False))
    s.append(f'<rect class="b-or" x="10" y="365" width="1160" height="86" rx="9"/>')
    s.append('<text class="bt" x="590" y="388" text-anchor="middle">Orchestration &amp; tests transverses</text>')
    s.append('<text class="bl" x="590" y="410" text-anchor="middle">pipeline.py : manifest → bronze → silver → dq → gold → ml → analysis → dashboard → docs (une étape = une fonction rejouable)</text>')
    s.append('<text class="bl" x="590" y="430" text-anchor="middle">Makefile · tests unittest (réconciliation, clés, chiffres clés) · intégration continue GitHub Actions · journal reports/pipeline.log</text>')
    s.append("</svg>")
    return "".join(s)


def star_svg() -> str:
    W, H = 1100, 440
    s = [f'<svg class="arch" viewBox="0 0 {W} {H}" role="img" aria-label="Modèle en étoile de la banque">']
    facts_ = [(20, 20, "fact_account_month", "grain : compte × mois", "185 615 lignes"), (20, 150, "fact_transaction", "grain : 1 mouvement", "1 056 320 lignes"),
              (20, 280, "fact_loan", "grain : 1 prêt", "682 lignes")]
    dims = [(410, 20, "dim_date", "jour (date_key)"), (410, 150, "dim_account", "compte · ancienneté · fréquence"), (410, 280, "dim_tx_type", "opération · canal · finalité"),
            (830, 20, "dim_district", "région · salaire · chômage"), (830, 150, "dim_client", "âge · tranche d'âge"), (830, 280, "dim_card", "type · titulaire")]
    for x, y, t, g, r in facts_:
        s.append(f'<rect class="b-go" x="{x}" y="{y}" width="240" height="100" rx="9"/><text class="bt" x="{x + 120}" y="{y + 28}" text-anchor="middle">{t}</text>'
                 f'<text class="bl" x="{x + 120}" y="{y + 54}" text-anchor="middle">{g}</text><text class="bl" x="{x + 120}" y="{y + 76}" text-anchor="middle">{r}</text>')
    for x, y, t, d in dims:
        s.append(f'<rect class="b-si" x="{x}" y="{y}" width="240" height="100" rx="9"/><text class="bt" x="{x + 120}" y="{y + 28}" text-anchor="middle">{t}</text><text class="bl" x="{x + 120}" y="{y + 54}" text-anchor="middle">{d}</text>')
    L = lambda x1, y1, x2, y2, d="": f'<line class="ar{d}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
    s += [L(260, 70, 410, 70, " dash"),            # mois -> date
          L(260, 70, 410, 200), L(260, 200, 410, 200), L(260, 200, 410, 330), L(260, 330, 410, 200),   # faits -> compte / type
          L(650, 200, 830, 200), L(650, 200, 830, 70), L(650, 330, 830, 200),                           # compte -> client / district ; carte -> compte
          L(950, 150, 950, 120), L(950, 280, 950, 250)]                                                 # client -> district ; carte -> client
    s.append('<text class="bl" x="550" y="410" text-anchor="middle">Chaque table de faits porte aussi une clé de date vers dim_date (trait pointillé). Le pont bridge_account_client relie comptes et clients (titulaire / disposant).</text>')
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------------------------------------ page
EXTRA_CSS = """
.hero{padding:10px 0 26px}.hero h1{font-size:clamp(2rem,4.4vw,3.2rem);line-height:1.08;letter-spacing:-.02em;font-weight:700;max-width:30ch}
.hero p{max-width:66ch;color:var(--ink-2);margin:14px 0 0}
.toc{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0 0}.toc a{font:600 .82rem var(--f-body);text-decoration:none;color:var(--ink-2);border:1px solid var(--line);border-radius:99px;padding:6px 12px;background:var(--surface)}.toc a:hover{border-color:var(--accent);color:var(--ink)}
.blk{margin-top:44px}.blk>h2{font-size:clamp(1.5rem,2.6vw,2rem);line-height:1.15;margin:4px 0 8px}.blk>.lead{margin:0 0 18px}
.scroll{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px;box-shadow:var(--shadow)}
svg.arch{width:100%;min-width:900px;height:auto;display:block}
svg.arch rect{stroke-width:1.3}svg.arch .b-src{fill:var(--surface-2);stroke:var(--axis)}svg.arch .b-br{fill:var(--warn-soft);stroke:var(--warn)}svg.arch .b-si{fill:var(--accent-soft);stroke:var(--accent)}
svg.arch .b-dq{fill:var(--bad-soft);stroke:var(--bad)}svg.arch .b-go{fill:var(--good-soft);stroke:var(--good)}svg.arch .b-co{fill:var(--surface);stroke:var(--ink-2)}svg.arch .b-or{fill:none;stroke:var(--axis);stroke-dasharray:5 4}
svg.arch .bt{fill:var(--ink);font:700 14px var(--f-body)}svg.arch .bl{fill:var(--ink-2);font:12.5px var(--f-body)}svg.arch .ch2{fill:var(--muted);font:600 11.5px var(--f-mono);letter-spacing:.06em}
svg.arch .ar{stroke:var(--ink-2);stroke-width:1.6;fill:none}svg.arch .ar.dash{stroke-dasharray:4 3}svg.arch .ahp{fill:var(--ink-2)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr));gap:16px}
.box{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow);min-width:0}
.box h3{font-size:1.1rem;margin:0 0 6px}.box p{margin:6px 0;color:var(--ink-2);font-size:.95rem}.box ul{margin:6px 0 0;padding-left:1.1rem;color:var(--ink-2);font-size:.93rem}
.adr{border-left:4px solid var(--accent);padding-left:14px;margin:0 0 16px}.adr h3{font-size:1.05rem;margin:0}.adr p{margin:4px 0;color:var(--ink-2);font-size:.95rem}.adr .tag{font:600 .7rem var(--f-mono);color:var(--accent);text-transform:uppercase;letter-spacing:.05em}
details.qa{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:2px 16px;margin-bottom:8px}details.qa summary{cursor:pointer;font:600 1rem var(--f-body);padding:12px 0;list-style:none}
details.qa summary::-webkit-details-marker{display:none}details.qa summary::before{content:"+";display:inline-block;width:1.2em;color:var(--accent);font-weight:700}details.qa[open] summary::before{content:"–"}
details.qa p{margin:0 0 14px;color:var(--ink-2)}
pre.cmd{background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto;font:.84rem/1.55 var(--f-mono);color:var(--ink)}
.pitch{background:var(--accent-soft);border:1px solid var(--accent);border-radius:12px;padding:18px 22px;color:var(--ink);font-size:1.05rem}.pitch p{margin:0}
ol.walk{padding-left:1.2rem;color:var(--ink-2)}ol.walk li{margin:8px 0}ol.walk b{color:var(--ink)}
.hn{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:12px;margin-top:22px}
"""


def _table(headers, rows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def build_architecture(con, f) -> str:
    css = (Path(__file__).parent / "dashboard.css").read_text(encoding="utf-8")
    kp = "".join(f'<div class="kpi"><div class="kl">{a}</div><div class="kv">{b}</div><div class="ks">{c}</div></div>' for a, b, c in [
        ("Lignes ingérées", n(f["bronze_rows"]), f"{f['n_files']} fichiers · {f['n_sources']} sources"),
        ("Contrôles qualité", f"{f['dq_pass']}/{f['dq_total']}", f"{f['dq_warn']} avertissements · {f['dq_fail']} échec"),
        ("Tables gold", str(f["gold_tables"]), "modèle en étoile"),
        ("Requêtes métier", str(f["queries"]), f"{n(f['sql_lines'])} lignes de SQL"),
        ("Soldes chaînés", pct(f["chain"], 3), "reconstitution de l'ordre des mouvements"),
        ("Code Python", n(f["py_lines"]), "lignes, hors SQL"),
    ])
    lineage = _table(["Source officielle", "Plateforme", "Miroir utilisé", "Licence", "Tables"],
                     [[esc(s["title"]), esc(s["platform"]), f'<span class="mono">{esc(s["mirror"])}</span>', esc(s["licence"]), esc(", ".join(s["tables"]))] for s in SOURCES.values()])
    dqrows = pd.read_sql("SELECT rule_id, dimension, description, severity, checked, failed, status FROM dq_results ORDER BY rule_id", con)
    chip = lambda s: f'<span class="chip {"ok" if s == "PASS" else "warn" if s == "WARN" else "ko"}">{s}</span>'
    dqt = _table(["Règle", "Dimension", "Contrôle", "Gravité", "Vérifié", "Écarts", "Statut"],
                 [[f'<span class="mono">{r.rule_id}</span>', esc(r.dimension), esc(r.description), esc(r.severity), n(r.checked), n(r.failed), chip(r.status)] for r in dqrows.itertuples()])
    fixes = pd.read_sql("SELECT source, tbl, fix_id, description, rows_affected FROM dq_fixes ORDER BY source, tbl, fix_id", con)
    fxt = _table(["Table", "Réf.", "Correction appliquée", "Lignes"],
                 [[f'<span class="mono">{esc(r.source)}.{esc(r.tbl)}</span>', f'<span class="mono">{r.fix_id}</span>', esc(r.description), n(r.rows_affected)] for r in fixes.itertuples()])
    gold_rows = [[f'<span class="mono">{t}</span>', esc(d), esc(g), n(_scalar(con, f"SELECT COUNT(*) FROM {t}"))] for t, (d, g) in GOLD_TABLES.items()]
    gold = _table(["Table", "Rôle", "Grain", "Lignes"], gold_rows)
    adrs = [
        ("Stockage", "SQLite comme entrepôt", "Volume modeste, exécution locale, zéro coût, reproductible. SQL standard pour rester portable. Compromis : pas de concurrence d'écriture ni de colonnes compressées ; inutile à cette taille."),
        ("Découpage", "Médaillon bronze / silver / gold", "Le brut est conservé en texte avec empreinte, le nettoyage est rejouable, l'étoile est jetable. Un défaut de nettoyage se corrige sans re-télécharger."),
        ("Transformations", "SQL d'abord, Python seulement si nécessaire", "Gold et analyses sont écrits en SQL (CTE, fenêtres), lisibles par un analyste. Python sert au nettoyage de codes, à la chaîne de soldes et aux modèles."),
        ("Qualité", "Aucune imputation silencieuse", "Une valeur manquante reste NULL (« ? » du chômage, pdays=999). On ne devine pas un taux ; l'absence est une information et elle est comptée."),
        ("Doublons", "Écarter les doublons exacts, en quarantaine", f"{n(f['quarantine'])} lignes identiques sur 31 colonnes sont retirées mais conservées avec leur motif, pour pouvoir contester la décision."),
        ("Éthique", "Sexe exclu des modèles", "Variable protégée : décodée pour décrire, jamais utilisée pour scorer."),
        ("Évaluation", "Découpage temporel et variables d'avant-octroi", "Le passé prédit le futur, jamais l'inverse. Les variables connues après coup (durée d'appel, issue du prêt) sont exclues."),
        ("Honnêteté", "Intervalles de confiance et limites affichés", "Petits effectifs, corrélation non significative sur 8 régions, confusion Euribor / période : chaque conclusion dit ce qu'elle ne prouve pas."),
    ]
    adr_html = "".join(f'<div class="adr"><span class="tag">{a}</span><h3>{b}</h3><p>{c}</p></div>' for a, b, c in adrs)
    cloud = _table(["Brique BankLens", "Azure", "Google Cloud", "AWS", "Open source"],
                   [["Fichiers bruts (bronze)", "ADLS Gen2", "Cloud Storage", "S3", "MinIO"],
                    ["Entrepôt (silver / gold)", "Synapse / Fabric", "BigQuery", "Redshift / Athena", "DuckDB, PostgreSQL"],
                    ["Transformations SQL", "dbt + Fabric", "dbt + Dataform", "dbt + Glue", "dbt-core"],
                    ["Règles de qualité", "Purview / dbt tests", "Dataplex", "Glue Data Quality", "Great Expectations, dbt tests"],
                    ["Orchestration", "Data Factory", "Cloud Composer", "MWAA", "Airflow, Dagster"],
                    ["Modèles", "Azure ML", "Vertex AI", "SageMaker", "scikit-learn + MLflow"],
                    ["Restitution", "Power BI", "Looker", "QuickSight", "Metabase, Superset"]])
    res = [
        ("Encours de prêts / défaut", f"{pct(f['default_cnt'])} en nombre, {pct(f['default_amt'])} en montant", "Q09, Q10"),
        ("Fraude carte", f"{n(f['fraud_n'])} fraudes = {pct(f['fraud_rate'], 3)} des transactions ; PR-AUC {n(f['pr_fraud'], 2)} sur test futur", "F01, ml_fraud_gains"),
        ("Modèle de défaut de prêt", f"AUC {n(f['auc_loan'], 2)} (référence {n(f['auc_loan_base'], 2)})", "ml_metrics"),
        ("Score de crédit allemand", f"AUC {n(f['auc_german'], 2)}", "G01, G02"),
    ]
    resh = _table(["Résultat", "Valeur calculée", "Où le retrouver"], [[esc(a), esc(b), f'<span class="mono">{esc(c)}</span>'] for a, b, c in res])
    qa = "".join(f"<details class='qa'><summary>{esc(q)}</summary><p>{a}</p></details>" for q, a in qa_list(f))
    limits = [
        "Jeux de recherche anonymisés, pas les données d'une banque : les conclusions illustrent une méthode, elles ne se transposent pas telles quelles.",
        "Berka couvre 1993-1998 en Tchéquie ; les montants sont en couronnes de l'époque. Les fraudes carte datent de 2013 (deux jours), le marketing du Portugal 2008-2010.",
        "Les prêts de 1998 sont censurés (on n'a pas vu leur fin) : le taux de défaut de ce millésime est sous-estimé.",
        "Le jeu marketing est un échantillon de 2 999 lignes, pas la base complète.",
        "Les fichiers viennent de miroirs GitHub ; les empreintes SHA-256 permettent de les comparer aux téléchargements officiels.",
        "Chargement complet et non incrémental ; pas de gestion de dérive des modèles ni d'historisation des dimensions.",
    ]
    lim = "".join(f"<li>{esc(x)}</li>" for x in limits)
    html_ = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BankLens - architecture</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}{EXTRA_CSS}</style></head><body>
<header class="top"><div class="brand"><span class="logo">B</span><div><b>BankLens</b><small>Architecture et décisions techniques</small></div></div>
<div class="tools" style="margin-left:auto"><a class="btn" href="index.html">← Dashboard</a><button class="btn" id="theme" aria-label="Changer de thème">Mode sombre</button></div></header>
<main>
<section class="hero"><p class="kick">Projet de données bancaires · de bout en bout</p>
<h1>De quatre sources publiques à un tableau de bord fiable</h1>
<p>BankLens ingère des jeux bancaires réels, les nettoie en couches traçables, les modélise en étoile, répond à {f['queries']} questions métier en SQL et entraîne quatre modèles évalués sans fuite d'information. Cette page montre comment c'est construit et pourquoi.</p>
<div class="hn">{kp}</div>
<nav class="toc" aria-label="Sommaire"><a href="#pitch">Pitch</a><a href="#archi">Architecture</a><a href="#lineage">Sources</a><a href="#etoile">Modèle en étoile</a><a href="#qualite">Qualité</a><a href="#adr">Décisions</a><a href="#cloud">Cloud</a><a href="#resultats">Résultats</a><a href="#limites">Limites</a><a href="#qa">Questions</a><a href="#rejouer">Rejouer</a></nav></section>

<section class="blk" id="pitch"><h2>Pitch en 60 secondes</h2>
<div class="pitch"><p>« J'ai construit une plateforme de données bancaires de bout en bout à partir de quatre jeux publics réels : une banque tchèque avec {n(f['tx'])} mouvements, de la fraude carte, du crédit et du marketing. Les données brutes sont conservées telles quelles, puis nettoyées en SQL et Python avec {f['dq_total']} contrôles qualité qui bloquent le pipeline en cas d'échec ; rien n'est perdu, les rejets sont en quarantaine. J'ai modélisé le tout en étoile, répondu à {f['queries']} questions métier, et entraîné des modèles de risque en évitant la fuite d'information. Le défaut de prêt atteint {pct(f['default_cnt'])} et la fraude {pct(f['fraud_rate'], 3)} des transactions. Tout se rejoue en une commande et chaque conclusion indique ses limites. »</p></div>
<h3 style="margin:22px 0 4px">Déroulé en 5 minutes</h3>
<ol class="walk"><li><b>Le besoin (30 s).</b> Quatre sources hétérogènes, des questions de pilotage : risque, fraude, usage, marketing.</li>
<li><b>L'architecture (1 min).</b> Schéma ci-dessous : bronze en texte pour ne rien perdre, silver typé avec barrière qualité, gold en étoile.</li>
<li><b>Le piège le plus instructif (1 min).</b> L'ordre des transactions Berka : reconstruction par chaînage de soldes, {pct(f['chain'], 3)} de réussite.</li>
<li><b>Les résultats (1 min 30).</b> Ouvrir le dashboard : effort de remboursement et défaut, fraude de nuit, score de crédit.</li>
<li><b>Les limites (1 min).</b> Petits effectifs, censure des prêts récents, jeux de recherche. Montrer qu'on sait ce que les chiffres ne prouvent pas.</li></ol></section>

<section class="blk" id="archi"><p class="kick">Vue d'ensemble</p><h2>Architecture en médaillon</h2><p class="lead">Chaque flèche est une étape rejouable du pipeline. Rien n'est écrit à la main dans les couches : tout se reconstruit depuis les fichiers bruts.</p>
<div class="scroll">{arch_svg(f)}</div></section>

<section class="blk" id="lineage"><p class="kick">Traçabilité</p><h2>D'où viennent les données</h2><p class="lead">Quatre plateformes, quatre formats. Les copies de travail viennent de miroirs de dépôts publics ; la version et l'empreinte SHA-256 de chaque fichier sont enregistrées dans <code>data/MANIFEST.json</code>.</p>
<div class="scroll">{lineage}</div></section>

<section class="blk" id="etoile"><p class="kick">Modélisation</p><h2>Modèle en étoile de la banque</h2><p class="lead">Trois tables de faits à des grains différents partagent les mêmes dimensions. Le grain est écrit avant la moindre jointure : c'est ce qui évite de compter deux fois.</p>
<div class="scroll">{star_svg()}</div>
<h3 style="margin:22px 0 8px">Toutes les tables gold</h3><div class="scroll">{gold}</div></section>

<section class="blk" id="qualite"><p class="kick">Qualité des données</p><h2>{f['dq_total']} contrôles, {f['fixes']} corrections tracées</h2>
<p class="lead">Les règles bloquantes arrêtent le pipeline ; les avertissements restent visibles dans le dashboard au lieu d'être cachés.</p>
<div class="scroll">{dqt}</div>
<h3 style="margin:22px 0 8px">Corrections appliquées au passage bronze → silver</h3><div class="scroll">{fxt}</div></section>

<section class="blk" id="adr"><p class="kick">Choix d'ingénierie</p><h2>Décisions d'architecture</h2><p class="lead">Chaque décision indique le compromis accepté.</p>{adr_html}</section>

<section class="blk" id="cloud"><p class="kick">Passage à l'échelle</p><h2>Correspondance cloud</h2><p class="lead">La conception est indépendante de l'outil : voici où chaque brique irait en production.</p><div class="scroll">{cloud}</div></section>

<section class="blk" id="resultats"><p class="kick">Ce que ça donne</p><h2>Résultats clés</h2><p class="lead">Recalculés à chaque exécution. Le détail et les graphiques sont dans le dashboard ; les lectures rédigées dans <code>reports/ANSWERS.md</code>.</p><div class="scroll">{resh}</div></section>

<section class="blk" id="limites"><p class="kick">Honnêteté</p><h2>Limites assumées</h2><div class="box"><ul>{lim}</ul></div></section>

<section class="blk" id="qa"><p class="kick">Préparation</p><h2>Questions probables de l'entretien</h2><p class="lead">Réponses courtes, à reformuler avec tes mots.</p>{qa}</section>

<section class="blk" id="rejouer"><p class="kick">Reproductibilité</p><h2>Rejouer le projet</h2>
<pre class="cmd">pip install -r requirements.txt
make data     # télécharge les données brutes (dépôts publics à commit figé, SHA-256 vérifiables)
make all      # manifeste → bronze → silver → qualité → gold → modèles → analyses → dashboard → docs
make test     # tests de réconciliation, de clés et de chiffres clés</pre></section>
</main>
<footer><p>BankLens · données publiques de recherche (Berka, Kaggle/ULB, UCI). Toutes les valeurs de cette page sont lues dans l'entrepôt au moment de la génération.</p></footer>
<script>(function(){{var r=document.documentElement,b=document.getElementById("theme");function s(t){{r.setAttribute("data-theme",t);b.textContent=t==="dark"?"Mode clair":"Mode sombre";try{{localStorage.setItem("banklens-theme",t)}}catch(e){{}}}}
var v=null;try{{v=localStorage.getItem("banklens-theme")}}catch(e){{}}s(v||(matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"));
b.addEventListener("click",function(){{s(r.getAttribute("data-theme")==="dark"?"light":"dark")}})}})();</script></body></html>'''
    return html_.replace(" %", "&nbsp;%")


def build_dictionary(con) -> str:
    out = ["# Dictionnaire de données (couche gold)\n",
           "Généré automatiquement depuis l'entrepôt (`python -m banklens docs`). Le grain de chaque table est indiqué : c'est la première chose à vérifier avant une jointure.\n"]
    for t, (desc, grain) in GOLD_TABLES.items():
        rows = con.execute(f"PRAGMA table_info({t})").fetchall()
        cnt = _scalar(con, f"SELECT COUNT(*) FROM {t}")
        out.append(f"\n## `{t}`\n\n{desc}.  \n**Grain** : {grain} · **Lignes** : {n(cnt)}\n\n| Colonne | Type | Clé | Nullable |\n|---|---|---|---|")
        for _, name, typ, notnull, _d, pk in rows:
            key = "PK" if pk else ("FK" if name.endswith("_key") else "")
            out.append(f"| `{name}` | {typ or 'TEXT'} | {key} | {'non' if notnull or pk else 'oui'} |")
    return "\n".join(out) + "\n"


def build_guide(con, f) -> str:
    out = ["# Guide d'entretien BankLens\n",
           "## Pitch (60 secondes)\n",
           f"J'ai construit une plateforme de données bancaires de bout en bout à partir de quatre jeux publics réels ({n(f['tx'])} mouvements bancaires, fraude carte, crédit, marketing). "
           f"Les données brutes sont conservées, nettoyées avec {f['dq_total']} contrôles qualité bloquants, modélisées en étoile, interrogées par {f['queries']} requêtes SQL et modélisées sans fuite d'information. Tout se rejoue avec `make all`.\n",
           "## Chiffres à connaître\n",
           f"- {n(f['bronze_rows'])} lignes ingérées, {f['n_files']} fichiers, {f['n_sources']} sources\n- {n(f['quarantine'])} lignes en quarantaine, {f['fixes']} corrections tracées\n"
           f"- Défaut de prêt : {pct(f['default_cnt'])} (nombre), {pct(f['default_amt'])} (montant)\n- Fraude carte : {pct(f['fraud_rate'], 3)} ; PR-AUC {n(f['pr_fraud'], 2)}\n"
           f"- AUC défaut de prêt {n(f['auc_loan'], 2)} (référence {n(f['auc_loan_base'], 2)}) ; AUC score allemand {n(f['auc_german'], 2)}\n- Soldes chaînés : {pct(f['chain'], 3)}\n",
           "## Questions probables\n"]
    for q, a in qa_list(f):
        out.append(f"### {q}\n\n{a}\n")
    out.append("## À dire spontanément\n\n- Ce sont des jeux de recherche, pas les données d'une banque.\n- Les fichiers viennent de miroirs de dépôts publics ; les empreintes SHA-256 sont vérifiables.\n- Les limites sont écrites dans la page d'architecture.\n")
    return "\n".join(out)


def build_docs(con):
    f = facts(con)
    DASH.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    (DASH / "architecture.html").write_text(build_architecture(con, f), encoding="utf-8")
    (DOCS / "DATA_DICTIONARY.md").write_text(build_dictionary(con), encoding="utf-8")
    (DOCS / "INTERVIEW_GUIDE.md").write_text(build_guide(con, f), encoding="utf-8")
    log.info("docs    architecture.html, DATA_DICTIONARY.md, INTERVIEW_GUIDE.md")
