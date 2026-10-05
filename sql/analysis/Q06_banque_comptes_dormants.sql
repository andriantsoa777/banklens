-- id: Q06
-- domain: banque
-- title: Comptes dormants et attrition silencieuse
-- question: Combien de comptes ont cessé toute activité avant la fin de la période observée ? Qui sont-ils ?
-- grain: 1 ligne par statut d'activité
WITH last_tx AS (SELECT account_key, MAX(date_key) AS last_date_key, COUNT(*) AS n FROM fact_transaction GROUP BY account_key),
     lab AS (
       SELECT a.account_key, a.owner_age_band, a.has_loan, a.best_card_type, l.n,
              CASE WHEN l.last_date_key >= 19981001 THEN 'Actif (opération depuis oct. 1998)'
                   WHEN l.last_date_key >= 19980701 THEN 'Ralenti (dernière opération juil.-sept. 1998)'
                   ELSE 'Dormant (aucune opération depuis juil. 1998)' END AS statut
       FROM dim_account a JOIN last_tx l USING (account_key))
SELECT statut, COUNT(*) AS comptes, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct,
       ROUND(AVG(n), 0) AS transactions_moyennes,
       ROUND(100.0 * SUM(has_loan) / COUNT(*), 1) AS pct_avec_pret,
       ROUND(100.0 * SUM(best_card_type <> 'none') / COUNT(*), 1) AS pct_avec_carte
FROM lab GROUP BY statut ORDER BY statut;
