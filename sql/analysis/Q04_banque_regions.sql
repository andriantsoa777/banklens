-- id: Q04
-- domain: banque
-- title: Géographie des comptes et des soldes
-- question: Quelles régions concentrent les comptes et les dépôts, et le solde moyen suit-il le niveau de salaire local ?
-- grain: 1 ligne par région
SELECT d.region,
       COUNT(*) AS comptes,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_comptes_pct,
       ROUND(SUM(f.closing_balance) / 1e6, 1) AS encours_m,
       ROUND(100.0 * SUM(f.closing_balance) / SUM(SUM(f.closing_balance)) OVER (), 1) AS part_encours_pct,
       ROUND(AVG(f.closing_balance), 0) AS solde_moyen,
       ROUND(AVG(d.avg_salary), 0) AS salaire_moyen_district,
       ROUND(AVG(d.unemployment_1996), 2) AS chomage_1996_pct
FROM dim_account a
JOIN dim_district d ON d.district_key = a.district_key
JOIN fact_account_month f ON f.account_key = a.account_key AND f.year_month = '1998-12'
GROUP BY d.region ORDER BY comptes DESC;
