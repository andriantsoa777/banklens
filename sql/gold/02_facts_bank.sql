-- ============================================================================
-- GOLD / faits bancaires. Grain explicite pour chaque table (la 1re question à un entretien : "quel est le grain ?").
-- ============================================================================

-- GRAIN : 1 ligne = 1 opération sur un compte (1 056 320 lignes)
DROP TABLE IF EXISTS fact_transaction;
CREATE TABLE fact_transaction AS
SELECT t.trans_id AS transaction_key,
       CAST(strftime('%Y%m%d', t.tx_date) AS INTEGER) AS date_key,
       t.account_id AS account_key,
       tt.tx_type_key,
       t.tx_seq, t.amount, t.signed_amount, t.balance_after,
       t.counterpart_bank, t.is_negative_balance, t.balance_chain_ok
FROM silver_transaction t
JOIN dim_tx_type tt ON tt.operation = t.operation AND tt.category = t.category AND tt.direction = t.direction;
CREATE UNIQUE INDEX ux_fact_tx ON fact_transaction(transaction_key);
CREATE INDEX ix_fact_tx_acc ON fact_transaction(account_key, tx_seq);
CREATE INDEX ix_fact_tx_date ON fact_transaction(date_key);

-- GRAIN : 1 ligne = 1 compte x 1 mois, de l'ouverture à décembre 1998 (le solde est reporté les mois sans opération)
DROP TABLE IF EXISTS fact_account_month;
CREATE TABLE fact_account_month AS
WITH RECURSIVE months(ym, month_end) AS (
  SELECT '1993-01', '1993-01-31'
  UNION ALL SELECT strftime('%Y-%m', date(month_end, '+1 day')),
                   date(month_end, '+1 day', 'start of month', '+1 month', '-1 day') FROM months WHERE ym < '1998-12'),
grid AS (SELECT a.account_key, m.ym, m.month_end FROM dim_account a JOIN months m
         ON m.ym >= strftime('%Y-%m', a.opened_on)),
agg AS (
  SELECT account_id AS account_key, strftime('%Y-%m', tx_date) AS ym,
         COUNT(*) AS n_tx,
         SUM(CASE WHEN signed_amount > 0 THEN signed_amount ELSE 0 END) AS credits,
         -SUM(CASE WHEN signed_amount < 0 THEN signed_amount ELSE 0 END) AS debits,
         SUM(CASE WHEN operation IN ('cash_deposit','cash_withdrawal') AND category NOT IN ('statement_fee','overdraft_interest') THEN 1 ELSE 0 END) AS n_cash_tx,
         SUM(CASE WHEN operation = 'card_withdrawal' THEN 1 ELSE 0 END) AS n_card_tx,
         MIN(balance_after) AS min_balance
  FROM silver_transaction GROUP BY account_id, strftime('%Y-%m', tx_date))
SELECT g.account_key, g.ym AS year_month,
       CAST(strftime('%Y%m%d', g.month_end) AS INTEGER) AS month_end_date_key,
       COALESCE(a.n_tx, 0) AS n_tx, COALESCE(a.credits, 0) AS credits, COALESCE(a.debits, 0) AS debits,
       COALESCE(a.n_cash_tx, 0) AS n_cash_tx, COALESCE(a.n_card_tx, 0) AS n_card_tx,
       (SELECT balance_after FROM silver_transaction x
         WHERE x.account_id = g.account_key AND x.tx_date <= g.month_end ORDER BY x.tx_date DESC, x.tx_seq DESC LIMIT 1) AS closing_balance,
       a.min_balance,
       CASE WHEN COALESCE(a.min_balance, 0) < 0 THEN 1 ELSE 0 END AS had_overdraft
FROM grid g LEFT JOIN agg a ON a.account_key = g.account_key AND a.ym = g.ym;
CREATE UNIQUE INDEX ux_fam ON fact_account_month(account_key, year_month);
CREATE INDEX ix_fam_ym ON fact_account_month(year_month);

-- GRAIN : 1 ligne = 1 prêt accordé. Les variables "pre_loan_*" n'utilisent QUE des données antérieures à l'octroi
-- (condition indispensable pour un score utilisable en production : pas de fuite du futur).
DROP TABLE IF EXISTS fact_loan;
CREATE TABLE fact_loan AS
WITH pre AS (
  SELECT l.loan_id,
         AVG(f.closing_balance) AS pre_avg_balance_6m,
         AVG(f.credits) AS pre_avg_monthly_inflow_6m,
         AVG(f.debits) AS pre_avg_monthly_outflow_6m,
         SUM(f.had_overdraft) AS pre_overdraft_months_6m,
         COUNT(*) AS pre_months_observed
  FROM silver_loan l
  JOIN fact_account_month f ON f.account_key = l.account_id
   AND f.year_month < strftime('%Y-%m', l.granted_on)
   AND f.year_month >= strftime('%Y-%m', date(l.granted_on, 'start of month', '-6 months'))
  GROUP BY l.loan_id)
SELECT l.loan_id AS loan_key, l.account_id AS account_key,
       CAST(strftime('%Y%m%d', l.granted_on) AS INTEGER) AS granted_date_key,
       l.amount, l.duration_months, l.monthly_payment, l.status_code, l.status_label, l.is_default,
       CASE l.status_code WHEN 'A' THEN 'terminé' WHEN 'B' THEN 'terminé' ELSE 'en cours' END AS lifecycle,
       ROUND(l.monthly_payment * l.duration_months - l.amount, 0) AS interest_cost_implied,
       CASE WHEN l.amount < 50000 THEN '<50k' WHEN l.amount < 100000 THEN '50-100k' WHEN l.amount < 200000 THEN '100-200k' ELSE '200k+' END AS amount_band,
       p.pre_avg_balance_6m, p.pre_avg_monthly_inflow_6m, p.pre_avg_monthly_outflow_6m, p.pre_overdraft_months_6m, p.pre_months_observed,
       CASE WHEN p.pre_avg_monthly_inflow_6m > 0 THEN ROUND(l.monthly_payment / p.pre_avg_monthly_inflow_6m, 3) END AS payment_to_inflow_ratio
FROM silver_loan l LEFT JOIN pre p ON p.loan_id = l.loan_id;
CREATE UNIQUE INDEX ux_fact_loan ON fact_loan(loan_key);

-- GRAIN : 1 ligne = 1 ordre permanent
DROP TABLE IF EXISTS fact_standing_order;
CREATE TABLE fact_standing_order AS
SELECT order_id AS order_key, account_id AS account_key, bank_to, amount, purpose FROM silver_standing_order;
