-- id: Q18
-- domain: banque
-- title: Ordres permanents et équipement des comptes
-- question: Quels engagements récurrents les clients ont-ils confiés à la banque (loyer/énergie, assurance, leasing, prêt) ?
-- grain: 1 ligne par objet d'ordre permanent
SELECT CASE purpose WHEN 'household_payment' THEN 'Loyer, énergie, charges (SIPO)' WHEN 'loan_repayment' THEN 'Remboursement de prêt' WHEN 'insurance' THEN 'Assurance' WHEN 'leasing' THEN 'Leasing' ELSE 'Non précisé' END AS objet, COUNT(*) AS ordres, COUNT(DISTINCT account_key) AS comptes,
       ROUND(100.0 * COUNT(DISTINCT account_key) / (SELECT COUNT(*) FROM dim_account), 1) AS pct_des_comptes,
       ROUND(AVG(amount), 0) AS montant_moyen, ROUND(SUM(amount) / 1e6, 2) AS total_mensuel_m
FROM fact_standing_order GROUP BY purpose ORDER BY ordres DESC;
