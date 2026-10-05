-- id: Q13
-- domain: banque
-- title: Revenus et coûts observables dans les données
-- question: Que gagne la banque en frais et pénalités, que verse-t-elle en intérêts, et à quel taux implicite rémunère-t-elle les dépôts ?
-- grain: 1 ligne par année
-- limite: les mensualités de prêt valent exactement capital / durée (aucun intérêt n'est enregistré) ; ni marge d'intermédiation,
--         ni coût du risque, ni refinancement n'existent dans les données. Périmètre partiel et assumé.
WITH tx AS (
  SELECT d.year AS annee,
         SUM(CASE WHEN t.category = 'statement_fee' THEN f.amount ELSE 0 END) AS frais_releve,
         SUM(CASE WHEN t.category = 'overdraft_interest' THEN f.amount ELSE 0 END) AS interets_penalite,
         SUM(CASE WHEN t.category = 'interest_credited' THEN f.amount ELSE 0 END) AS interets_verses
  FROM fact_transaction f JOIN dim_tx_type t USING (tx_type_key) JOIN dim_date d USING (date_key)
  GROUP BY d.year),
dep AS (
  SELECT CAST(substr(year_month, 1, 4) AS INT) AS annee, SUM(closing_balance) / COUNT(DISTINCT year_month) AS encours_moyen
  FROM fact_account_month GROUP BY 1)
SELECT tx.annee,
       ROUND(frais_releve / 1e3, 0) AS frais_releve_k,
       ROUND(interets_penalite / 1e3, 0) AS interets_penalite_k,
       ROUND(interets_verses / 1e3, 0) AS interets_verses_k,
       ROUND(dep.encours_moyen / 1e6, 1) AS encours_moyen_m,
       ROUND(100.0 * interets_verses / dep.encours_moyen, 2) AS taux_servi_implicite_pct
FROM tx JOIN dep USING (annee) ORDER BY tx.annee;
