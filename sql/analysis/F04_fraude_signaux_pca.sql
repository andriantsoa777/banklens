-- id: F04
-- domain: fraude
-- title: Quelles variables séparent le mieux fraude et légitime ?
-- question: Parmi les composantes anonymisées V1-V28, lesquelles se comportent le plus différemment en cas de fraude ?
-- grain: 1 ligne par variable (écart standardisé : différence des moyennes / écart-type global)
-- note: les variables sont déjà une ACP fournie par la source : on ne peut pas dire ce qu'elles "signifient", seulement qu'elles discriminent.
WITH v AS (
  SELECT 'V14' AS variable, v14 AS x, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V17', v17, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V12', v12, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V10', v10, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V4', v4, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V11', v11, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V3', v3, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V7', v7, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V16', v16, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)
  UNION ALL SELECT 'V2', v2, is_fraud FROM fact_card_tx_features JOIN fact_card_tx USING (transaction_key)),
st AS (
  SELECT variable, AVG(x) AS mu, AVG(x * x) - AVG(x) * AVG(x) AS var_all,
         AVG(CASE WHEN is_fraud = 1 THEN x END) AS mu_f, AVG(CASE WHEN is_fraud = 0 THEN x END) AS mu_l
  FROM v GROUP BY variable)
SELECT variable, ROUND(mu_l, 2) AS moyenne_legitime, ROUND(mu_f, 2) AS moyenne_fraude,
       ROUND((mu_f - mu_l) / sqrt(var_all), 2) AS ecart_standardise
FROM st ORDER BY ABS((mu_f - mu_l) / sqrt(var_all)) DESC;
