# Réponses aux questions métier

Toutes les valeurs ci-dessous sont **calculées par le pipeline** (SQL dans `sql/analysis/`) : aucune n'est saisie à la main.

## Banque de détail (Berka)

### Q01 — Les chiffres clés de la banque

**Question.** Quelle est la taille de la banque en décembre 1998 : combien de comptes, de clients, de transactions, quel encours ?

**Réponse.** La banque tient 4 500 comptes pour 5 369 personnes, 1 056 320 opérations sur six ans, et 197,2 M CZK de dépôts au 31/12/1998 (solde moyen 43 811 CZK).

| indicateur | valeur | unite |
|---|---|---|
| Comptes ouverts | 4 500 | comptes |
| Clients (titulaires + disposants) | 5 369 | personnes |
| Transactions enregistrées | 1 056 320 | opérations |
| Encours de dépôts au 31/12/1998 | 197.2 | M CZK |
| Solde moyen par compte au 31/12/1998 | 43 811 | CZK |
| Prêts accordés | 682 | prêts |
| Montant total prêté | 103.3 | M CZK |
| Cartes émises | 892 | cartes |
| Districts couverts | 77 | districts |

**Lecture.** Elle a prêté 103,3 M CZK sur 682 prêts, soit 52 % de l'encours de dépôts : c'est une banque de dépôts qui prête modérément. Seuls 20 % des comptes ont une carte.

**Décision / action.** Ces chiffres sont le « pied » du dashboard : toute autre analyse doit pouvoir se réconcilier avec eux.

### Q02 — Évolution mensuelle de l'activité et des dépôts

**Question.** La banque grossit-elle ? Comment évoluent le nombre de comptes actifs, les flux et l'encours de dépôts mois après mois ?

**Réponse.** Les 4 500 comptes sont tous ouverts à fin 1997 ; en 1998 la croissance vient uniquement des soldes : l'encours passe de 170,0 à 197,2 M CZK (16 %).

| year_month | comptes_ouverts | comptes_actifs | transactions | entrees_m | sorties_m | flux_net_m | encours_m |
|---|---|---|---|---|---|---|---|
| 1993-01 | 96 | 96 | 177 | 0.67 | 0.03 | 0.63 | 0.6 |
| 1993-02 | 194 | 194 | 395 | 2.45 | 0.28 | 2.16 | 2.8 |
| 1993-03 | 298 | 298 | 676 | 3.86 | 0.87 | 2.98 | 5.8 |
| 1993-04 | 375 | 375 | 913 | 5.33 | 2.05 | 3.27 | 9.1 |
| 1993-05 | 466 | 466 | 1 306 | 7.66 | 4.02 | 3.65 | 12.7 |
| 1993-06 | 554 | 553 | 1 880 | 10.77 | 7.52 | 3.25 | 15.9 |
| 1993-07 | 653 | 652 | 2 399 | 10.64 | 7.38 | 3.25 | 19.2 |
| 1993-08 | 755 | 754 | 2 938 | 11.96 | 9.07 | 2.89 | 22.1 |
| 1993-09 | 858 | 858 | 3 441 | 13.52 | 9.92 | 3.59 | 25.7 |
| 1993-10 | 933 | 933 | 3 989 | 15.48 | 12.09 | 3.4 | 29.1 |
| 1993-11 | 1 048 | 1 047 | 4 422 | 15.61 | 12.91 | 2.7 | 31.8 |
| 1993-12 | 1 139 | 1 138 | 5 669 | 22.51 | 17.7 | 4.8 | 36.6 |
| 1994-01 | 1 163 | 1 163 | 9 139 | 18.62 | 23.97 | -5.36 | 31.2 |
| 1994-02 | 1 197 | 1 194 | 5 601 | 18.39 | 12.9 | 5.49 | 36.7 |
| 1994-03 | 1 229 | 1 229 | 6 255 | 19.92 | 17.46 | 2.47 | 39.2 |
| 1994-04 | 1 270 | 1 270 | 6 549 | 19.79 | 17.7 | 2.08 | 41.3 |
| 1994-05 | 1 325 | 1 323 | 7 059 | 21.61 | 20.13 | 1.48 | 42.7 |
| 1994-06 | 1 360 | 1 360 | 7 916 | 29.52 | 30.16 | -0.64 | 42.1 |
| 1994-07 | 1 391 | 1 390 | 7 398 | 22.29 | 20.18 | 2.11 | 44.2 |
| 1994-08 | 1 428 | 1 427 | 7 600 | 22.83 | 20.74 | 2.09 | 46.3 |
| 1994-09 | 1 468 | 1 468 | 7 844 | 24.42 | 22.06 | 2.36 | 48.7 |
| 1994-10 | 1 515 | 1 512 | 8 197 | 23.79 | 22.82 | 0.97 | 49.6 |
| 1994-11 | 1 543 | 1 542 | 8 275 | 25.03 | 22.56 | 2.47 | 52.1 |
| 1994-12 | 1 578 | 1 577 | 9 795 | 32.33 | 29.58 | 2.75 | 54.9 |
| 1995-01 | 1 642 | 1 642 | 15 493 | 26.89 | 39.36 | -12.47 | 42.4 |
| 1995-02 | 1 686 | 1 680 | 8 682 | 27.11 | 18.02 | 9.09 | 51.5 |
| 1995-03 | 1 734 | 1 733 | 9 304 | 29.31 | 24.81 | 4.5 | 56 |
| 1995-04 | 1 786 | 1 786 | 9 519 | 28.92 | 25.92 | 3 | 59 |
| 1995-05 | 1 836 | 1 836 | 9 938 | 31.33 | 28.58 | 2.75 | 61.7 |
| 1995-06 | 1 893 | 1 891 | 10 930 | 39.82 | 41.79 | -1.97 | 59.7 |
| 1995-07 | 1 941 | 1 941 | 10 431 | 31.92 | 28.04 | 3.89 | 63.6 |
| 1995-08 | 1 999 | 1 997 | 10 766 | 32.57 | 29.35 | 3.22 | 66.9 |
| 1995-09 | 2 059 | 2 059 | 11 013 | 33.07 | 29.98 | 3.09 | 69.9 |
| 1995-10 | 2 124 | 2 121 | 11 431 | 34.52 | 32.07 | 2.45 | 72.4 |
| 1995-11 | 2 189 | 2 188 | 11 741 | 34.7 | 32.75 | 1.95 | 74.3 |
| 1995-12 | 2 239 | 2 238 | 13 774 | 45.91 | 40.99 | 4.92 | 79.3 |
| 1996-01 | 2 345 | 2 344 | 21 405 | 38.69 | 54.93 | -16.25 | 63 |
| 1996-02 | 2 449 | 2 445 | 12 507 | 40.12 | 27.55 | 12.56 | 75.6 |
| 1996-03 | 2 573 | 2 569 | 13 297 | 41.92 | 35.04 | 6.87 | 82.4 |
| 1996-04 | 2 674 | 2 671 | 13 754 | 42.82 | 36.36 | 6.46 | 88.9 |

