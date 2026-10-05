-- id: Q03
-- domain: banque
-- title: Qui sont les titulaires de compte ?
-- question: Quel est le profil des titulaires (sexe, âge) et quelle part équipe-t-on en carte et en prêt ?
-- grain: 1 ligne par tranche d'âge
SELECT owner_age_band AS tranche_age,
       COUNT(*) AS comptes,
       ROUND(100.0 * SUM(owner_gender = 'F') / COUNT(*), 1) AS pct_femmes,
       ROUND(100.0 * SUM(best_card_type <> 'none') / COUNT(*), 1) AS pct_avec_carte,
       ROUND(100.0 * SUM(has_loan) / COUNT(*), 1) AS pct_avec_pret,
       ROUND(AVG(f.closing_balance), 0) AS solde_moyen_1998
FROM dim_account a
JOIN fact_account_month f ON f.account_key = a.account_key AND f.year_month = '1998-12'
GROUP BY owner_age_band ORDER BY owner_age_band;
