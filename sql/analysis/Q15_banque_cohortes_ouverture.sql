-- id: Q15
-- domain: banque
-- title: Cohortes d'ouverture de compte
-- question: Les comptes ouverts en 1993 se comportent-ils comme ceux de 1997 ? Quel solde et quelle activité après 12 et 24 mois ?
-- grain: 1 ligne par année d'ouverture
WITH m AS (
  SELECT a.opening_year, f.account_key, f.year_month, f.closing_balance, f.n_tx,
         (CAST(substr(f.year_month, 1, 4) AS INT) - CAST(substr(a.opened_on, 1, 4) AS INT)) * 12
         + CAST(substr(f.year_month, 6, 2) AS INT) - CAST(substr(a.opened_on, 6, 2) AS INT) AS age_mois
  FROM fact_account_month f JOIN dim_account a USING (account_key))
SELECT opening_year AS annee_ouverture, COUNT(DISTINCT account_key) AS comptes,
       ROUND(AVG(CASE WHEN age_mois = 12 THEN closing_balance END), 0) AS solde_moyen_12m,
       ROUND(AVG(CASE WHEN age_mois = 24 THEN closing_balance END), 0) AS solde_moyen_24m,
       ROUND(AVG(CASE WHEN age_mois = 12 THEN n_tx END), 1) AS tx_mois_12m,
       ROUND(AVG(CASE WHEN age_mois = 24 THEN n_tx END), 1) AS tx_mois_24m
FROM m GROUP BY opening_year ORDER BY opening_year;