**Lecture.** Chaque mois de janvier affiche un flux net négatif (-18,5 M CZK en moyenne contre 4,6 M les autres mois) : les clients vident leur compte en début d'année, puis le rebond de février le reconstitue.

**Décision / action.** Anticiper la trésorerie (cash disponible aux guichets) à chaque janvier et décembre, et ne jamais comparer janvier à décembre sans corriger de la saisonnalité.

**Limite.** Aucune ouverture de compte après 1997 dans l'extraction : la « croissance » du nombre de comptes ne peut pas être extrapolée à 1998.

### Q03 — Qui sont les titulaires de compte ?

**Question.** Quel est le profil des titulaires (sexe, âge) et quelle part équipe-t-on en carte et en prêt ?

**Réponse.** Le portefeuille est équilibré (49 % de femmes) et réparti sur toutes les tranches d'âge, mais l'équipement varie fortement : les 65 ans et plus (638 comptes) n'ont que 2,4 % de cartes et 0,0 % de prêts, contre 28,1 % de cartes chez les moins de 25 ans.

| tranche_age | comptes | pct_femmes | pct_avec_carte | pct_avec_pret | solde_moyen_1998 |
|---|---|---|---|---|---|
| 25-34 | 819 | 53.2 | 20.8 | 20.4 | 46 810 |
| 35-44 | 798 | 50.8 | 20.1 | 18.8 | 46 222 |
| 45-54 | 832 | 51.6 | 23.3 | 19.2 | 48 249 |
| 55-64 | 698 | 43 | 21.8 | 15.9 | 44 693 |
| 65+ | 638 | 44.7 | 2.4 | 0 | 28 235 |
| <25 | 715 | 49.4 | 28.1 | 13.1 | 45 560 |

**Lecture.** Le solde moyen est stable en dessous de 65 ans (44 693 à 48 249 CZK) puis chute à 28 235 CZK chez les 65 ans et plus : clients peu équipés, aux soldes bas.

**Décision / action.** Deux leviers distincts : l'équipement des seniors (cartes) et le crédit, aujourd'hui concentré sur les 25-54 ans.

**Limite.** L'âge est calculé au 31/12/1998 et l'équipement est observé à cette date, pas à l'ouverture du compte.

### Q04 — Géographie des comptes et des soldes

**Question.** Quelles régions concentrent les comptes et les dépôts, et le solde moyen suit-il le niveau de salaire local ?

**Réponse.** North Moravia et South Moravia concentrent 35 % des comptes. Le solde moyen varie de seulement 7 % d'une région à l'autre (41 843 à 44 942 CZK) alors que le salaire moyen varie de 45 %.

| region | comptes | part_comptes_pct | encours_m | part_encours_pct | solde_moyen | salaire_moyen_district | chomage_1996_pct |
|---|---|---|---|---|---|---|---|
| north moravia | 793 | 17.6 | 35 | 17.8 | 44 139 | 9 410 | 5.83 |
| south moravia | 778 | 17.3 | 34 | 17.3 | 43 732 | 8 895 | 3.51 |
| central bohemia | 574 | 12.8 | 25.2 | 12.8 | 43 820 | 9 409 | 2.89 |
| prague | 554 | 12.3 | 24.9 | 12.6 | 44 942 | 12 541 | 0.43 |
| east bohemia | 544 | 12.1 | 23.7 | 12 | 43 496 | 8 626 | 2.98 |
| north bohemia | 457 | 10.2 | 20.2 | 10.2 | 44 127 | 9 310 | 5.83 |
| west bohemia | 430 | 9.6 | 18.8 | 9.5 | 43 638 | 9 018 | 2.7 |
| south bohemia | 370 | 8.2 | 15.5 | 7.9 | 41 843 | 8 817 | 2.82 |

**Lecture.** La corrélation région par région entre salaire local et solde moyen est de 0,66, mais avec 8 régions elle n'est pas significative au seuil de 5 % (il faudrait au moins 0,71) et l'effet reste faible : Prague a un salaire 32 % au-dessus de la moyenne des régions pour un solde moyen de 44 942 CZK, quasi identique aux autres.

**Décision / action.** Ne pas segmenter l'offre d'épargne par région : le comportement de dépôt est homogène. Réserver la segmentation géographique au risque de crédit (chômage) et à l'implantation.

**Limite.** 8 régions seulement : une corrélation sur 8 points est indicative, pas démonstrative ; le salaire est celui du district, pas celui du client.

### Q05 — Comment les clients utilisent leur compte

**Question.** Quelle part des opérations passe par les espèces au guichet, la carte, les virements ? Qu'est-ce qui entre, qu'est-ce qui sort ?

**Réponse.** Les espèces au guichet pèsent 41 % des opérations et 76 % des montants ; les virements 26 % des opérations et 23 % des montants ; la carte 0,8 % des opérations.

| canal | sens | operations | part_operations_pct | montant_m | part_montant_pct | montant_moyen |
|---|---|---|---|---|---|---|
| Espèces (guichet) | credit | 156 743 | 14.8 | 2 418.5 | 38.6 | 15 430 |
| Espèces (guichet) | debit | 277 509 | 26.3 | 2 336.8 | 37.3 | 8 421 |
| Virement | credit | 65 226 | 6.2 | 781.5 | 12.5 | 11 981 |
| Virement | debit | 208 283 | 19.7 | 672.6 | 10.7 | 3 229 |
| Interne (frais & intérêts) | credit | 183 114 | 17.3 | 27.5 | 0.4 | 150 |
| Carte | debit | 8 036 | 0.8 | 18.2 | 0.3 | 2 261 |
| Interne (frais & intérêts) | debit | 157 409 | 14.9 | 2.7 | 0 | 17 |

**Lecture.** La banque fonctionne en 1993-1998 comme une banque de guichet : l'argent entre en espèces et ressort en espèces. Les frais et intérêts (« Interne ») représentent un tiers du nombre d'opérations pour moins de 1 % des montants : ils gonflent les volumes sans refléter l'activité des clients.

**Décision / action.** Pour mesurer l'activité client, exclure les opérations internes ; pour dimensionner l'infrastructure, les compter.

**Limite.** Dans la source, « retrait » (VYBER) désigne aussi les frais de relevé : le canal est reconstruit à partir du motif, pas du libellé brut.

