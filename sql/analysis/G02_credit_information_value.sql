-- id: G02
-- domain: credit
-- title: Information Value : quelles variables pèsent le plus dans un scorecard ?
-- question: Quelle est la force prédictive de chaque variable (méthode WoE / IV, standard en risque de crédit) ?
-- grain: 1 ligne par variable
-- lecture IV : < 0,02 inutile ; 0,02-0,1 faible ; 0,1-0,3 moyenne ; 0,3-0,5 forte ; > 0,5 très forte (à vérifier : fuite de données possible)
WITH cats AS (
  SELECT 'Compte courant' AS variable, checking_balance AS modalite, is_default FROM fact_credit_application
  UNION ALL SELECT 'Historique de crédit', credit_history, is_default FROM fact_credit_application
  UNION ALL SELECT 'Épargne', savings_balance, is_default FROM fact_credit_application
  UNION ALL SELECT 'Objet du crédit', purpose, is_default FROM fact_credit_application
  UNION ALL SELECT 'Durée', duration_band, is_default FROM fact_credit_application
  UNION ALL SELECT 'Montant', amount_band, is_default FROM fact_credit_application
  UNION ALL SELECT 'Ancienneté emploi', employment_length, is_default FROM fact_credit_application
  UNION ALL SELECT 'Logement', housing, is_default FROM fact_credit_application
  UNION ALL SELECT 'Âge', age_band, is_default FROM fact_credit_application
  UNION ALL SELECT 'Biens', property, is_default FROM fact_credit_application
  UNION ALL SELECT 'Autres crédits', other_installment_plans, is_default FROM fact_credit_application),
g AS (SELECT variable, modalite, SUM(1 - is_default) AS good, SUM(is_default) AS bad FROM cats GROUP BY variable, modalite),
t AS (SELECT variable, SUM(good) AS tg, SUM(bad) AS tb FROM g GROUP BY variable),
w AS (SELECT g.variable, (g.good + 0.5) / (t.tg + 0.5) AS pg, (g.bad + 0.5) / (t.tb + 0.5) AS pb FROM g JOIN t USING (variable))
SELECT variable, ROUND(SUM((pg - pb) * ln(pg / pb)), 3) AS information_value,
       CASE WHEN SUM((pg - pb) * ln(pg / pb)) < 0.02 THEN 'inutile' WHEN SUM((pg - pb) * ln(pg / pb)) < 0.1 THEN 'faible'
            WHEN SUM((pg - pb) * ln(pg / pb)) < 0.3 THEN 'moyenne' WHEN SUM((pg - pb) * ln(pg / pb)) < 0.5 THEN 'forte' ELSE 'très forte' END AS force
FROM w GROUP BY variable ORDER BY information_value DESC;
