-- ============================================================================
-- GOLD / autres domaines : fraude carte, scoring de crédit, marketing.
-- ============================================================================
DROP TABLE IF EXISTS dim_hour;
CREATE TABLE dim_hour AS
WITH RECURSIVE h(hour_key) AS (SELECT 0 UNION ALL SELECT hour_key + 1 FROM h WHERE hour_key < 23)
SELECT hour_key,
       CASE WHEN hour_key < 6 THEN '1-nuit (0-5h)' WHEN hour_key < 12 THEN '2-matin (6-11h)'
            WHEN hour_key < 18 THEN '3-après-midi (12-17h)' ELSE '4-soir (18-23h)' END AS daypart
FROM h;

-- GRAIN : 1 ligne = 1 transaction carte (après déduplication)
DROP TABLE IF EXISTS fact_card_tx;
CREATE TABLE fact_card_tx AS
SELECT tx_id AS transaction_key, time_s, day_index, hour_of_day AS hour_key, amount, is_zero_amount, is_fraud,
       CASE WHEN amount = 0 THEN '0' WHEN amount < 1 THEN '<1' WHEN amount < 10 THEN '1-10' WHEN amount < 50 THEN '10-50'
            WHEN amount < 100 THEN '50-100' WHEN amount < 500 THEN '100-500' WHEN amount < 1000 THEN '500-1000' ELSE '1000+' END AS amount_band,
       CASE WHEN amount = 0 THEN 1 WHEN amount < 1 THEN 2 WHEN amount < 10 THEN 3 WHEN amount < 50 THEN 4
            WHEN amount < 100 THEN 5 WHEN amount < 500 THEN 6 WHEN amount < 1000 THEN 7 ELSE 8 END AS amount_band_order
FROM silver_card_tx;
CREATE UNIQUE INDEX ux_fact_card_tx ON fact_card_tx(transaction_key);

-- Variables anonymisées V1-V28 (ACP fournie par la source) : gardées à part pour ne pas alourdir le fait.
DROP TABLE IF EXISTS fact_card_tx_features;
CREATE TABLE fact_card_tx_features AS
SELECT tx_id AS transaction_key, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14,
       v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, v25, v26, v27, v28 FROM silver_card_tx;
CREATE UNIQUE INDEX ux_fact_card_feat ON fact_card_tx_features(transaction_key);

-- GRAIN : 1 ligne = 1 dossier de crédit (UCI Statlog German Credit)
DROP TABLE IF EXISTS fact_credit_application;
CREATE TABLE fact_credit_application AS
SELECT application_id AS application_key, checking_balance, credit_history, purpose, savings_balance, employment_length,
       personal_status, other_debtors, property, other_installment_plans, housing, job,
       duration_months, amount_dm, installment_rate, residence_years, age, existing_credits, dependents,
       has_telephone, foreign_worker, is_default,
       CASE WHEN age < 25 THEN '<25' WHEN age < 35 THEN '25-34' WHEN age < 45 THEN '35-44' WHEN age < 55 THEN '45-54' ELSE '55+' END AS age_band,
       CASE WHEN duration_months <= 12 THEN '<=12 mois' WHEN duration_months <= 24 THEN '13-24 mois' WHEN duration_months <= 36 THEN '25-36 mois' ELSE '37+ mois' END AS duration_band,
       CASE WHEN amount_dm < 1500 THEN '<1500' WHEN amount_dm < 3000 THEN '1500-2999' WHEN amount_dm < 6000 THEN '3000-5999' ELSE '6000+' END AS amount_band,
       ROUND(1.0 * amount_dm / duration_months, 0) AS monthly_burden_dm
FROM silver_credit_application;

-- GRAIN : 1 ligne = 1 contact téléphonique de campagne (UCI Bank Marketing, échantillon)
DROP TABLE IF EXISTS fact_marketing_contact;
CREATE TABLE fact_marketing_contact AS
SELECT contact_id AS contact_key, age, job, marital_status, education, has_credit_default, has_housing_loan, has_personal_loan,
       contact_channel, contact_month, contact_weekday, call_duration_s, campaign_contacts, days_since_prev_campaign,
       previous_contacts, previous_outcome, euribor3m, emp_var_rate, cons_conf_idx, subscribed,
       CASE WHEN age < 30 THEN '<30' WHEN age < 40 THEN '30-39' WHEN age < 50 THEN '40-49' WHEN age < 60 THEN '50-59' ELSE '60+' END AS age_band,
       CASE WHEN euribor3m < 1 THEN '1-euribor <1 %' WHEN euribor3m < 3 THEN '2-euribor 1-3 %' ELSE '3-euribor 3 %+' END AS euribor_band,
       CASE WHEN campaign_contacts = 1 THEN '1 contact' WHEN campaign_contacts <= 3 THEN '2-3 contacts' WHEN campaign_contacts <= 6 THEN '4-6 contacts' ELSE '7+ contacts' END AS pressure_band,
       CASE WHEN call_duration_s < 60 THEN '1-<1 min' WHEN call_duration_s < 180 THEN '2-1-3 min' WHEN call_duration_s < 400 THEN '3-3-7 min' ELSE '4-7 min +' END AS duration_band
FROM silver_marketing_contact;