### Q06 — Comptes dormants et attrition silencieuse

**Question.** Combien de comptes ont cessé toute activité avant la fin de la période observée ? Qui sont-ils ?

**Réponse.** 16 comptes seulement (0,4 %) n'ont plus d'opération depuis juillet 1998.

| statut | comptes | part_pct | transactions_moyennes | pct_avec_pret | pct_avec_carte |
|---|---|---|---|---|---|
| Actif (opération depuis oct. 1998) | 4 484 | 99.6 | 235 | 15.2 | 19.9 |
| Dormant (aucune opération depuis juil. 1998) | 14 | 0.3 | 26 | 0 | 0 |
| Ralenti (dernière opération juil.-sept. 1998) | 2 | 0 | 100 | 0 | 0 |

**Lecture.** Une attrition aussi faible est suspecte : l'extraction ne contient très probablement que des comptes restés ouverts (biais du survivant). Elle ne permet donc pas de mesurer le churn réel.

**Décision / action.** Avant tout modèle d'attrition, demander à la source si les comptes clôturés ont été exclus ; sinon, ne pas conclure que la banque fidélise bien.

**Limite.** Le critère « dormant » (aucune opération depuis juillet 1998) est arbitraire : à calibrer avec le métier.

### Q07 — Découverts : combien, qui, et à quel point

**Question.** Quelle part des comptes passe en négatif ? Le phénomène est-il récurrent ou accidentel ? Qui est concerné ?

**Réponse.** 93,6 % des comptes ne passent jamais en négatif ; 288 comptes (6,4 %) ont connu au moins un mois de découvert, dont 49 de façon chronique (7 mois ou plus, pire solde moyen -13 242 CZK).

| profil | comptes | part_pct | pire_solde_moyen | pct_avec_pret | age_moyen |
|---|---|---|---|---|---|
| 0-jamais à découvert | 4 212 | 93.6 | 777 | 14.4 | 44.4 |
| 1-accidentel (1-2 mois) | 170 | 3.8 | -1 965 | 21.8 | 39.2 |
| 2-récurrent (3-6 mois) | 69 | 1.5 | -5 042 | 36.2 | 41.8 |
| 3-chronique (7 mois ou plus) | 49 | 1.1 | -13 242 | 28.6 | 41.3 |

**Lecture.** Les découverts récurrents sont liés au crédit : 36 % des comptes à découvert récurrent ont aussi un prêt, contre 14 % des comptes sans découvert. Le découvert répété accompagne la prise de crédit : c'est un signal de tension financière, pas un simple incident (association observée, pas un lien de cause à effet).

**Décision / action.** Mettre une alerte « 3 mois de découvert sur 12 » dans le suivi du risque, avant toute nouvelle autorisation de crédit.

**Limite.** Découvert mesuré sur le solde après chaque opération (minimum du mois), pas sur le solde de fin de journée.

### Q08 — Cartes : pénétration et effet sur les usages

**Question.** Quelle part des comptes a une carte ? Les détenteurs vont-ils moins souvent au guichet ?

**Réponse.** 20 % des comptes ont une carte, mais ils l'utilisent très peu : 0,21 retrait par carte par mois en moyenne.

| carte | comptes | part_comptes_pct | tx_par_mois | passages_guichet_par_mois | retraits_carte_par_mois | age_moyen |
|---|---|---|---|---|---|---|
| none | 3 608 | 80.2 | 5.47 | 2.2 | 0 | 45.4 |
| classic | 659 | 14.6 | 5.94 | 2.69 | 0.19 | 42.8 |
| junior | 145 | 3.2 | 5.69 | 2.65 | 0.24 | 19.1 |
| gold | 88 | 2 | 5.99 | 2.71 | 0.19 | 43.5 |

**Lecture.** Les détenteurs de carte ne vont pas moins au guichet (2,68 passages par mois contre 2,20 sans carte) : la carte s'ajoute aux habitudes, elle ne les remplace pas.

**Décision / action.** Si la banque veut désengorger les guichets, l'équipement ne suffit pas ; il faut activer l'usage (retraits gratuits, distributeurs, communication).

**Limite.** Une corrélation (les clients à carte sont aussi les plus actifs) n'est pas un effet causal de la carte.

### Q09 — Le portefeuille de prêts et son taux de défaut

**Question.** Combien de prêts, pour quel montant, et quelle part est en défaut (terminé non remboursé ou en cours en impayé) ?

**Réponse.** 76 prêts sur 682 sont en défaut (terminés non remboursés ou en impayé) : 11,1 % en nombre mais 15,1 % en montant (15,6 M CZK sur 103,3).

| statut | libelle | prets | part_prets_pct | montant_m | part_montant_pct | montant_moyen | duree_moyenne_mois |
|---|---|---|---|---|---|---|---|
| A | finished_ok | 203 | 29.8 | 18.6 | 18 | 91 641 | 22.2 |
| B | finished_not_paid | 31 | 4.5 | 4.4 | 4.2 | 140 721 | 25.5 |
| C | running_ok | 403 | 59.1 | 69.1 | 66.9 | 171 410 | 43.4 |
| D | running_in_debt | 45 | 6.6 | 11.2 | 10.9 | 249 285 | 46.1 |

**Lecture.** Les prêts en défaut sont plus gros que la moyenne (D : 249 285 CZK contre 91 641 CZK pour A) : la perte en valeur est supérieure à la perte en nombre. Le risque se concentre sur les gros dossiers.

**Décision / action.** Piloter le risque en montant (exposition) et pas seulement en nombre de dossiers.

**Limite.** B + D = défaut est une convention de lecture du statut Berka (D = en cours mais impayé) ; aucune perte réelle ni récupération n'est observée.

### Q10 — Quels prêts font défaut ?

**Question.** Le défaut dépend-il du montant, de la durée, de la région (chômage), de l'âge de l'emprunteur ?

**Réponse.** Le montant est le facteur dominant : 18,9 % de défaut au-dessus de 200 k CZK contre 4,0 % sous 50 k (4,7 fois plus).

