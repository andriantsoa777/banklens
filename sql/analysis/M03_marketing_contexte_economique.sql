-- id: M03
-- domain: marketing
-- title: Le contexte de taux change tout
-- question: La conversion dépend-elle du niveau de l'Euribor 3 mois au moment de l'appel ?
-- grain: 1 ligne par bande d'Euribor
SELECT euribor_band AS contexte_taux, COUNT(*) AS contacts, SUM(subscribed) AS souscriptions,
       ROUND(100.0 * AVG(subscribed), 1) AS taux_conversion_pct, ROUND(AVG(euribor3m), 2) AS euribor_moyen
FROM fact_marketing_contact GROUP BY euribor_band ORDER BY euribor_band;
