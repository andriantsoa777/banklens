-- id: Q14
-- domain: banque
-- title: Concentration des dépôts
-- question: Quelle part de l'encours détiennent les 1 %, 10 % et 20 % de comptes les plus riches ?
-- grain: 1 ligne par seuil de concentration
WITH ranked AS (
  SELECT closing_balance AS bal, ROW_NUMBER() OVER (ORDER BY closing_balance DESC) AS rk, COUNT(*) OVER () AS n,
         SUM(MAX(closing_balance, 0)) OVER () AS total
  FROM fact_account_month WHERE year_month = '1998-12')
SELECT CASE WHEN rk <= n * 0.01 THEN 'a-1 % des comptes' WHEN rk <= n * 0.10 THEN 'b-10 % des comptes' ELSE 'c-90 % restants' END AS segment_riche,
       COUNT(*) AS comptes, ROUND(SUM(MAX(bal, 0)) / 1e6, 1) AS encours_m,
       ROUND(100.0 * SUM(MAX(bal, 0)) / MAX(total), 1) AS part_encours_pct, ROUND(AVG(bal), 0) AS solde_moyen
FROM ranked GROUP BY segment_riche ORDER BY segment_riche;
