-- id: Q08
-- domain: banque
-- title: Cartes : pénétration et effet sur les usages
-- question: Quelle part des comptes a une carte ? Les détenteurs vont-ils moins souvent au guichet ?
-- grain: 1 ligne par type de carte (meilleure carte du compte)
WITH usage AS (
  SELECT account_key, SUM(n_tx) AS tx, SUM(n_cash_tx) AS guichet_tx, SUM(n_card_tx) AS card_tx, COUNT(*) AS months
  FROM fact_account_month GROUP BY account_key)
SELECT a.best_card_type AS carte, COUNT(*) AS comptes,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_comptes_pct,
       ROUND(AVG(1.0 * u.tx / u.months), 2) AS tx_par_mois,
       ROUND(AVG(1.0 * u.guichet_tx / u.months), 2) AS passages_guichet_par_mois,
       ROUND(AVG(1.0 * u.card_tx / u.months), 2) AS retraits_carte_par_mois,
       ROUND(AVG(a.owner_age), 1) AS age_moyen
FROM dim_account a JOIN usage u USING (account_key)
GROUP BY a.best_card_type ORDER BY comptes DESC;
