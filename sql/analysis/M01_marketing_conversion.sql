-- id: M01
-- domain: marketing
-- title: Campagnes de dépôt à terme : qui accepte ?
-- question: Quel est le taux de conversion global, et par canal, par métier, par statut précédent ? (échantillon de 2 999 contacts)
-- grain: 1 ligne par (dimension, modalité)
SELECT 'Global' AS dimension, 'tous contacts' AS modalite, COUNT(*) AS contacts, SUM(subscribed) AS souscriptions, ROUND(100.0 * AVG(subscribed), 1) AS taux_conversion_pct FROM fact_marketing_contact
UNION ALL SELECT 'Canal', contact_channel, COUNT(*), SUM(subscribed), ROUND(100.0 * AVG(subscribed), 1) FROM fact_marketing_contact GROUP BY contact_channel
UNION ALL SELECT 'Campagne précédente', COALESCE(previous_outcome, 'n/a'), COUNT(*), SUM(subscribed), ROUND(100.0 * AVG(subscribed), 1) FROM fact_marketing_contact GROUP BY previous_outcome
UNION ALL SELECT 'Métier', job, COUNT(*), SUM(subscribed), ROUND(100.0 * AVG(subscribed), 1) FROM fact_marketing_contact WHERE job IS NOT NULL GROUP BY job HAVING COUNT(*) >= 50
UNION ALL SELECT 'Tranche d''âge', age_band, COUNT(*), SUM(subscribed), ROUND(100.0 * AVG(subscribed), 1) FROM fact_marketing_contact GROUP BY age_band
ORDER BY dimension, taux_conversion_pct DESC;