| dimension | modalite | prets | defauts | taux_defaut_pct |
|---|---|---|---|---|
| Chômage du district | chômage faible (<3 %) | 298 | 29 | 9.7 |
| Chômage du district | chômage moyen (3-5 %) | 230 | 28 | 12.2 |
| Chômage du district | chômage élevé (5 %+) | 154 | 19 | 12.3 |
| Durée | 12 mois | 131 | 11 | 8.4 |
| Durée | 24 mois | 138 | 17 | 12.3 |
| Durée | 36 mois | 130 | 15 | 11.5 |
| Durée | 48 mois | 138 | 16 | 11.6 |
| Durée | 60 mois | 145 | 17 | 11.7 |
| Montant | 100-200k | 192 | 18 | 9.4 |
| Montant | 200k+ | 185 | 35 | 18.9 |
| Montant | 50-100k | 179 | 18 | 10.1 |
| Montant | <50k | 126 | 5 | 4 |
| Âge | 25-34 | 167 | 16 | 9.6 |
| Âge | 35-44 | 150 | 15 | 10 |
| Âge | 45-54 | 160 | 19 | 11.9 |
| Âge | 55-64 | 111 | 13 | 11.7 |
| Âge | <25 | 94 | 13 | 13.8 |

**Lecture.** La durée compte peu au-delà d'un an (8,4 % à 12 mois, puis de 11,5 % à 12,3 % ensuite) ; le chômage local et l'âge produisent des écarts modestes (âge : de 9,6 % à 13,8 %). Avec 94 à 167 prêts par tranche, un écart de 4 points est dans le bruit statistique (± 5 points).

**Décision / action.** Plafonner l'exposition unitaire ou exiger des garanties au-delà de 200 k CZK. Ne pas surinterpréter les tranches d'âge.

**Limite.** Analyse univariée : le montant est corrélé à la durée et au revenu ; le modèle multivarié (module ML) démêle ces effets.

### Q11 — Défaut par année d'octroi (analyse de vintage) et biais de censure

**Question.** Les prêts récents sont-ils meilleurs ou simplement trop jeunes pour avoir fait défaut ?

**Réponse.** Les prêts de 1998 affichent seulement 2,5 % de défaut contre 13 % pour l'ensemble 1994-1997.

| annee_octroi | prets | defauts | taux_defaut_pct | pct_encore_en_cours | montant_moyen |
|---|---|---|---|---|---|
| 1 993 | 20 | 4 | 20 | 0 | 130 964 |
| 1 994 | 101 | 14 | 13.9 | 15.8 | 132 474 |
| 1 995 | 90 | 12 | 13.3 | 43.3 | 148 271 |
| 1 996 | 117 | 16 | 13.7 | 70.1 | 156 561 |
| 1 997 | 196 | 26 | 13.3 | 78.1 | 156 793 |
| 1 998 | 158 | 4 | 2.5 | 100 | 157 400 |

**Lecture.** Ce n'est PAS une amélioration : 100 % des prêts de 1998 sont encore en cours, ils n'ont pas eu le temps de faire défaut (censure à droite). La comparaison valide se fait à âge de prêt égal, pas à date de calendrier.

**Décision / action.** Ne jamais présenter le taux de défaut brut d'un millésime récent sans préciser son âge ; produire des courbes de défaut par mois depuis l'octroi.

**Limite.** Les données n'ont pas la date du défaut : la courbe par âge de prêt n'est pas reconstructible ici.

### Q12 — Signaux d'alerte AVANT l'octroi

**Question.** Que savait-on sur le compte dans les 6 mois précédant le prêt qui aurait permis de prévoir le défaut ?

**Réponse.** Le taux d'effort (mensualité / entrées mensuelles moyennes des 6 mois précédents) sépare très bien les dossiers : 5,2 % de défaut sous 10 %, 26,8 % au-delà de 35 % (5,2 fois plus).

| taux_effort | prets | defauts | taux_defaut_pct | solde_moyen_avant | mois_decouvert_avant |
|---|---|---|---|---|---|
| 1-effort < 10 % | 191 | 10 | 5.2 | 48 332 | 0.02 |
| 2-effort 10-20 % | 329 | 27 | 8.2 | 39 720 | 0.02 |
| 3-effort 20-35 % | 80 | 17 | 21.3 | 34 084 | 0.11 |
| 4-effort 35 % et plus | 82 | 22 | 26.8 | 25 508 | 0.16 |

**Lecture.** Les 24 % de prêts à taux d'effort supérieur à 20 % concentrent 51 % des défauts. Le solde moyen avant octroi tombe de 48 332 à 25 508 CZK, et les mois de découvert passent de 0,02 à 0,16 par dossier. Tout est calculé avec des données antérieures à l'octroi : le signal est donc exploitable en production.

**Décision / action.** Règle simple immédiate : revue manuelle obligatoire au-delà de 20 % de taux d'effort ; le score statistique (module ML) affine ensuite.

**Limite.** Les entrées du compte sous-estiment le revenu des clients qui sont payés sur un autre compte.

### Q13 — Revenus et coûts observables dans les données

**Question.** Que gagne la banque en frais et pénalités, que verse-t-elle en intérêts, et à quel taux implicite rémunère-t-elle les dépôts ?

**Réponse.** En 1998 les frais de relevé rapportent 816 k CZK et les pénalités de découvert 27 k, alors que la banque verse 8 685 k CZK d'intérêts aux déposants (10,6 fois plus), à un taux implicite stable d'environ 5,2 %.

| annee | frais_releve_k | interets_penalite_k | interets_verses_k | encours_moyen_m | taux_servi_implicite_pct |
|---|---|---|---|---|---|
| 1 993 | 50 | 0 | 811 | 17.6 | 4.61 |
| 1 994 | 233 | 1 | 2 294 | 44.1 | 5.2 |
| 1 995 | 344 | 1 | 3 298 | 63.1 | 5.23 |
| 1 996 | 501 | 2 | 5 010 | 97.6 | 5.13 |
| 1 997 | 744 | 7 | 7 373 | 142.1 | 5.19 |
| 1 998 | 816 | 27 | 8 685 | 167.8 | 5.17 |

**Lecture.** Les pénalités de découvert ont été multipliées par 3,9 entre 1997 et 1998 : recette en hausse, mais aussi signe de tension croissante des clients (cf. Q07).

**Décision / action.** Ne pas conclure à la rentabilité à partir de ces seuls flux : le revenu d'intermédiation (prêts - dépôts) manque.

**Limite.** Les mensualités de prêt valent exactement capital / durée : aucun intérêt de prêt n'est enregistré. Marge, coût du risque et refinancement ne sont pas calculables. Périmètre partiel assumé.

### Q14 — Concentration des dépôts

**Question.** Quelle part de l'encours détiennent les 1 %, 10 % et 20 % de comptes les plus riches ?

**Réponse.** Les 10 % de comptes les plus riches détiennent 22 % des dépôts ; le 1 % du haut seulement 2,6 %.

| segment_riche | comptes | encours_m | part_encours_pct | solde_moyen |
|---|---|---|---|---|
| a-1 % des comptes | 45 | 5.1 | 2.6 | 114 204 |
| b-10 % des comptes | 405 | 37.5 | 19 | 92 665 |
| c-90 % restants | 4 050 | 154.7 | 78.4 | 38 144 |

