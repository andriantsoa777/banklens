-- id: G01
-- domain: credit
-- title: Scoring de crédit : qui fait défaut ?
-- question: Quels profils d'emprunteurs ont les plus forts taux de défaut ? (1 000 dossiers du jeu UCI Statlog German Credit)
-- grain: 1 ligne par (variable, modalité)
SELECT 'Compte courant' AS variable, checking_balance AS modalite, COUNT(*) AS dossiers, SUM(is_default) AS defauts, ROUND(100.0 * AVG(is_default), 1) AS taux_defaut_pct FROM fact_credit_application GROUP BY checking_balance
UNION ALL SELECT 'Historique de crédit', credit_history, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM fact_credit_application GROUP BY credit_history
UNION ALL SELECT 'Durée', duration_band, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM fact_credit_application GROUP BY duration_band
UNION ALL SELECT 'Montant (DM)', amount_band, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM fact_credit_application GROUP BY amount_band
UNION ALL SELECT 'Épargne', savings_balance, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM fact_credit_application GROUP BY savings_balance
UNION ALL SELECT 'Âge', age_band, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM fact_credit_application GROUP BY age_band
UNION ALL SELECT 'Logement', housing, COUNT(*), SUM(is_default), ROUND(100.0 * AVG(is_default), 1) FROM fact_credit_application GROUP BY housing
ORDER BY variable, taux_defaut_pct DESC;
