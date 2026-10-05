-- id: Q10
-- domain: banque
-- title: Quels prêts font défaut ?
-- question: Le défaut dépend-il du montant, de la durée, de la région (chômage), de l'âge de l'emprunteur ?
-- grain: 1 ligne par (dimension, modalité)
WITH base AS (
  SELECT l.loan_key, l.is_default, l.amount_band, l.duration_months, a.owner_age_band, d.unemployment_band, d.region, l.amount
  FROM fact_loan l JOIN dim_account a USING (account_key) JOIN dim_district d ON d.district_key = a.district_key)
SELECT 'Montant' AS dimension, amount_band AS modalite, COUNT(*) AS prets, SUM(is_default) AS defauts, ROUND(100.0 * AVG(is_default), 1) AS taux_defaut_pct FROM base GROUP BY amount_band
UNION ALL SELECT 'Durée', duration_months || ' mois', COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM base GROUP BY duration_months
UNION ALL SELECT 'Âge', owner_age_band, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM base GROUP BY owner_age_band
UNION ALL SELECT 'Chômage du district', unemployment_band, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM base GROUP BY unemployment_band
ORDER BY dimension, modalite;