**Lecture.** Concentration faible : portefeuille de détail, sans gros dépôts dont le départ menacerait la liquidité.

**Décision / action.** Risque de concentration des dépôts : faible. Pas de politique « grands comptes » à prévoir.

**Limite.** Soldes comptés par compte ; un client à plusieurs comptes n'est pas regroupé (le jeu en a peu : un titulaire par compte).

### Q15 — Cohortes d'ouverture de compte

**Question.** Les comptes ouverts en 1993 se comportent-ils comme ceux de 1997 ? Quel solde et quelle activité après 12 et 24 mois ?

**Réponse.** Toutes les cohortes se ressemblent : solde moyen à 12 mois de 31 766 à 34 216 CZK et environ 6,1 opérations par mois.

| annee_ouverture | comptes | solde_moyen_12m | solde_moyen_24m | tx_mois_12m | tx_mois_24m |
|---|---|---|---|---|---|
| 1 993 | 1 139 | 31 766 | 33 313 | 6.2 | 6.3 |
| 1 994 | 439 | 34 216 | 35 071 | 6.1 | 6.1 |
| 1 995 | 661 | 32 009 | 34 635 | 6.2 | 6.2 |
| 1 996 | 1 363 | 32 261 | 35 149 | 6.2 | 6 |
| 1 997 | 898 | 32 602 | — | 6 | — |

**Lecture.** Le solde progresse de quelques milliers de CZK entre 12 et 24 mois mais l'activité reste plate : les clients gardent leurs habitudes dès la première année. Pas d'effet millésime.

**Décision / action.** Le comportement observé à 12 mois est déjà celui des 24 mois : inutile d'attendre deux ans pour juger un compte.

**Limite.** La cohorte 1997 n'a pas 24 mois d'historique (NaN attendu).

### Q16 — Saisonnalité : le pic de janvier

**Question.** Existe-t-il des mois ou des jours où l'activité explose ? Quelles opérations expliquent le pic ?

**Réponse.** Janvier concentre 79 097 opérations en 1994-1997, soit 1,7 fois février ; décembre est le deuxième pic (indice 125, base 100 = mois moyen).

| mois | operations | indice_activite_100 | retraits_guichet | sorties_m | part_retraits_pct |
|---|---|---|---|---|---|
| 1 | 79 097 | 134 | 41 418 | 205.3 | 52.4 |
| 2 | 45 992 | 78 | 8 276 | 102.3 | 18 |
| 3 | 49 347 | 84 | 10 728 | 133.4 | 21.7 |
| 4 | 50 744 | 86 | 11 112 | 138.2 | 21.9 |
| 5 | 52 991 | 90 | 12 125 | 152.9 | 22.9 |
| 6 | 58 563 | 100 | 16 159 | 226.2 | 27.6 |
| 7 | 55 810 | 95 | 12 005 | 151.2 | 21.5 |
| 8 | 57 644 | 98 | 12 835 | 160.4 | 22.3 |
| 9 | 59 064 | 100 | 13 006 | 166.7 | 22 |
| 10 | 61 161 | 104 | 13 887 | 175 | 22.7 |
| 11 | 62 127 | 106 | 13 827 | 175.8 | 22.3 |
| 12 | 73 298 | 125 | 23 329 | 225.3 | 31.8 |

**Lecture.** Les retraits au guichet expliquent le pic : 52 % des opérations de janvier contre 22 % les mois ordinaires, pour 205 M CZK de sorties contre 102 M en février. Hypothèse à confirmer avec le métier : besoins de trésorerie de fin d'année (fêtes, charges annuelles).

**Décision / action.** Renforcer les liquidités en agence en décembre-janvier ; ne pas déclencher d'alerte « retraits anormaux » en janvier sans neutraliser la saisonnalité.

**Limite.** Quatre années pleines seulement ; l'hypothèse n'est pas démontrée par ces données.

### Q17 — Segmentation comportementale des comptes

**Question.** Peut-on regrouper les comptes en segments actionnables pour le marketing et la gestion du risque ?

**Réponse.** 5 segments : 11 % de comptes Premium détiennent 23 % de l'encours ; 68 comptes (1,5 %) sont à surveiller (découvert récurrent).

| segment | comptes | part_comptes_pct | encours_m | solde_moyen | tx_par_mois | pct_avec_pret |
|---|---|---|---|---|---|---|
| 1-Premium (solde >= 80 k) | 496 | 11 | 46.4 | 93 540 | 6.6 | 19.4 |
| 2-Actifs (8 opérations/mois et +, top 10 %) | 372 | 8.3 | 17.7 | 47 485 | 8.8 | 45.2 |
| 3-Courants | 2 712 | 60.3 | 107.6 | 39 659 | 5.7 | 14 |
| 4-Seniors (60 ans et +) | 852 | 18.9 | 25.3 | 29 680 | 5.3 | 2.7 |
| 5-À surveiller (découvert récurrent) | 68 | 1.5 | 0.5 | 3 647 | 4.9 | 22.1 |

**Lecture.** Les règles sont volontairement lisibles par un directeur d'agence : seuil de solde, âge, fréquence d'opérations, découverts. Le segment « Actifs » est celui où le crédit est le plus présent (45 % ont un prêt contre 14 % des « Courants ») : une partie de leur activité vient des remboursements, pas d'une intensité d'usage à valoriser commercialement.

**Décision / action.** Premium : offre d'épargne rémunérée. Seniors : conseil et sécurité. À surveiller : appel proactif avant un incident de remboursement.

**Limite.** Segmentation à règles, pas un clustering statistique ; les seuils (80 k, 25 opérations, 3 mois) sont des choix métier révisables.

### Q18 — Ordres permanents et équipement des comptes

**Question.** Quels engagements récurrents les clients ont-ils confiés à la banque (loyer/énergie, assurance, leasing, prêt) ?

**Réponse.** 75 % des comptes confient à la banque un ordre permanent de charges (14,0 M CZK par mois), loin devant l'assurance (12 %) et le leasing.

| objet | ordres | comptes | pct_des_comptes | montant_moyen | total_mensuel_m |
|---|---|---|---|---|---|
| Loyer, énergie, charges (SIPO) | 3 502 | 3 365 | 74.8 | 3 988 | 13.97 |
| Non précisé | 1 379 | 1 198 | 26.6 | 2 017 | 2.78 |
| Remboursement de prêt | 717 | 717 | 15.9 | 4 233 | 3.04 |
| Assurance | 532 | 532 | 11.8 | 1 291 | 0.69 |
| Leasing | 341 | 341 | 7.6 | 2 227 | 0.76 |

