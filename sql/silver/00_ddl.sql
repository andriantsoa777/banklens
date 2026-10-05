-- ============================================================================
-- SILVER : tables typées, contraintes explicites, noms lisibles (anglais métier).
-- Chaque table a une clé primaire ; les CHECK rejettent en base ce que Python aurait laissé passer.
-- ============================================================================
DROP TABLE IF EXISTS silver_district;
CREATE TABLE silver_district (
  district_id INTEGER PRIMARY KEY,
  district_name TEXT NOT NULL,
  region TEXT NOT NULL,
  inhabitants INTEGER NOT NULL CHECK (inhabitants > 0),
  municipalities_lt_500 INTEGER, municipalities_500_1999 INTEGER,
  municipalities_2000_9999 INTEGER, municipalities_gt_10000 INTEGER,
  cities INTEGER,
  urban_ratio REAL CHECK (urban_ratio BETWEEN 0 AND 100),
  avg_salary INTEGER CHECK (avg_salary > 0),
  unemployment_1995 REAL, unemployment_1996 REAL,
  entrepreneurs_per_1000 INTEGER,
  crimes_1995 INTEGER, crimes_1996 INTEGER
);

DROP TABLE IF EXISTS silver_account;
CREATE TABLE silver_account (
  account_id INTEGER PRIMARY KEY,
  district_id INTEGER NOT NULL,
  statement_frequency TEXT NOT NULL CHECK (statement_frequency IN ('monthly','weekly','after_transaction')),
  opened_on TEXT NOT NULL
);

DROP TABLE IF EXISTS silver_client;
CREATE TABLE silver_client (
  client_id INTEGER PRIMARY KEY,
  district_id INTEGER NOT NULL,
  birth_date TEXT NOT NULL,
  gender TEXT NOT NULL CHECK (gender IN ('F','M'))
);

DROP TABLE IF EXISTS silver_disposition;
CREATE TABLE silver_disposition (
  disp_id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL,
  account_id INTEGER NOT NULL,
  disp_type TEXT NOT NULL CHECK (disp_type IN ('owner','disponent'))
);

DROP TABLE IF EXISTS silver_card;
CREATE TABLE silver_card (
  card_id INTEGER PRIMARY KEY,
  disp_id INTEGER NOT NULL,
  card_type TEXT NOT NULL CHECK (card_type IN ('junior','classic','gold')),
  issued_on TEXT NOT NULL
);

DROP TABLE IF EXISTS silver_loan;
CREATE TABLE silver_loan (
  loan_id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  granted_on TEXT NOT NULL,
  amount INTEGER NOT NULL CHECK (amount > 0),
  duration_months INTEGER NOT NULL CHECK (duration_months IN (12,24,36,48,60)),
  monthly_payment REAL NOT NULL CHECK (monthly_payment > 0),
  status_code TEXT NOT NULL CHECK (status_code IN ('A','B','C','D')),
  status_label TEXT NOT NULL,
  is_default INTEGER NOT NULL CHECK (is_default IN (0,1))
);

DROP TABLE IF EXISTS silver_standing_order;
CREATE TABLE silver_standing_order (
  order_id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  bank_to TEXT NOT NULL,
  account_to TEXT NOT NULL,
  amount REAL NOT NULL CHECK (amount > 0),
  purpose TEXT NOT NULL
);

DROP TABLE IF EXISTS silver_transaction;
CREATE TABLE silver_transaction (
  trans_id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  tx_seq INTEGER NOT NULL,            -- ordre réel dans le compte (reconstitué par chaînage des soldes)
  tx_date TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('credit','debit')),
  operation TEXT NOT NULL,
  category TEXT NOT NULL,
  amount REAL NOT NULL CHECK (amount >= 0),
  signed_amount REAL NOT NULL,
  balance_after REAL NOT NULL,
  counterpart_bank TEXT,
  counterpart_account TEXT,
  is_zero_amount INTEGER NOT NULL,
  is_negative_balance INTEGER NOT NULL,
  balance_chain_ok INTEGER NOT NULL,  -- 1 si solde_précédent + montant = solde_après (±0,15)
  balance_drift REAL NOT NULL         -- écart observé (0,10 = arrondi d'intérêts ; autre = rupture)
);
CREATE UNIQUE INDEX ux_tx_account_seq ON silver_transaction(account_id, tx_seq);
CREATE INDEX ix_tx_account_date ON silver_transaction(account_id, tx_date);

DROP TABLE IF EXISTS silver_card_tx;
CREATE TABLE silver_card_tx (
  tx_id INTEGER PRIMARY KEY,         -- numéro de ligne dans le fichier source (aucun identifiant fourni)
  time_s INTEGER NOT NULL,           -- secondes écoulées depuis la 1re transaction du jeu
  day_index INTEGER NOT NULL,        -- 0 ou 1 : le jeu couvre 48 h
  hour_of_day INTEGER NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
  amount REAL NOT NULL CHECK (amount >= 0),
  is_zero_amount INTEGER NOT NULL,
  is_fraud INTEGER NOT NULL CHECK (is_fraud IN (0,1)),
  v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL, v7 REAL, v8 REAL, v9 REAL, v10 REAL,
  v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL, v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL,
  v21 REAL, v22 REAL, v23 REAL, v24 REAL, v25 REAL, v26 REAL, v27 REAL, v28 REAL
);

DROP TABLE IF EXISTS silver_credit_application;
CREATE TABLE silver_credit_application (
  application_id INTEGER PRIMARY KEY,
  checking_balance TEXT, duration_months INTEGER NOT NULL, credit_history TEXT, purpose TEXT,
  amount_dm INTEGER NOT NULL CHECK (amount_dm > 0),
  savings_balance TEXT, employment_length TEXT, installment_rate INTEGER, personal_status TEXT,
  other_debtors TEXT, residence_years INTEGER, property TEXT, age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 100),
  other_installment_plans TEXT, housing TEXT, existing_credits INTEGER, dependents INTEGER,
  has_telephone INTEGER, foreign_worker INTEGER, job TEXT,
  is_default INTEGER NOT NULL CHECK (is_default IN (0,1))
);

DROP TABLE IF EXISTS silver_marketing_contact;
CREATE TABLE silver_marketing_contact (
  contact_id INTEGER PRIMARY KEY,
  age INTEGER NOT NULL, job TEXT, marital_status TEXT, education TEXT,
  has_credit_default INTEGER, has_housing_loan INTEGER, has_personal_loan INTEGER,
  contact_channel TEXT NOT NULL, contact_month INTEGER NOT NULL, contact_weekday TEXT NOT NULL,
  call_duration_s INTEGER NOT NULL, campaign_contacts INTEGER NOT NULL,
  days_since_prev_campaign INTEGER, previous_contacts INTEGER NOT NULL, previous_outcome TEXT,
  emp_var_rate REAL, cons_price_idx REAL, cons_conf_idx REAL, euribor3m REAL, nr_employed REAL,
  subscribed INTEGER NOT NULL CHECK (subscribed IN (0,1))
);

-- Traçabilité des corrections et rejets
DROP TABLE IF EXISTS dq_fixes;
CREATE TABLE dq_fixes (source TEXT, tbl TEXT, fix_id TEXT, description TEXT, rows_affected INTEGER);
DROP TABLE IF EXISTS quarantine;
CREATE TABLE quarantine (source TEXT, tbl TEXT, row_ref TEXT, rule_id TEXT, detail TEXT, payload TEXT);
