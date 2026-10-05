-- id: Q12
-- domain: banque
-- title: Signaux d'alerte AVANT l'octroi
-- question: Que savait-on sur le compte dans les 6 mois précédant le prêt qui aurait permis de prévoir le défaut ?
-- grain: 1 ligne par bande de taux d'effort (mensualité / entrées mensuelles moyennes)
SELECT CASE WHEN payment_to_inflow_ratio < 0.10 THEN '1-effort < 10 %'
            WHEN payment_to_inflow_ratio < 0.20 THEN '2-effort 10-20 %'
            WHEN payment_to_inflow_ratio < 0.35 THEN '3-effort 20-35 %'
            ELSE '4-effort 35 % et plus' END AS taux_effort,
       COUNT(*) AS prets, SUM(is_default) AS defauts,
       ROUND(100.0 * AVG(is_default), 1) AS taux_defaut_pct,
       ROUND(AVG(pre_avg_balance_6m), 0) AS solde_moyen_avant,
       ROUND(AVG(pre_overdraft_months_6m), 2) AS mois_decouvert_avant
FROM fact_loan WHERE payment_to_inflow_ratio IS NOT NULL
GROUP BY taux_effort ORDER BY taux_effort;
