-- id: Q16
-- domain: banque
-- title: Saisonnalité : le pic de janvier
-- question: Existe-t-il des mois ou des jours où l'activité explose ? Quelles opérations expliquent le pic ?
-- grain: 1 ligne par mois calendaire (années complètes 1994-1997)
SELECT d.month AS mois,
       COUNT(*) AS operations,
       ROUND(100.0 * COUNT(*) / AVG(COUNT(*)) OVER (), 0) AS indice_activite_100,
       SUM(CASE WHEN t.channel = 'Espèces (guichet)' AND t.direction = 'debit' THEN 1 ELSE 0 END) AS retraits_guichet,
       ROUND(SUM(CASE WHEN f.signed_amount < 0 THEN -f.signed_amount ELSE 0 END) / 1e6, 1) AS sorties_m,
       ROUND(100.0 * SUM(CASE WHEN t.channel = 'Espèces (guichet)' AND t.direction = 'debit' THEN 1 ELSE 0 END) / COUNT(*), 1) AS part_retraits_pct
FROM fact_transaction f JOIN dim_date d USING (date_key) JOIN dim_tx_type t USING (tx_type_key)
WHERE d.year BETWEEN 1994 AND 1997 GROUP BY d.month ORDER BY d.month;
