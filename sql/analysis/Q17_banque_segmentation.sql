-- id: Q17
-- domain: banque
-- title: Segmentation comportementale des comptes
-- question: Peut-on regrouper les comptes en segments actionnables pour le marketing et la gestion du risque ?
-- grain: 1 ligne par segment (règles métier explicites, pas une boîte noire)
WITH s AS (
  SELECT a.account_key, a.owner_age, a.has_loan, f.closing_balance AS solde,
         (SELECT AVG(n_tx) FROM fact_account_month x WHERE x.account_key = a.account_key AND x.year_month BETWEEN '1998-01' AND '1998-12') AS tx_mois,
         (SELECT SUM(had_overdraft) FROM fact_account_month x WHERE x.account_key = a.account_key AND x.year_month BETWEEN '1998-01' AND '1998-12') AS mois_decouvert
  FROM dim_account a JOIN fact_account_month f ON f.account_key = a.account_key AND f.year_month = '1998-12'),
seg AS (
  SELECT *, CASE WHEN mois_decouvert >= 3 THEN '5-À surveiller (découvert récurrent)'
                 WHEN solde >= 80000 THEN '1-Premium (solde >= 80 k)'
                 WHEN owner_age >= 60 THEN '4-Seniors (60 ans et +)'
                 WHEN tx_mois >= 8 THEN '2-Actifs (8 opérations/mois et +, top 10 %)'
                 ELSE '3-Courants' END AS segment FROM s)
SELECT segment, COUNT(*) AS comptes, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_comptes_pct,
       ROUND(SUM(MAX(solde, 0)) / 1e6, 1) AS encours_m, ROUND(AVG(solde), 0) AS solde_moyen,
       ROUND(AVG(tx_mois), 1) AS tx_par_mois, ROUND(100.0 * AVG(has_loan), 1) AS pct_avec_pret
FROM seg GROUP BY segment ORDER BY segment;
