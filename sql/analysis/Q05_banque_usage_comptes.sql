-- id: Q05
-- domain: banque
-- title: Comment les clients utilisent leur compte
-- question: Quelle part des opérations passe par les espèces au guichet, la carte, les virements ? Qu'est-ce qui entre, qu'est-ce qui sort ?
-- grain: 1 ligne par canal x sens
SELECT t.channel AS canal, t.direction AS sens,
       COUNT(*) AS operations,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_operations_pct,
       ROUND(SUM(f.amount) / 1e6, 1) AS montant_m,
       ROUND(100.0 * SUM(f.amount) / SUM(SUM(f.amount)) OVER (), 1) AS part_montant_pct,
       ROUND(AVG(f.amount), 0) AS montant_moyen
FROM fact_transaction f JOIN dim_tx_type t USING (tx_type_key)
GROUP BY t.channel, t.direction ORDER BY montant_m DESC;
