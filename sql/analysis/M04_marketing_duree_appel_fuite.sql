-- id: M04
-- domain: marketing
-- title: La durée de l'appel : un faux ami prédictif
-- question: La durée de l'appel est très liée à la souscription. Peut-on l'utiliser pour cibler les clients ?
-- grain: 1 ligne par tranche de durée
-- réponse attendue : NON. La durée n'est connue qu'APRÈS l'appel (fuite de données) : elle sert à comprendre, pas à prédire.
SELECT duration_band AS duree_appel, COUNT(*) AS contacts, SUM(subscribed) AS souscriptions,
       ROUND(100.0 * AVG(subscribed), 1) AS taux_conversion_pct
FROM fact_marketing_contact GROUP BY duration_band ORDER BY duration_band;
