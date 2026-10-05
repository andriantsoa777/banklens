-- id: M02
-- domain: marketing
-- title: Insister paie-t-il ?
-- question: Au-delà de quel nombre d'appels la conversion s'effondre-t-elle ? (rendement décroissant)
-- grain: 1 ligne par niveau de pression
SELECT pressure_band AS pression, COUNT(*) AS contacts, SUM(subscribed) AS souscriptions,
       ROUND(100.0 * AVG(subscribed), 1) AS taux_conversion_pct
FROM fact_marketing_contact GROUP BY pressure_band ORDER BY MIN(campaign_contacts);