**Lecture.** Ces comptes sont « ancrés » : un prélèvement automatique rend le changement de banque pénible. 717 ordres de remboursement existent alors que le fichier ne contient que 682 prêts : 35 ordres correspondent à des prêts absents du fichier (cf. règle qualité K07).

**Décision / action.** Cibler la vente d'assurance (seulement 11,8 % des comptes) aux comptes ayant déjà des charges prélevées.

**Limite.** Le montant d'un ordre est un montant mensuel déclaré, pas un flux observé.

## Fraude carte bancaire

### F01 — Fraude carte : l'ampleur du problème

**Question.** Quelle part des transactions et des montants est frauduleuse ? (après suppression des doublons exacts)

**Réponse.** 473 fraudes sur 283 726 transactions : 0,167 %, soit 1 transaction sur 599. Le montant moyen d'une fraude (124) dépasse celui d'une transaction légitime (88).

| classe | transactions | part_transactions_pct | montant_total | part_montant_pct | montant_moyen | montant_max |
|---|---|---|---|---|---|---|
| Fraude | 473 | 0.17 | 58 591 | 0.23 | 123.9 | 2 126 |
| Légitime | 283 253 | 99.83 | 25 043 410 | 99.77 | 88.4 | 25 691 |

**Lecture.** En valeur, la fraude ne pèse que 0,233 % des montants : le sujet n'est pas le coût direct mais le tri. Avec un tel déséquilibre, un modèle « tout est légitime » aurait 99,83 % d'exactitude : l'exactitude est une métrique inutile ici.

**Décision / action.** Évaluer tout modèle avec la précision-rappel (PR-AUC) et en euros, jamais avec l'exactitude.

**Limite.** 492 fraudes dans le jeu public, 473 après suppression des 19 doublons exacts : ce choix est tracé en quarantaine (règle F01).

### F02 — Fraude et heure de la journée

**Question.** La fraude est-elle plus fréquente à certaines heures ? Quelles fenêtres de risque surveiller ?

**Réponse.** La nuit (0 h à 5 h) concentre 24 % des fraudes pour 8 % des transactions. Le pire créneau est 2 h : 145 fraudes pour 10 000 transactions, soit 9 fois la moyenne (16,7).

| heure | tranche | transactions | fraudes | fraudes_pour_10000 |
|---|---|---|---|---|
| 0 | 1-nuit (0-5h) | 7 647 | 6 | 7.8 |
| 1 | 1-nuit (0-5h) | 4 208 | 10 | 23.8 |
| 2 | 1-nuit (0-5h) | 3 308 | 48 | 145.1 |
| 3 | 1-nuit (0-5h) | 3 487 | 17 | 48.8 |
| 4 | 1-nuit (0-5h) | 2 204 | 23 | 104.4 |
| 5 | 1-nuit (0-5h) | 2 988 | 11 | 36.8 |
| 6 | 2-matin (6-11h) | 4 082 | 9 | 22 |
| 7 | 2-matin (6-11h) | 7 233 | 23 | 31.8 |
| 8 | 2-matin (6-11h) | 10 232 | 9 | 8.8 |
| 9 | 2-matin (6-11h) | 15 767 | 16 | 10.1 |
| 10 | 2-matin (6-11h) | 16 548 | 8 | 4.8 |
| 11 | 2-matin (6-11h) | 16 781 | 53 | 31.6 |
| 12 | 3-après-midi (12-17h) | 15 378 | 17 | 11.1 |
| 13 | 3-après-midi (12-17h) | 15 323 | 17 | 11.1 |
| 14 | 3-après-midi (12-17h) | 16 520 | 23 | 13.9 |
| 15 | 3-après-midi (12-17h) | 16 374 | 26 | 15.9 |
| 16 | 3-après-midi (12-17h) | 16 396 | 22 | 13.4 |
| 17 | 3-après-midi (12-17h) | 16 130 | 28 | 17.4 |
| 18 | 4-soir (18-23h) | 16 959 | 28 | 16.5 |
| 19 | 4-soir (18-23h) | 15 566 | 19 | 12.2 |
| 20 | 4-soir (18-23h) | 16 705 | 18 | 10.8 |
| 21 | 4-soir (18-23h) | 17 629 | 16 | 9.1 |
| 22 | 4-soir (18-23h) | 15 378 | 9 | 5.9 |
| 23 | 4-soir (18-23h) | 10 883 | 17 | 15.6 |

**Lecture.** En nombre absolu, la fraude est aussi fréquente la nuit que le jour (19 fraudes par heure de nuit contre 20 de jour) alors que le volume légitime est bien plus faible la nuit : la proportion de fraude explose donc mécaniquement. Hypothèse : les fraudeurs n'ont pas de rythme jour/nuit du pays des porteurs de cartes.

**Décision / action.** Durcir les règles (authentification forte, plafonds) sur la fenêtre 0 h - 5 h plutôt que sur toute la journée : l'impact sur les clients légitimes est limité (8 % du volume).

**Limite.** Heure relative au début du jeu sur 48 h, pas à un fuseau horaire ; émetteurs européens, sept. 2013.

### F03 — Montants : les fraudeurs testent-ils les cartes avec de petits achats ?

**Question.** Comment se répartissent les montants des fraudes comparés aux transactions légitimes ?

**Réponse.** Les transactions à montant nul ont 138 fraudes pour 10 000, soit 8 fois la moyenne ; 50 % des fraudes concernent des montants de moins de 10, contre 34 % des transactions légitimes.

| tranche_montant | transactions | fraudes | part_des_fraudes_pct | part_des_legitimes_pct | fraudes_pour_10000 |
|---|---|---|---|---|---|
| 0 | 1 808 | 25 | 5.3 | 0.6 | 138.3 |
| <1 | 14 957 | 41 | 8.7 | 5.3 | 27.4 |
| 1-10 | 80 108 | 172 | 36.4 | 28.2 | 21.5 |
| 10-50 | 91 937 | 54 | 11.4 | 32.4 | 5.9 |
| 50-100 | 37 640 | 56 | 11.8 | 13.3 | 14.9 |
| 100-500 | 47 817 | 91 | 19.2 | 16.8 | 19 |
| 500-1000 | 6 395 | 25 | 5.3 | 2.2 | 39.1 |
| 1000+ | 3 064 | 9 | 1.9 | 1.1 | 29.4 |

**Lecture.** Compatible avec le « card testing » (hypothèse) : le fraudeur valide la carte volée avec un micro-montant, puis la vide. Les montants de 500 et plus sont 2,2 fois plus fréquents parmi les fraudes que parmi les légitimes.

