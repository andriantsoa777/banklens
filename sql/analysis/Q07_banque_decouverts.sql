-- id: Q07
-- domain: banque
-- title: Découverts : combien, qui, et à quel point
-- question: Quelle part des comptes passe en négatif ? Le phénomène est-il récurrent ou accidentel ? Qui est concerné ?
-- grain: 1 ligne par intensité de découvert
WITH per_acc AS (
  SELECT account_key, SUM(had_overdraft) AS mois_en_decouvert, COUNT(*) AS mois_observes, MIN(min_balance) AS pire_solde
  FROM fact_account_month GROUP BY account_key)
SELECT CASE WHEN mois_en_decouvert = 0 THEN '0-jamais à découvert'
            WHEN mois_en_decouvert <= 2 THEN '1-accidentel (1-2 mois)'
            WHEN mois_en_decouvert <= 6 THEN '2-récurrent (3-6 mois)' ELSE '3-chronique (7 mois ou plus)' END AS profil,
       COUNT(*) AS comptes,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct,
       ROUND(AVG(pire_solde), 0) AS pire_solde_moyen,
       ROUND(100.0 * SUM(a.has_loan) / COUNT(*), 1) AS pct_avec_pret,
       ROUND(AVG(a.owner_age), 1) AS age_moyen
FROM per_acc p JOIN dim_account a USING (account_key)
GROUP BY profil ORDER BY profil;
