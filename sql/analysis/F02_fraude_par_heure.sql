-- id: F02
-- domain: fraude
-- title: Fraude et heure de la journée
-- question: La fraude est-elle plus fréquente à certaines heures ? Quelles fenêtres de risque surveiller ?
-- grain: 1 ligne par heure (les deux jours sont cumulés ; l'heure est relative au début du jeu, pas à un fuseau)
SELECT h.hour_key AS heure, h.daypart AS tranche,
       COUNT(*) AS transactions, SUM(f.is_fraud) AS fraudes,
       ROUND(10000.0 * AVG(f.is_fraud), 1) AS fraudes_pour_10000
FROM fact_card_tx f JOIN dim_hour h USING (hour_key)
GROUP BY h.hour_key, h.daypart ORDER BY h.hour_key;