**Décision / action.** Surveiller les séries de micro-transactions (< 1) sur une même carte : c'est un signal précoce, avant la grosse fraude.

**Limite.** Aucun identifiant de carte dans le jeu : on ne peut pas reconstituer les séries par carte, seulement la distribution des montants.

### F04 — Quelles variables séparent le mieux fraude et légitime ?

**Question.** Parmi les composantes anonymisées V1-V28, lesquelles se comportent le plus différemment en cas de fraude ?

**Réponse.** Quatre composantes séparent nettement fraude et légitime : V17, V14, V12, V10 (écarts de 5,1 à 7,7 écarts-types).

| variable | moyenne_legitime | moyenne_fraude | ecart_standardise |
|---|---|---|---|
| V17 | 0.01 | -6.46 | -7.68 |
| V14 | 0.01 | -6.84 | -7.19 |
| V12 | 0.01 | -6.1 | -6.15 |
| V10 | 0.01 | -5.45 | -5.07 |
| V16 | 0.01 | -4 | -4.59 |
| V3 | 0.01 | -6.73 | -4.47 |
| V7 | 0.01 | -5.18 | -4.22 |
| V11 | -0.01 | 3.72 | 3.65 |
| V4 | -0.01 | 4.47 | 3.17 |
| V2 | -0.01 | 3.41 | 2.07 |

**Lecture.** Les variables sont une ACP anonymisée par la source : on ne peut pas dire ce qu'elles « signifient » (c'est volontaire, confidentialité), seulement qu'elles portent le signal. Un écart de plus de 5 écarts-types est exceptionnel : peu de variables suffisent à séparer l'essentiel.

**Décision / action.** Pour le modèle (module ML), garder toutes les composantes ; pour l'explicabilité, présenter ces quatre-là.

**Limite.** Séparation univariée : les composantes sont décorrélées par construction (ACP), donc leurs effets s'additionnent.

## Scoring de crédit

### G01 — Scoring de crédit : qui fait défaut ?

**Question.** Quels profils d'emprunteurs ont les plus forts taux de défaut ? (1 000 dossiers du jeu UCI Statlog German Credit)

**Réponse.** Le défaut global est de 30 %. Il atteint 49,3 % pour les comptes courants à découvert contre 11,7 % pour les clients sans compte courant connu, et 51,7 % pour les crédits de plus de 36 mois contre 21,2 % à 12 mois ou moins.

| variable | modalite | dossiers | defauts | taux_defaut_pct |
|---|---|---|---|---|
| Compte courant | < 0 DM | 274 | 135 | 49.3 |
| Compte courant | 1 - 200 DM | 269 | 105 | 39 |
| Compte courant | > 200 DM | 63 | 14 | 22.2 |
| Compte courant | unknown | 394 | 46 | 11.7 |
| Durée | 37+ mois | 87 | 45 | 51.7 |
| Durée | 25-36 mois | 143 | 57 | 39.9 |
| Durée | 13-24 mois | 411 | 122 | 29.7 |
| Durée | <=12 mois | 359 | 76 | 21.2 |
| Historique de crédit | fully repaid | 40 | 25 | 62.5 |
| Historique de crédit | fully repaid this bank | 49 | 28 | 57.1 |
| Historique de crédit | repaid | 530 | 169 | 31.9 |
| Historique de crédit | delayed | 88 | 28 | 31.8 |
| Historique de crédit | critical | 293 | 50 | 17.1 |
| Logement | for free | 108 | 44 | 40.7 |
| Logement | rent | 179 | 70 | 39.1 |
| Logement | own | 713 | 186 | 26.1 |
| Montant (DM) | 6000+ | 149 | 68 | 45.6 |
| Montant (DM) | <1500 | 306 | 88 | 28.8 |
| Montant (DM) | 3000-5999 | 231 | 66 | 28.6 |
| Montant (DM) | 1500-2999 | 314 | 78 | 24.8 |
| Âge | <25 | 149 | 61 | 40.9 |
| Âge | 25-34 | 399 | 131 | 32.8 |
| Âge | 55+ | 79 | 22 | 27.8 |
| Âge | 35-44 | 251 | 58 | 23.1 |
| Âge | 45-54 | 122 | 28 | 23 |
| Épargne | < 100 DM | 603 | 217 | 36 |
| Épargne | 101 - 500 DM | 103 | 34 | 33 |
| Épargne | 501 - 1000 DM | 63 | 11 | 17.5 |
| Épargne | unknown | 183 | 32 | 17.5 |
| Épargne | > 1000 DM | 48 | 6 | 12.5 |

**Lecture.** Résultat contre-intuitif à expliquer : l'historique « critique » a un taux de défaut de 17,1 % (le plus bas) alors que « entièrement remboursé » monte à 62,5 %. C'est un biais de sélection : on n'observe que des clients à qui la banque a accordé un crédit ; hypothèse : ceux qui ont un passé difficile n'ont été acceptés qu'après un examen très sévère.

**Décision / action.** Ne jamais « lire » un coefficient de scoring comme une cause : le modèle apprend la politique d'octroi passée (problème de l'inférence des refusés).

**Limite.** 1 000 dossiers d'un seul établissement allemand (années 1970-90) : valeurs non transposables, méthode oui.

### G02 — Information Value : quelles variables pèsent le plus dans un scorecard ?

**Question.** Quelle est la force prédictive de chaque variable (méthode WoE / IV, standard en risque de crédit) ?

**Réponse.** « Compte courant » domine avec une IV de 0,66 ; 6 variables ont une IV supérieure à 0,1 (Compte courant, Historique de crédit, Épargne, Durée, Objet du crédit, Biens).

| variable | information_value | force |
|---|---|---|
| Compte courant | 0.66 | très forte |
| Historique de crédit | 0.29 | moyenne |
| Épargne | 0.19 | moyenne |
| Durée | 0.18 | moyenne |
| Objet du crédit | 0.17 | moyenne |
| Biens | 0.11 | moyenne |
| Montant | 0.1 | faible |
| Âge | 0.09 | faible |
| Ancienneté emploi | 0.09 | faible |
| Logement | 0.08 | faible |
| Autres crédits | 0.06 | faible |

**Lecture.** Une IV supérieure à 0,5 est normalement un signal d'alarme (fuite possible) ; ici elle s'explique : le statut du compte courant est une information bancaire déjà connue au moment de la demande. Les variables sociodémographiques (âge, logement, emploi) pèsent peu (IV < 0,1) : le comportement bancaire passé prime sur le profil.

**Décision / action.** Construire le scorecard en priorité sur compte courant, historique, épargne, durée et objet du crédit.

