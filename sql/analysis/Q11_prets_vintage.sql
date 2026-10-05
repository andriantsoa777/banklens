-- id: Q11
-- domain: banque
-- title: Défaut par année d'octroi (analyse de vintage) et biais de censure
-- question: Les prêts récents sont-ils meilleurs ou simplement trop jeunes pour avoir fait défaut ?
-- grain: 1 ligne par année d'octroi
SELECT d.year AS annee_octroi, COUNT(*) AS prets, SUM(l.is_default) AS defauts,
       ROUND(100.0 * AVG(l.is_default), 1) AS taux_defaut_pct,
       ROUND(100.0 * SUM(l.lifecycle = 'en cours') / COUNT(*), 1) AS pct_encore_en_cours,
       ROUND(AVG(l.amount), 0) AS montant_moyen
FROM fact_loan l JOIN dim_date d ON d.date_key = l.granted_date_key
GROUP BY d.year ORDER BY d.year;
