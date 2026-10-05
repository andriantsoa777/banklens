"""Rédaction des réponses métier à partir des résultats SQL (jamais de chiffre saisi à la main)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def n(x, d=0):
    """Format français : 1 234 567,8"""
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s


def pct(x, d=1):
    return n(x, d) + " %"


def _v(df, col, **where):
    m = pd.Series(True, index=df.index)
    for k, v in where.items():
        m &= df[k] == v
    return df.loc[m, col].iloc[0]


# ======================================================================================= BANQUE
def q01(df):
    g = lambda ind: float(df.loc[df["indicateur"].str.startswith(ind), "valeur"].iloc[0])
    cartes_pct = 100 * g("Cartes émises") / g("Comptes ouverts")
    return dict(
        reponse=f"La banque tient {n(g('Comptes ouverts'))} comptes pour {n(g('Clients'))} personnes, {n(g('Transactions'))} opérations sur six ans, "
                f"et {n(g('Encours'), 1)} M CZK de dépôts au 31/12/1998 (solde moyen {n(g('Solde moyen'))} CZK).",
        lecture=f"Elle a prêté {n(g('Montant total prêté'), 1)} M CZK sur {n(g('Prêts accordés'))} prêts, soit {pct(100 * g('Montant total prêté') / g('Encours'), 0)} de l'encours de dépôts : "
                f"c'est une banque de dépôts qui prête modérément. Seuls {pct(cartes_pct, 0)} des comptes ont une carte.",
        action="Ces chiffres sont le « pied » du dashboard : toute autre analyse doit pouvoir se réconcilier avec eux.")


def q02(df):
    d = df.set_index("year_month")
    dec97, dec98 = d.loc["1997-12", "encours_m"], d.loc["1998-12", "encours_m"]
    last_open = d[d["comptes_ouverts"] == d["comptes_ouverts"].max()].index[0]
    jan = d[d.index.str.endswith("-01") & (d.index >= "1994-01")]
    other = d[~d.index.str.endswith("-01") & (d.index >= "1994-01")]
    return dict(
        reponse=f"Les {n(d['comptes_ouverts'].max())} comptes sont tous ouverts à fin {last_open[:4]} ; en 1998 la croissance vient uniquement des soldes : "
                f"l'encours passe de {n(dec97, 1)} à {n(dec98, 1)} M CZK ({pct(100 * (dec98 / dec97 - 1), 0)}).",
        lecture=f"Chaque mois de janvier affiche un flux net négatif ({n(jan['flux_net_m'].mean(), 1)} M CZK en moyenne contre {n(other['flux_net_m'].mean(), 1)} M les autres mois) : "
                f"les clients vident leur compte en début d'année, puis le rebond de février le reconstitue.",
        action="Anticiper la trésorerie (cash disponible aux guichets) à chaque janvier et décembre, et ne jamais comparer janvier à décembre sans corriger de la saisonnalité.",
        limite="Aucune ouverture de compte après 1997 dans l'extraction : la « croissance » du nombre de comptes ne peut pas être extrapolée à 1998.")


def q03(df):
    tot = df["comptes"].sum()
    fem = (df["pct_femmes"] * df["comptes"]).sum() / tot
    old = df[df["tranche_age"] == "65+"].iloc[0]
    young = df[df["tranche_age"] == "<25"].iloc[0]
    return dict(
        reponse=f"Le portefeuille est équilibré ({pct(fem, 0)} de femmes) et réparti sur toutes les tranches d'âge, mais l'équipement varie fortement : "
                f"les 65 ans et plus ({n(old['comptes'])} comptes) n'ont que {pct(old['pct_avec_carte'])} de cartes et {pct(old['pct_avec_pret'])} de prêts, contre {pct(young['pct_avec_carte'])} de cartes chez les moins de 25 ans.",
        lecture=f"Le solde moyen est stable en dessous de 65 ans ({n(df[df['tranche_age'] != '65+']['solde_moyen_1998'].min())} à {n(df[df['tranche_age'] != '65+']['solde_moyen_1998'].max())} CZK) puis chute à {n(old['solde_moyen_1998'])} CZK chez les 65 ans et plus : clients peu équipés, aux soldes bas.",
        action="Deux leviers distincts : l'équipement des seniors (cartes) et le crédit, aujourd'hui concentré sur les 25-54 ans.",
        limite="L'âge est calculé au 31/12/1998 et l'équipement est observé à cette date, pas à l'ouverture du compte.")


def q04(df):
    corr = float(np.corrcoef(df["solde_moyen"], df["salaire_moyen_district"])[0, 1])
    top2 = df.nlargest(2, "comptes")
    spread_bal = 100 * (df["solde_moyen"].max() / df["solde_moyen"].min() - 1)
    spread_sal = 100 * (df["salaire_moyen_district"].max() / df["salaire_moyen_district"].min() - 1)
    prague = df[df["region"] == "prague"].iloc[0]
    sal_gap = 100 * (prague["salaire_moyen_district"] / df["salaire_moyen_district"].mean() - 1)
    return dict(
        reponse=f"{top2.iloc[0]['region'].title()} et {top2.iloc[1]['region'].title()} concentrent {pct(top2['part_comptes_pct'].sum(), 0)} des comptes. "
                f"Le solde moyen varie de seulement {pct(spread_bal, 0)} d'une région à l'autre ({n(df['solde_moyen'].min())} à {n(df['solde_moyen'].max())} CZK) alors que le salaire moyen varie de {pct(spread_sal, 0)}.",
        lecture=f"La corrélation région par région entre salaire local et solde moyen est de {n(corr, 2)}, mais avec 8 régions elle n'est pas significative au seuil de 5 % (il faudrait au moins 0,71) et l'effet reste faible : "
                f"Prague a un salaire {pct(sal_gap, 0)} au-dessus de la moyenne des régions pour un solde moyen de {n(prague['solde_moyen'])} CZK, quasi identique aux autres.",
        action="Ne pas segmenter l'offre d'épargne par région : le comportement de dépôt est homogène. Réserver la segmentation géographique au risque de crédit (chômage) et à l'implantation.",
        limite="8 régions seulement : une corrélation sur 8 points est indicative, pas démonstrative ; le salaire est celui du district, pas celui du client.")


def q05(df):
    sh = lambda canal, col: df.loc[df["canal"] == canal, col].sum()
    return dict(
        reponse=f"Les espèces au guichet pèsent {pct(sh('Espèces (guichet)', 'part_operations_pct'), 0)} des opérations et {pct(sh('Espèces (guichet)', 'part_montant_pct'), 0)} des montants ; "
                f"les virements {pct(sh('Virement', 'part_operations_pct'), 0)} des opérations et {pct(sh('Virement', 'part_montant_pct'), 0)} des montants ; la carte {pct(sh('Carte', 'part_operations_pct'))} des opérations.",
        lecture="La banque fonctionne en 1993-1998 comme une banque de guichet : l'argent entre en espèces et ressort en espèces. "
                "Les frais et intérêts (« Interne ») représentent un tiers du nombre d'opérations pour moins de 1 % des montants : ils gonflent les volumes sans refléter l'activité des clients.",
        action="Pour mesurer l'activité client, exclure les opérations internes ; pour dimensionner l'infrastructure, les compter.",
        limite="Dans la source, « retrait » (VYBER) désigne aussi les frais de relevé : le canal est reconstruit à partir du motif, pas du libellé brut.")


def q06(df):
    tot = df["comptes"].sum()
    inactive = df[~df["statut"].str.startswith("Actif")]["comptes"].sum()
    return dict(
        reponse=f"{n(inactive)} comptes seulement ({pct(100 * inactive / tot, 1)}) n'ont plus d'opération depuis juillet 1998.",
        lecture="Une attrition aussi faible est suspecte : l'extraction ne contient très probablement que des comptes restés ouverts (biais du survivant). "
                "Elle ne permet donc pas de mesurer le churn réel.",
        action="Avant tout modèle d'attrition, demander à la source si les comptes clôturés ont été exclus ; sinon, ne pas conclure que la banque fidélise bien.",
        limite="Le critère « dormant » (aucune opération depuis juillet 1998) est arbitraire : à calibrer avec le métier.")


def q07(df):
    never = _v(df, "part_pct", profil="0-jamais à découvert")
    chronic = df[df["profil"].str.startswith("3")].iloc[0]
    rec = df[df["profil"].str.startswith("2")].iloc[0]
    base = _v(df, "pct_avec_pret", profil="0-jamais à découvert")
    n_od = int(df[~df["profil"].str.startswith("0")]["comptes"].sum())
    return dict(
        reponse=f"{pct(never)} des comptes ne passent jamais en négatif ; {n(n_od)} comptes ({pct(100 - never)}) ont connu au moins un mois de découvert, dont {n(chronic['comptes'])} de façon chronique (7 mois ou plus, pire solde moyen {n(chronic['pire_solde_moyen'])} CZK).",
        lecture=f"Les découverts récurrents sont liés au crédit : {pct(rec['pct_avec_pret'], 0)} des comptes à découvert récurrent ont aussi un prêt, contre {pct(base, 0)} des comptes sans découvert. "
                f"Le découvert répété accompagne la prise de crédit : c'est un signal de tension financière, pas un simple incident (association observée, pas un lien de cause à effet).",
        action="Mettre une alerte « 3 mois de découvert sur 12 » dans le suivi du risque, avant toute nouvelle autorisation de crédit.",
        limite="Découvert mesuré sur le solde après chaque opération (minimum du mois), pas sur le solde de fin de journée.")


def q08(df):
    none = df[df["carte"] == "none"].iloc[0]
    with_c = df[df["carte"] != "none"]
    equip = 100 - none["part_comptes_pct"]
    return dict(
        reponse=f"{pct(equip, 0)} des comptes ont une carte, mais ils l'utilisent très peu : {n(with_c['retraits_carte_par_mois'].mean(), 2)} retrait par carte par mois en moyenne.",
        lecture=f"Les détenteurs de carte ne vont pas moins au guichet ({n(with_c['passages_guichet_par_mois'].mean(), 2)} passages par mois contre {n(none['passages_guichet_par_mois'], 2)} sans carte) : "
                f"la carte s'ajoute aux habitudes, elle ne les remplace pas.",
        action="Si la banque veut désengorger les guichets, l'équipement ne suffit pas ; il faut activer l'usage (retraits gratuits, distributeurs, communication).",
        limite="Une corrélation (les clients à carte sont aussi les plus actifs) n'est pas un effet causal de la carte.")


def q09(df):
    bad = df[df["statut"].isin(["B", "D"])]
    nb, tot = int(bad["prets"].sum()), int(df["prets"].sum())
    amt_bad, amt = bad["montant_m"].sum(), df["montant_m"].sum()
    return dict(
        reponse=f"{n(nb)} prêts sur {n(tot)} sont en défaut (terminés non remboursés ou en impayé) : {pct(100 * nb / tot)} en nombre mais {pct(100 * amt_bad / amt)} en montant ({n(amt_bad, 1)} M CZK sur {n(amt, 1)}).",
        lecture=f"Les prêts en défaut sont plus gros que la moyenne (D : {n(_v(df, 'montant_moyen', statut='D'))} CZK contre {n(_v(df, 'montant_moyen', statut='A'))} CZK pour A) : "
                f"la perte en valeur est supérieure à la perte en nombre. Le risque se concentre sur les gros dossiers.",
        action="Piloter le risque en montant (exposition) et pas seulement en nombre de dossiers.",
        limite="B + D = défaut est une convention de lecture du statut Berka (D = en cours mais impayé) ; aucune perte réelle ni récupération n'est observée.")


def q10(df):
    amt = df[df["dimension"] == "Montant"].set_index("modalite")["taux_defaut_pct"]
    dur = df[df["dimension"] == "Durée"].set_index("modalite")["taux_defaut_pct"]
    age = df[df["dimension"] == "Âge"]
    return dict(
        reponse=f"Le montant est le facteur dominant : {pct(amt['200k+'])} de défaut au-dessus de 200 k CZK contre {pct(amt['<50k'])} sous 50 k ({n(amt['200k+'] / amt['<50k'], 1)} fois plus).",
        lecture=f"La durée compte peu au-delà d'un an ({pct(dur['12 mois'])} à 12 mois, puis de {pct(dur.drop('12 mois').min())} à {pct(dur.drop('12 mois').max())} ensuite) ; le chômage local et l'âge produisent des écarts modestes "
                f"(âge : de {pct(age['taux_defaut_pct'].min())} à {pct(age['taux_defaut_pct'].max())}). Avec {n(age['prets'].min())} à {n(age['prets'].max())} prêts par tranche, un écart de 4 points est dans le bruit statistique (± 5 points).",
        action="Plafonner l'exposition unitaire ou exiger des garanties au-delà de 200 k CZK. Ne pas surinterpréter les tranches d'âge.",
        limite="Analyse univariée : le montant est corrélé à la durée et au revenu ; le modèle multivarié (module ML) démêle ces effets.")


def q11(df):
    d = df.set_index("annee_octroi")
    return dict(
        reponse=f"Les prêts de 1998 affichent seulement {pct(d.loc[1998, 'taux_defaut_pct'])} de défaut contre {pct(100 * d.loc[1994:1997, 'defauts'].sum() / d.loc[1994:1997, 'prets'].sum(), 0)} pour l'ensemble 1994-1997.",
        lecture=f"Ce n'est PAS une amélioration : {pct(d.loc[1998, 'pct_encore_en_cours'], 0)} des prêts de 1998 sont encore en cours, ils n'ont pas eu le temps de faire défaut (censure à droite). "
                f"La comparaison valide se fait à âge de prêt égal, pas à date de calendrier.",
        action="Ne jamais présenter le taux de défaut brut d'un millésime récent sans préciser son âge ; produire des courbes de défaut par mois depuis l'octroi.",
        limite="Les données n'ont pas la date du défaut : la courbe par âge de prêt n'est pas reconstructible ici.")


def q12(df):
    low, high = df.iloc[0], df.iloc[-1]
    risky = df[df["taux_effort"].str.startswith(("3", "4"))]
    share_def = 100 * risky["defauts"].sum() / df["defauts"].sum()
    share_n = 100 * risky["prets"].sum() / df["prets"].sum()
    return dict(
        reponse=f"Le taux d'effort (mensualité / entrées mensuelles moyennes des 6 mois précédents) sépare très bien les dossiers : {pct(low['taux_defaut_pct'])} de défaut sous 10 %, {pct(high['taux_defaut_pct'])} au-delà de 35 % ({n(high['taux_defaut_pct'] / low['taux_defaut_pct'], 1)} fois plus).",
        lecture=f"Les {pct(share_n, 0)} de prêts à taux d'effort supérieur à 20 % concentrent {pct(share_def, 0)} des défauts. Le solde moyen avant octroi tombe de {n(low['solde_moyen_avant'])} à {n(high['solde_moyen_avant'])} CZK, "
                f"et les mois de découvert passent de {n(low['mois_decouvert_avant'], 2)} à {n(high['mois_decouvert_avant'], 2)} par dossier. Tout est calculé avec des données antérieures à l'octroi : le signal est donc exploitable en production.",
        action="Règle simple immédiate : revue manuelle obligatoire au-delà de 20 % de taux d'effort ; le score statistique (module ML) affine ensuite.",
        limite="Les entrées du compte sous-estiment le revenu des clients qui sont payés sur un autre compte.")


def q13(df):
    d = df.set_index("annee")
    ratio = d.loc[1998, "interets_verses_k"] / d.loc[1998, "frais_releve_k"]
    pen = d.loc[1998, "interets_penalite_k"] / max(d.loc[1997, "interets_penalite_k"], 1)
    return dict(
        reponse=f"En 1998 les frais de relevé rapportent {n(d.loc[1998, 'frais_releve_k'])} k CZK et les pénalités de découvert {n(d.loc[1998, 'interets_penalite_k'])} k, "
                f"alors que la banque verse {n(d.loc[1998, 'interets_verses_k'])} k CZK d'intérêts aux déposants ({n(ratio, 1)} fois plus), à un taux implicite stable d'environ {n(d['taux_servi_implicite_pct'].iloc[1:].mean(), 1)} %.",
        lecture=f"Les pénalités de découvert ont été multipliées par {n(pen, 1)} entre 1997 et 1998 : recette en hausse, mais aussi signe de tension croissante des clients (cf. Q07).",
        action="Ne pas conclure à la rentabilité à partir de ces seuls flux : le revenu d'intermédiation (prêts - dépôts) manque.",
        limite="Les mensualités de prêt valent exactement capital / durée : aucun intérêt de prêt n'est enregistré. Marge, coût du risque et refinancement ne sont pas calculables. Périmètre partiel assumé.")


def q14(df):
    top10 = df[df["segment_riche"].isin(["a-1 % des comptes", "b-10 % des comptes"])]["part_encours_pct"].sum()
    return dict(
        reponse=f"Les 10 % de comptes les plus riches détiennent {pct(top10, 0)} des dépôts ; le 1 % du haut seulement {pct(_v(df, 'part_encours_pct', segment_riche='a-1 % des comptes'))}.",
        lecture="Concentration faible : portefeuille de détail, sans gros dépôts dont le départ menacerait la liquidité.",
        action="Risque de concentration des dépôts : faible. Pas de politique « grands comptes » à prévoir.",
        limite="Soldes comptés par compte ; un client à plusieurs comptes n'est pas regroupé (le jeu en a peu : un titulaire par compte).")


def q15(df):
    s12 = df["solde_moyen_12m"].dropna()
    return dict(
        reponse=f"Toutes les cohortes se ressemblent : solde moyen à 12 mois de {n(s12.min())} à {n(s12.max())} CZK et environ {n(df['tx_mois_12m'].mean(), 1)} opérations par mois.",
        lecture="Le solde progresse de quelques milliers de CZK entre 12 et 24 mois mais l'activité reste plate : les clients gardent leurs habitudes dès la première année. Pas d'effet millésime.",
        action="Le comportement observé à 12 mois est déjà celui des 24 mois : inutile d'attendre deux ans pour juger un compte.",
        limite="La cohorte 1997 n'a pas 24 mois d'historique (NaN attendu).")


def q16(df):
    d = df.set_index("mois")
    jan, feb = d.loc[1, "operations"], d.loc[2, "operations"]
    return dict(
        reponse=f"Janvier concentre {n(jan)} opérations en 1994-1997, soit {n(jan / feb, 1)} fois février ; décembre est le deuxième pic (indice {n(d.loc[12, 'indice_activite_100'], 0)}, base 100 = mois moyen).",
        lecture=f"Les retraits au guichet expliquent le pic : {pct(d.loc[1, 'part_retraits_pct'], 0)} des opérations de janvier contre {pct(d.drop([1, 12])['part_retraits_pct'].mean(), 0)} les mois ordinaires, "
                f"pour {n(d.loc[1, 'sorties_m'], 0)} M CZK de sorties contre {n(d.loc[2, 'sorties_m'], 0)} M en février. Hypothèse à confirmer avec le métier : besoins de trésorerie de fin d'année (fêtes, charges annuelles).",
        action="Renforcer les liquidités en agence en décembre-janvier ; ne pas déclencher d'alerte « retraits anormaux » en janvier sans neutraliser la saisonnalité.",
        limite="Quatre années pleines seulement ; l'hypothèse n'est pas démontrée par ces données.")


def q17(df):
    prem = df[df["segment"].str.startswith("1")].iloc[0]
    watch = df[df["segment"].str.startswith("5")].iloc[0]
    tot_enc = df["encours_m"].sum()
    return dict(
        reponse=f"{len(df)} segments : {pct(prem['part_comptes_pct'], 0)} de comptes Premium détiennent {pct(100 * prem['encours_m'] / tot_enc, 0)} de l'encours ; {n(watch['comptes'])} comptes ({pct(watch['part_comptes_pct'])}) sont à surveiller (découvert récurrent).",
        lecture=f"Les règles sont volontairement lisibles par un directeur d'agence : seuil de solde, âge, fréquence d'opérations, découverts. "
                f"Le segment « Actifs » est celui où le crédit est le plus présent ({pct(df[df['segment'].str.startswith('2')]['pct_avec_pret'].iloc[0], 0)} ont un prêt contre {pct(df[df['segment'].str.startswith('3')]['pct_avec_pret'].iloc[0], 0)} des « Courants ») : "
                f"une partie de leur activité vient des remboursements, pas d'une intensité d'usage à valoriser commercialement.",
        action="Premium : offre d'épargne rémunérée. Seniors : conseil et sécurité. À surveiller : appel proactif avant un incident de remboursement.",
        limite="Segmentation à règles, pas un clustering statistique ; les seuils (80 k, 25 opérations, 3 mois) sont des choix métier révisables.")


def q18(df):
    sipo = df[df["objet"].str.startswith("Loyer")].iloc[0]
    lo = df[df["objet"] == "Remboursement de prêt"].iloc[0]
    return dict(
        reponse=f"{pct(sipo['pct_des_comptes'], 0)} des comptes confient à la banque un ordre permanent de charges ({n(sipo['total_mensuel_m'], 1)} M CZK par mois), loin devant l'assurance ({pct(df[df['objet']=='Assurance']['pct_des_comptes'].iloc[0], 0)}) et le leasing.",
        lecture=f"Ces comptes sont « ancrés » : un prélèvement automatique rend le changement de banque pénible. {n(lo['ordres'])} ordres de remboursement existent alors que le fichier ne contient que 682 prêts : "
                f"35 ordres correspondent à des prêts absents du fichier (cf. règle qualité K07).",
        action=f"Cibler la vente d'assurance (seulement {pct(df[df['objet']=='Assurance']['pct_des_comptes'].iloc[0])} des comptes) aux comptes ayant déjà des charges prélevées.",
        limite="Le montant d'un ordre est un montant mensuel déclaré, pas un flux observé.")


# ======================================================================================= FRAUDE
def f01(df):
    f, l = df[df["classe"] == "Fraude"].iloc[0], df[df["classe"] == "Légitime"].iloc[0]
    return dict(
        reponse=f"{n(f['transactions'])} fraudes sur {n(f['transactions'] + l['transactions'])} transactions : {pct(f['part_transactions_pct'], 3)}, soit 1 transaction sur {n(100 / f['part_transactions_pct'], 0)}. "
                f"Le montant moyen d'une fraude ({n(f['montant_moyen'], 0)}) dépasse celui d'une transaction légitime ({n(l['montant_moyen'], 0)}).",
        lecture=f"En valeur, la fraude ne pèse que {pct(f['part_montant_pct'], 3)} des montants : le sujet n'est pas le coût direct mais le tri. "
                f"Avec un tel déséquilibre, un modèle « tout est légitime » aurait {pct(l['part_transactions_pct'], 2)} d'exactitude : l'exactitude est une métrique inutile ici.",
        action="Évaluer tout modèle avec la précision-rappel (PR-AUC) et en euros, jamais avec l'exactitude.",
        limite="492 fraudes dans le jeu public, 473 après suppression des 19 doublons exacts : ce choix est tracé en quarantaine (règle F01).")


def f02(df):
    night, day = df[df["heure"] <= 5], df[df["heure"] > 5]
    share_f = 100 * night["fraudes"].sum() / df["fraudes"].sum()
    share_t = 100 * night["transactions"].sum() / df["transactions"].sum()
    top = df.loc[df["fraudes_pour_10000"].idxmax()]
    base = 10000 * df["fraudes"].sum() / df["transactions"].sum()
    f_night, f_day = night["fraudes"].sum() / len(night), day["fraudes"].sum() / len(day)
    return dict(
        reponse=f"La nuit (0 h à 5 h) concentre {pct(share_f, 0)} des fraudes pour {pct(share_t, 0)} des transactions. Le pire créneau est {int(top['heure'])} h : {n(top['fraudes_pour_10000'], 0)} fraudes pour 10 000 transactions, soit {n(top['fraudes_pour_10000'] / base, 0)} fois la moyenne ({n(base, 1)}).",
        lecture=f"En nombre absolu, la fraude est aussi fréquente la nuit que le jour ({n(f_night, 0)} fraudes par heure de nuit contre {n(f_day, 0)} de jour) alors que le volume légitime est bien plus faible la nuit : "
                f"la proportion de fraude explose donc mécaniquement. Hypothèse : les fraudeurs n'ont pas de rythme jour/nuit du pays des porteurs de cartes.",
        action=f"Durcir les règles (authentification forte, plafonds) sur la fenêtre 0 h - 5 h plutôt que sur toute la journée : l'impact sur les clients légitimes est limité ({pct(share_t, 0)} du volume).",
        limite="Heure relative au début du jeu sur 48 h, pas à un fuseau horaire ; émetteurs européens, sept. 2013.")


def f03(df):
    zero = df[df["tranche_montant"] == "0"].iloc[0]
    small = df[df["tranche_montant"].isin(["0", "<1", "1-10"])]
    big = df[df["tranche_montant"].isin(["500-1000", "1000+"])]
    return dict(
        reponse=f"Les transactions à montant nul ont {n(zero['fraudes_pour_10000'], 0)} fraudes pour 10 000, soit {n(zero['fraudes_pour_10000'] / (10000 * df['fraudes'].sum() / df['transactions'].sum()), 0)} fois la moyenne ; "
                f"{pct(small['part_des_fraudes_pct'].sum(), 0)} des fraudes concernent des montants de moins de 10, contre {pct(small['part_des_legitimes_pct'].sum(), 0)} des transactions légitimes.",
        lecture=f"Compatible avec le « card testing » (hypothèse) : le fraudeur valide la carte volée avec un micro-montant, puis la vide. Les montants de 500 et plus sont {n(big['part_des_fraudes_pct'].sum() / big['part_des_legitimes_pct'].sum(), 1)} fois plus fréquents parmi les fraudes que parmi les légitimes.",
        action="Surveiller les séries de micro-transactions (< 1) sur une même carte : c'est un signal précoce, avant la grosse fraude.",
        limite="Aucun identifiant de carte dans le jeu : on ne peut pas reconstituer les séries par carte, seulement la distribution des montants.")


def f04(df):
    top = df.head(4)
    return dict(
        reponse=f"Quatre composantes séparent nettement fraude et légitime : {', '.join(top['variable'])} (écarts de {n(top['ecart_standardise'].abs().min(), 1)} à {n(top['ecart_standardise'].abs().max(), 1)} écarts-types).",
        lecture="Les variables sont une ACP anonymisée par la source : on ne peut pas dire ce qu'elles « signifient » (c'est volontaire, confidentialité), seulement qu'elles portent le signal. "
                "Un écart de plus de 5 écarts-types est exceptionnel : peu de variables suffisent à séparer l'essentiel.",
        action="Pour le modèle (module ML), garder toutes les composantes ; pour l'explicabilité, présenter ces quatre-là.",
        limite="Séparation univariée : les composantes sont décorrélées par construction (ACP), donc leurs effets s'additionnent.")


# ======================================================================================= CRÉDIT
def g01(df):
    chk = df[df["variable"] == "Compte courant"].set_index("modalite")["taux_defaut_pct"]
    dur = df[df["variable"] == "Durée"].set_index("modalite")["taux_defaut_pct"]
    hist = df[df["variable"] == "Historique de crédit"].set_index("modalite")["taux_defaut_pct"]
    return dict(
        reponse=f"Le défaut global est de {pct(100 * df[df['variable'] == 'Compte courant']['defauts'].sum() / df[df['variable'] == 'Compte courant']['dossiers'].sum(), 0)}. Il atteint {pct(chk['< 0 DM'])} pour les comptes courants à découvert contre {pct(chk['unknown'])} pour les clients sans compte courant connu, et {pct(dur['37+ mois'])} pour les crédits de plus de 36 mois contre {pct(dur['<=12 mois'])} à 12 mois ou moins.",
        lecture=f"Résultat contre-intuitif à expliquer : l'historique « critique » a un taux de défaut de {pct(hist['critical'])} (le plus bas) alors que « entièrement remboursé » monte à {pct(hist['fully repaid'])}. "
                f"C'est un biais de sélection : on n'observe que des clients à qui la banque a accordé un crédit ; hypothèse : ceux qui ont un passé difficile n'ont été acceptés qu'après un examen très sévère.",
        action="Ne jamais « lire » un coefficient de scoring comme une cause : le modèle apprend la politique d'octroi passée (problème de l'inférence des refusés).",
        limite="1 000 dossiers d'un seul établissement allemand (années 1970-90) : valeurs non transposables, méthode oui.")


def g02(df):
    top = df.iloc[0]
    strong = df[df["information_value"] >= 0.1]["variable"].tolist()
    return dict(
        reponse=f"« {top['variable']} » domine avec une IV de {n(top['information_value'], 2)} ; {len(strong)} variables ont une IV supérieure à 0,1 ({', '.join(strong)}).",
        lecture=f"Une IV supérieure à 0,5 est normalement un signal d'alarme (fuite possible) ; ici elle s'explique : le statut du compte courant est une information bancaire déjà connue au moment de la demande. "
                f"Les variables sociodémographiques (âge, logement, emploi) pèsent peu (IV < 0,1) : le comportement bancaire passé prime sur le profil.",
        action="Construire le scorecard en priorité sur compte courant, historique, épargne, durée et objet du crédit.",
        limite="IV calculée sur l'échantillon complet (sans hors-échantillon) : elle surestime légèrement ; le modèle ML est validé en validation croisée.")


# ======================================================================================= MARKETING
def m01(df):
    g = df[df["dimension"] == "Global"].iloc[0]
    prev = df[df["dimension"] == "Campagne précédente"].set_index("modalite")["taux_conversion_pct"]
    ch = df[df["dimension"] == "Canal"].set_index("modalite")["taux_conversion_pct"]
    return dict(
        reponse=f"Le taux de conversion global est de {pct(g['taux_conversion_pct'])}. Il atteint {pct(prev['success'])} chez les clients déjà convertis à une campagne précédente (contre {pct(prev['nonexistent'])} sans historique) et {pct(ch['cellular'])} sur mobile contre {pct(ch['telephone'])} sur fixe.",
        lecture="Le meilleur prédicteur d'une souscription est une souscription passée ; le mobile convertit 2,5 fois mieux que le fixe (raison à investiguer : profil des clients joints ou période de la campagne). Retraités, étudiants et plus de 60 ans convertissent le plus, les indépendants le moins.",
        action="Prioriser dans les listes d'appel : 1) anciens souscripteurs, 2) contacts mobiles, 3) seniors. Tester avant de généraliser la préférence pour le mobile.",
        limite="Échantillon de 2 999 contacts (7 % du jeu complet) : les modalités à moins de 100 contacts ne sont pas fiables ; le canal et la période sont confondus.")


def m02(df):
    d = df.set_index("pression")["taux_conversion_pct"]
    return dict(
        reponse=f"Le rendement s'effondre avec l'insistance : {pct(d['1 contact'])} au premier appel, {pct(d['2-3 contacts'])} à 2-3 appels, {pct(d['4-6 contacts'])} à 4-6, {pct(d['7+ contacts'])} au-delà de 6.",
        lecture=f"Au-delà de 6 appels le rendement est divisé par {n(d['1 contact'] / d['7+ contacts'], 1)} par rapport au premier appel, alors que chaque appel coûte le même temps de conseiller ; risque de réclamation en plus.",
        action="Plafonner à 3 appels par contact dans la campagne et réaffecter le temps des conseillers vers de nouveaux contacts.",
        limite="Les contacts très sollicités ne sont pas tirés au hasard (sélection : on réappelle ceux qui n'ont pas dit non d'emblée).")


def m03(df):
    d = df.set_index("contexte_taux")["taux_conversion_pct"]
    lo, hi = d.iloc[0], d.iloc[-1]
    return dict(
        reponse=f"Quand l'Euribor 3 mois est sous 1 %, {pct(lo, 0)} des contacts souscrivent ; au-dessus de 3 %, seulement {pct(hi)} ({n(lo / hi, 1)} fois moins).",
        lecture="Le sens est contre-intuitif (taux bas = plus de souscriptions). Euribor et date de campagne sont confondus : la variable capte surtout la période (2009-2010, crise financière, fuite vers les placements sûrs) ; on ne peut pas parler d'effet causal du taux. Le contexte pèse néanmoins plus que n'importe quelle caractéristique du client.",
        action="Piloter la campagne par le calendrier de taux (lancer quand le contexte est favorable) et corriger les comparaisons de performance entre périodes par le niveau de l'Euribor.",
        limite="Variable macroéconomique commune à tous les contacts d'une période : elle ne distingue pas les clients entre eux.")


def m04(df):
    d = df.set_index("duree_appel")["taux_conversion_pct"]
    return dict(
        reponse=f"La conversion grimpe de {pct(d.iloc[0], 0)} (appel de moins d'une minute) à {pct(d.iloc[-1], 0)} (appels de plus de 7 minutes) : la durée semble être le meilleur prédicteur.",
        lecture="C'est un piège : la durée n'est connue qu'à la fin de l'appel, donc il est impossible de s'en servir pour choisir qui appeler. Un client qui souscrit reste logiquement plus longtemps en ligne (cause inversée). "
                "Le module ML montre l'AUC qui monte à 0,93 avec la durée (irréaliste) contre 0,75 sans (utilisable).",
        action="Exclure la durée de tout modèle de ciblage ; l'utiliser seulement pour évaluer la qualité des appels a posteriori.",
        limite="Même la source UCI recommande d'écarter cette variable pour un modèle prédictif réaliste.")


ANSWERS = {"Q01": q01, "Q02": q02, "Q03": q03, "Q04": q04, "Q05": q05, "Q06": q06, "Q07": q07, "Q08": q08, "Q09": q09,
           "Q10": q10, "Q11": q11, "Q12": q12, "Q13": q13, "Q14": q14, "Q15": q15, "Q16": q16, "Q17": q17, "Q18": q18,
           "F01": f01, "F02": f02, "F03": f03, "F04": f04, "G01": g01, "G02": g02,
           "M01": m01, "M02": m02, "M03": m03, "M04": m04}
