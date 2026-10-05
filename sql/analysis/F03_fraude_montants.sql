-- id: F03
-- domain: fraude
-- title: Montants : les fraudeurs testent-ils les cartes avec de petits achats ?
-- question: Comment se répartissent les montants des fraudes comparés aux transactions légitimes ?
-- grain: 1 ligne par tranche de montant
SELECT amount_band AS tranche_montant,
       COUNT(*) AS transactions, SUM(is_fraud) AS fraudes,
       ROUND(100.0 * SUM(is_fraud) / SUM(SUM(is_fraud)) OVER (), 1) AS part_des_fraudes_pct,
       ROUND(100.0 * (COUNT(*) - SUM(is_fraud)) / SUM(COUNT(*) - SUM(is_fraud)) OVER (), 1) AS part_des_legitimes_pct,
       ROUND(10000.0 * AVG(is_fraud), 1) AS fraudes_pour_10000
FROM fact_card_tx GROUP BY amount_band, amount_band_order ORDER BY amount_band_order;
