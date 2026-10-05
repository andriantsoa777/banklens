-- ============================================================================
-- GOLD / dimensions. Clés de substitution = clés métier stables (source unique, pas de SCD nécessaire :
-- les dimensions Berka sont des photos 1998). Les dimensions "bande" sont figées ici, jamais recalculées en BI.
-- ============================================================================
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
WITH RECURSIVE d(dt) AS (
  SELECT '1993-01-01' UNION ALL SELECT date(dt, '+1 day') FROM d WHERE dt < '1998-12-31')
SELECT CAST(strftime('%Y%m%d', dt) AS INTEGER) AS date_key,
       dt AS full_date,
       CAST(strftime('%Y', dt) AS INTEGER) AS year,
       (CAST(strftime('%m', dt) AS INTEGER) + 2) / 3 AS quarter,
       CAST(strftime('%m', dt) AS INTEGER) AS month,
       strftime('%Y-%m', dt) AS year_month,
       CAST(strftime('%w', dt) AS INTEGER) AS weekday_num,         -- 0 = dimanche
       CASE strftime('%w', dt) WHEN '0' THEN 'dimanche' WHEN '1' THEN 'lundi' WHEN '2' THEN 'mardi' WHEN '3' THEN 'mercredi'
            WHEN '4' THEN 'jeudi' WHEN '5' THEN 'vendredi' ELSE 'samedi' END AS weekday_name,
       CASE WHEN strftime('%w', dt) IN ('0','6') THEN 1 ELSE 0 END AS is_weekend,
       CASE WHEN dt = date(dt, 'start of month', '+1 month', '-1 day') THEN 1 ELSE 0 END AS is_month_end
FROM d;
CREATE UNIQUE INDEX ux_dim_date ON dim_date(date_key);

DROP TABLE IF EXISTS dim_district;
CREATE TABLE dim_district AS
SELECT district_id AS district_key, district_name, region, inhabitants,
       cities, urban_ratio, avg_salary, unemployment_1995, unemployment_1996,
       entrepreneurs_per_1000, crimes_1995, crimes_1996,
       ROUND(1000.0 * crimes_1996 / inhabitants, 1) AS crimes_per_1000_1996,
       CASE WHEN inhabitants >= 200000 THEN 'grande (200k+)' WHEN inhabitants >= 100000 THEN 'moyenne (100-200k)'
            ELSE 'petite (<100k)' END AS size_class,
       NTILE(4) OVER (ORDER BY avg_salary) AS salary_quartile,    -- 1 = salaires les plus bas
       CASE WHEN unemployment_1996 IS NULL THEN 'inconnu'
            WHEN unemployment_1996 >= 5 THEN 'chômage élevé (5 %+)'
            WHEN unemployment_1996 >= 3 THEN 'chômage moyen (3-5 %)' ELSE 'chômage faible (<3 %)' END AS unemployment_band
FROM silver_district;
CREATE UNIQUE INDEX ux_dim_district ON dim_district(district_key);

-- Titulaire (OWNER) de chaque compte : sert à décrire "le client du compte" (démographie).
DROP TABLE IF EXISTS dim_client;
CREATE TABLE dim_client AS
SELECT c.client_id AS client_key, c.gender, c.birth_date,
       CAST((julianday('1998-12-31') - julianday(c.birth_date)) / 365.25 AS INTEGER) AS age_at_ref,
       CASE WHEN (julianday('1998-12-31') - julianday(c.birth_date)) / 365.25 < 25 THEN '<25'
            WHEN (julianday('1998-12-31') - julianday(c.birth_date)) / 365.25 < 35 THEN '25-34'
            WHEN (julianday('1998-12-31') - julianday(c.birth_date)) / 365.25 < 45 THEN '35-44'
            WHEN (julianday('1998-12-31') - julianday(c.birth_date)) / 365.25 < 55 THEN '45-54'
            WHEN (julianday('1998-12-31') - julianday(c.birth_date)) / 365.25 < 65 THEN '55-64' ELSE '65+' END AS age_band,
       c.district_id AS district_key
FROM silver_client c;
CREATE UNIQUE INDEX ux_dim_client ON dim_client(client_key);

