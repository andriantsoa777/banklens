-- id: Q02
-- domain: banque
-- title: Évolution mensuelle de l'activité et des dépôts
-- question: La banque grossit-elle ? Comment évoluent le nombre de comptes actifs, les flux et l'encours de dépôts mois après mois ?
-- grain: 1 ligne par mois
SELECT year_month,
       COUNT(*) AS comptes_ouverts,
       SUM(CASE WHEN n_tx > 0 THEN 1 ELSE 0 END) AS comptes_actifs,
       SUM(n_tx) AS transactions,
       ROUND(SUM(credits) / 1e6, 2) AS entrees_m,
       ROUND(SUM(debits) / 1e6, 2) AS sorties_m,
       ROUND((SUM(credits) - SUM(debits)) / 1e6, 2) AS flux_net_m,
       ROUND(SUM(closing_balance) / 1e6, 1) AS encours_m
FROM fact_account_month
GROUP BY year_month ORDER BY year_month;
