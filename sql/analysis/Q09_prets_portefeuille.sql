-- id: Q09
-- domain: banque
-- title: Le portefeuille de prêts et son taux de défaut
-- question: Combien de prêts, pour quel montant, et quelle part est en défaut (terminé non remboursé ou en cours en impayé) ?
-- grain: 1 ligne par statut de prêt
SELECT status_code AS statut, status_label AS libelle, COUNT(*) AS prets,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_prets_pct,
       ROUND(SUM(amount) / 1e6, 1) AS montant_m,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1) AS part_montant_pct,
       ROUND(AVG(amount), 0) AS montant_moyen,
       ROUND(AVG(duration_months), 1) AS duree_moyenne_mois
FROM fact_loan GROUP BY status_code, status_label ORDER BY status_code;
