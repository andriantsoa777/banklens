-- id: F01
-- domain: fraude
-- title: Fraude carte : l'ampleur du problème
-- question: Quelle part des transactions et des montants est frauduleuse ? (après suppression des doublons exacts)
-- grain: 1 ligne par classe
SELECT CASE is_fraud WHEN 1 THEN 'Fraude' ELSE 'Légitime' END AS classe,
       COUNT(*) AS transactions,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 3) AS part_transactions_pct,
       ROUND(SUM(amount), 0) AS montant_total,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 3) AS part_montant_pct,
       ROUND(AVG(amount), 1) AS montant_moyen,
       ROUND(MAX(amount), 0) AS montant_max
FROM fact_card_tx GROUP BY is_fraud ORDER BY is_fraud DESC;