**Limite.** IV calculée sur l'échantillon complet (sans hors-échantillon) : elle surestime légèrement ; le modèle ML est validé en validation croisée.

## Marketing bancaire

### M01 — Campagnes de dépôt à terme : qui accepte ?

**Question.** Quel est le taux de conversion global, et par canal, par métier, par statut précédent ? (échantillon de 2 999 contacts)

**Réponse.** Le taux de conversion global est de 11,0 %. Il atteint 65,3 % chez les clients déjà convertis à une campagne précédente (contre 8,4 % sans historique) et 14,0 % sur mobile contre 5,6 % sur fixe.

| dimension | modalite | contacts | souscriptions | taux_conversion_pct |
|---|---|---|---|---|
| Campagne précédente | success | 101 | 66 | 65.3 |
| Campagne précédente | failure | 331 | 49 | 14.8 |
| Campagne précédente | nonexistent | 2 567 | 216 | 8.4 |
| Canal | cellular | 1 935 | 271 | 14 |
| Canal | telephone | 1 064 | 60 | 5.6 |
| Global | tous contacts | 2 999 | 331 | 11 |
| Métier | retired | 118 | 27 | 22.9 |
| Métier | student | 58 | 12 | 20.7 |
| Métier | unemployed | 85 | 14 | 16.5 |
| Métier | admin. | 743 | 98 | 13.2 |
| Métier | technician | 496 | 61 | 12.3 |
| Métier | services | 294 | 26 | 8.8 |
| Métier | housemaid | 70 | 6 | 8.6 |
| Métier | management | 233 | 19 | 8.2 |
| Métier | blue-collar | 644 | 50 | 7.8 |
| Métier | entrepreneur | 112 | 8 | 7.1 |
| Métier | self-employed | 114 | 7 | 6.1 |
| Tranche d'âge | 60+ | 72 | 25 | 34.7 |
| Tranche d'âge | 50-59 | 524 | 66 | 12.6 |
| Tranche d'âge | <30 | 422 | 48 | 11.4 |
| Tranche d'âge | 30-39 | 1 243 | 131 | 10.5 |
| Tranche d'âge | 40-49 | 738 | 61 | 8.3 |

**Lecture.** Le meilleur prédicteur d'une souscription est une souscription passée ; le mobile convertit 2,5 fois mieux que le fixe (raison à investiguer : profil des clients joints ou période de la campagne). Retraités, étudiants et plus de 60 ans convertissent le plus, les indépendants le moins.

**Décision / action.** Prioriser dans les listes d'appel : 1) anciens souscripteurs, 2) contacts mobiles, 3) seniors. Tester avant de généraliser la préférence pour le mobile.

**Limite.** Échantillon de 2 999 contacts (7 % du jeu complet) : les modalités à moins de 100 contacts ne sont pas fiables ; le canal et la période sont confondus.

### M02 — Insister paie-t-il ?

**Question.** Au-delà de quel nombre d'appels la conversion s'effondre-t-elle ? (rendement décroissant)

**Réponse.** Le rendement s'effondre avec l'insistance : 12,9 % au premier appel, 11,4 % à 2-3 appels, 7,8 % à 4-6, 2,3 % au-delà de 6.

| pression | contacts | souscriptions | taux_conversion_pct |
|---|---|---|---|
| 1 contact | 1 307 | 168 | 12.9 |
| 2-3 contacts | 1 136 | 129 | 11.4 |
| 4-6 contacts | 384 | 30 | 7.8 |
| 7+ contacts | 172 | 4 | 2.3 |

**Lecture.** Au-delà de 6 appels le rendement est divisé par 5,6 par rapport au premier appel, alors que chaque appel coûte le même temps de conseiller ; risque de réclamation en plus.

**Décision / action.** Plafonner à 3 appels par contact dans la campagne et réaffecter le temps des conseillers vers de nouveaux contacts.

**Limite.** Les contacts très sollicités ne sont pas tirés au hasard (sélection : on réappelle ceux qui n'ont pas dit non d'emblée).

### M03 — Le contexte de taux change tout

**Question.** La conversion dépend-elle du niveau de l'Euribor 3 mois au moment de l'appel ?

**Réponse.** Quand l'Euribor 3 mois est sous 1 %, 42 % des contacts souscrivent ; au-dessus de 3 %, seulement 5,5 % (7,7 fois moins).

| contexte_taux | contacts | souscriptions | taux_conversion_pct | euribor_moyen |
|---|---|---|---|---|
| 1-euribor <1 % | 292 | 124 | 42.5 | 0.8 |
| 2-euribor 1-3 % | 699 | 97 | 13.9 | 1.31 |
| 3-euribor 3 %+ | 2 008 | 110 | 5.5 | 4.81 |

**Lecture.** Le sens est contre-intuitif (taux bas = plus de souscriptions). Euribor et date de campagne sont confondus : la variable capte surtout la période (2009-2010, crise financière, fuite vers les placements sûrs) ; on ne peut pas parler d'effet causal du taux. Le contexte pèse néanmoins plus que n'importe quelle caractéristique du client.

**Décision / action.** Piloter la campagne par le calendrier de taux (lancer quand le contexte est favorable) et corriger les comparaisons de performance entre périodes par le niveau de l'Euribor.

**Limite.** Variable macroéconomique commune à tous les contacts d'une période : elle ne distingue pas les clients entre eux.

### M04 — La durée de l'appel : un faux ami prédictif

**Question.** La durée de l'appel est très liée à la souscription. Peut-on l'utiliser pour cibler les clients ?

**Réponse.** La conversion grimpe de 0 % (appel de moins d'une minute) à 37 % (appels de plus de 7 minutes) : la durée semble être le meilleur prédicteur.

| duree_appel | contacts | souscriptions | taux_conversion_pct |
|---|---|---|---|
| 1-<1 min | 310 | 0 | 0 |
| 2-1-3 min | 1 183 | 39 | 3.3 |
| 3-3-7 min | 997 | 103 | 10.3 |
| 4-7 min + | 509 | 189 | 37.1 |

**Lecture.** C'est un piège : la durée n'est connue qu'à la fin de l'appel, donc il est impossible de s'en servir pour choisir qui appeler. Un client qui souscrit reste logiquement plus longtemps en ligne (cause inversée). Le module ML montre l'AUC qui monte à 0,93 avec la durée (irréaliste) contre 0,75 sans (utilisable).

**Décision / action.** Exclure la durée de tout modèle de ciblage ; l'utiliser seulement pour évaluer la qualité des appels a posteriori.

**Limite.** Même la source UCI recommande d'écarter cette variable pour un modèle prédictif réaliste.