DROP TABLE IF EXISTS bridge_account_client;
CREATE TABLE bridge_account_client AS
SELECT account_id AS account_key, client_id AS client_key, disp_type AS role, disp_id FROM silver_disposition;
CREATE INDEX ix_bridge_acc ON bridge_account_client(account_key);

DROP TABLE IF EXISTS dim_card;
CREATE TABLE dim_card AS
SELECT c.card_id AS card_key, c.card_type, c.issued_on, CAST(strftime('%Y%m%d', c.issued_on) AS INTEGER) AS issued_date_key,
       d.account_id AS account_key, d.client_id AS client_key, d.disp_type AS holder_role
FROM silver_card c JOIN silver_disposition d USING(disp_id);

DROP TABLE IF EXISTS dim_account;
CREATE TABLE dim_account AS
WITH owner AS (SELECT account_id, client_id FROM silver_disposition WHERE disp_type = 'owner'),
     best_card AS (SELECT account_key, CASE MAX(CASE card_type WHEN 'gold' THEN 3 WHEN 'classic' THEN 2 ELSE 1 END)
                                       WHEN 3 THEN 'gold' WHEN 2 THEN 'classic' ELSE 'junior' END AS card_type
                   FROM dim_card GROUP BY account_key),
     dispo AS (SELECT account_id, COUNT(*) AS n_disponents FROM silver_disposition WHERE disp_type = 'disponent' GROUP BY account_id)
SELECT a.account_id AS account_key, a.district_id AS district_key, a.statement_frequency,
       a.opened_on, CAST(strftime('%Y%m%d', a.opened_on) AS INTEGER) AS opened_date_key,
       CAST(strftime('%Y', a.opened_on) AS INTEGER) AS opening_year,
       CAST((julianday('1998-12-31') - julianday(a.opened_on)) / 30.4375 AS INTEGER) AS tenure_months_at_ref,
       o.client_id AS owner_client_key, cl.gender AS owner_gender, cl.age_band AS owner_age_band, cl.age_at_ref AS owner_age,
       COALESCE(dp.n_disponents, 0) AS n_disponents,
       CASE WHEN l.loan_id IS NULL THEN 0 ELSE 1 END AS has_loan,
       COALESCE(bc.card_type, 'none') AS best_card_type
FROM silver_account a
JOIN owner o ON o.account_id = a.account_id
JOIN dim_client cl ON cl.client_key = o.client_id
LEFT JOIN dispo dp ON dp.account_id = a.account_id
LEFT JOIN silver_loan l ON l.account_id = a.account_id
LEFT JOIN best_card bc ON bc.account_key = a.account_id;
CREATE UNIQUE INDEX ux_dim_account ON dim_account(account_key);

-- Type d'opération : operation x category regroupés en canal et en motif.
-- Piège Berka : les frais de relevé et intérêts de pénalité sont codés operation = VYBER (retrait),
-- donc "retrait" ne veut PAS dire "espèces". Le canal est déduit du motif d'abord, de l'opération ensuite.
DROP TABLE IF EXISTS dim_tx_type;
CREATE TABLE dim_tx_type AS
SELECT ROW_NUMBER() OVER (ORDER BY operation, category) AS tx_type_key, operation, category, direction,
  CASE WHEN category IN ('statement_fee','overdraft_interest','interest_credited') THEN 'Interne (frais & intérêts)'
       WHEN operation IN ('cash_deposit','cash_withdrawal') THEN 'Espèces (guichet)'
       WHEN operation = 'card_withdrawal' THEN 'Carte'
       ELSE 'Virement' END AS channel,
  CASE WHEN category IN ('statement_fee','overdraft_interest') THEN 'Frais & pénalités'
       WHEN category = 'interest_credited' THEN 'Intérêts crédités'
       WHEN category IN ('household_payment','insurance','leasing') THEN 'Paiements récurrents'
       WHEN category = 'loan_repayment' THEN 'Remboursement de prêt'
       WHEN category = 'pension' THEN 'Pensions' ELSE 'Autres opérations' END AS purpose
FROM (SELECT DISTINCT operation, category, direction FROM silver_transaction);
CREATE UNIQUE INDEX ux_dim_tx_type ON dim_tx_type(tx_type_key);
