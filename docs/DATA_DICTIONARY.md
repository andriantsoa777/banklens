# Dictionnaire de données (couche gold)

Généré automatiquement depuis l'entrepôt (`python -m banklens docs`). Le grain de chaque table est indiqué : c'est la première chose à vérifier avant une jointure.


## `dim_date`

Calendrier 1993-1998.  
**Grain** : 1 ligne = 1 jour · **Lignes** : 2 191

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `date_key` | INT | FK | oui |
| `full_date` | TEXT |  | oui |
| `year` | INT |  | oui |
| `quarter` | TEXT |  | oui |
| `month` | INT |  | oui |
| `year_month` | TEXT |  | oui |
| `weekday_num` | INT |  | oui |
| `weekday_name` | TEXT |  | oui |
| `is_weekend` | TEXT |  | oui |
| `is_month_end` | TEXT |  | oui |

## `dim_district`

Districts tchèques (région, salaire moyen, chômage, criminalité).  
**Grain** : 1 ligne = 1 district · **Lignes** : 77

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `district_key` | INT | FK | oui |
| `district_name` | TEXT |  | oui |
| `region` | TEXT |  | oui |
| `inhabitants` | INT |  | oui |
| `cities` | INT |  | oui |
| `urban_ratio` | REAL |  | oui |
| `avg_salary` | INT |  | oui |
| `unemployment_1995` | REAL |  | oui |
| `unemployment_1996` | REAL |  | oui |
| `entrepreneurs_per_1000` | INT |  | oui |
| `crimes_1995` | INT |  | oui |
| `crimes_1996` | INT |  | oui |
| `crimes_per_1000_1996` | TEXT |  | oui |
| `size_class` | TEXT |  | oui |
| `salary_quartile` | TEXT |  | oui |
| `unemployment_band` | TEXT |  | oui |

## `dim_client`

Clients (âge à la date de référence, tranche d'âge).  
**Grain** : 1 ligne = 1 client · **Lignes** : 5 369

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `client_key` | INT | FK | oui |
| `gender` | TEXT |  | oui |
| `birth_date` | TEXT |  | oui |
| `age_at_ref` | INT |  | oui |
| `age_band` | TEXT |  | oui |
| `district_key` | INT | FK | oui |

## `bridge_account_client`

Pont compte ↔ client avec rôle (titulaire / disposant).  
**Grain** : 1 ligne = 1 droit sur un compte · **Lignes** : 5 369

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `account_key` | INT | FK | oui |
| `client_key` | INT | FK | oui |
| `role` | TEXT |  | oui |
| `disp_id` | INT |  | oui |

## `dim_card`

Cartes bancaires (type, émission, titulaire).  
**Grain** : 1 ligne = 1 carte · **Lignes** : 892

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `card_key` | INT | FK | oui |
| `card_type` | TEXT |  | oui |
| `issued_on` | TEXT |  | oui |
| `issued_date_key` | INT | FK | oui |
| `account_key` | INT | FK | oui |
| `client_key` | INT | FK | oui |
| `holder_role` | TEXT |  | oui |

## `dim_account`

Comptes (fréquence de relevé, ancienneté, titulaire principal).  
**Grain** : 1 ligne = 1 compte · **Lignes** : 4 500

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `account_key` | INT | FK | oui |
| `district_key` | INT | FK | oui |
| `statement_frequency` | TEXT |  | oui |
| `opened_on` | TEXT |  | oui |
| `opened_date_key` | INT | FK | oui |
| `opening_year` | INT |  | oui |
| `tenure_months_at_ref` | INT |  | oui |
| `owner_client_key` | INT | FK | oui |
| `owner_gender` | TEXT |  | oui |
| `owner_age_band` | TEXT |  | oui |
| `owner_age` | INT |  | oui |
| `n_disponents` | TEXT |  | oui |
| `has_loan` | TEXT |  | oui |
| `best_card_type` | TEXT |  | oui |

## `dim_tx_type`

Type de mouvement : opération, catégorie, canal, finalité.  
**Grain** : 1 ligne = 1 combinaison opération/catégorie · **Lignes** : 14

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `tx_type_key` | TEXT | FK | oui |
| `operation` | TEXT |  | oui |
| `category` | TEXT |  | oui |
| `direction` | TEXT |  | oui |
| `channel` | TEXT |  | oui |
| `purpose` | TEXT |  | oui |

## `fact_transaction`

Mouvements du compte avec rang intra-journalier reconstitué et solde chaîné.  
**Grain** : 1 ligne = 1 mouvement · **Lignes** : 1 056 320

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `transaction_key` | INT | FK | oui |
| `date_key` | INT | FK | oui |
| `account_key` | INT | FK | oui |
| `tx_type_key` | TEXT | FK | oui |
| `tx_seq` | INT |  | oui |
| `amount` | REAL |  | oui |
| `signed_amount` | REAL |  | oui |
| `balance_after` | REAL |  | oui |
| `counterpart_bank` | TEXT |  | oui |
| `is_negative_balance` | INT |  | oui |
| `balance_chain_ok` | INT |  | oui |

## `fact_account_month`

Activité mensuelle d'un compte : flux, nb opérations, solde de fin de mois, découvert.  
**Grain** : 1 ligne = 1 compte × 1 mois · **Lignes** : 185 615

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `account_key` | INT | FK | oui |
| `year_month` | TEXT |  | oui |
| `month_end_date_key` | INT | FK | oui |
| `n_tx` | TEXT |  | oui |
| `credits` | TEXT |  | oui |
| `debits` | TEXT |  | oui |
| `n_cash_tx` | TEXT |  | oui |
| `n_card_tx` | TEXT |  | oui |
| `closing_balance` | REAL |  | oui |
| `min_balance` | TEXT |  | oui |
| `had_overdraft` | TEXT |  | oui |

## `fact_loan`

Prêts avec variables d'avant-octroi (sans fuite d'information) et statut final.  
**Grain** : 1 ligne = 1 prêt · **Lignes** : 682

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `loan_key` | INT | FK | oui |
| `account_key` | INT | FK | oui |
| `granted_date_key` | INT | FK | oui |
| `amount` | INT |  | oui |
| `duration_months` | INT |  | oui |
| `monthly_payment` | REAL |  | oui |
| `status_code` | TEXT |  | oui |
| `status_label` | TEXT |  | oui |
| `is_default` | INT |  | oui |
| `lifecycle` | TEXT |  | oui |
| `interest_cost_implied` | TEXT |  | oui |
| `amount_band` | TEXT |  | oui |
| `pre_avg_balance_6m` | TEXT |  | oui |
| `pre_avg_monthly_inflow_6m` | TEXT |  | oui |
| `pre_avg_monthly_outflow_6m` | TEXT |  | oui |
| `pre_overdraft_months_6m` | TEXT |  | oui |
| `pre_months_observed` | TEXT |  | oui |
| `payment_to_inflow_ratio` | TEXT |  | oui |

## `fact_standing_order`

Ordres permanents (montant, finalité).  
**Grain** : 1 ligne = 1 ordre permanent · **Lignes** : 6 471

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `order_key` | INT | FK | oui |
| `account_key` | INT | FK | oui |
| `bank_to` | TEXT |  | oui |
| `amount` | REAL |  | oui |
| `purpose` | TEXT |  | oui |

## `dim_hour`

Heure de la journée et plage (nuit / matin / après-midi / soir).  
**Grain** : 1 ligne = 1 heure · **Lignes** : 24

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `hour_key` | TEXT | FK | oui |
| `daypart` | TEXT |  | oui |

## `fact_card_tx`

Transactions carte (jeu fraude), doublons exacts écartés.  
**Grain** : 1 ligne = 1 transaction carte · **Lignes** : 283 726

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `transaction_key` | INT | FK | oui |
| `time_s` | INT |  | oui |
| `day_index` | INT |  | oui |
| `hour_key` | INT | FK | oui |
| `amount` | REAL |  | oui |
| `is_zero_amount` | INT |  | oui |
| `is_fraud` | INT |  | oui |
| `amount_band` | TEXT |  | oui |
| `amount_band_order` | TEXT |  | oui |

## `fact_card_tx_features`

Composantes anonymisées V1-V28 (ACP), séparées pour garder la table de faits étroite.  
**Grain** : 1 ligne = 1 transaction carte · **Lignes** : 283 726

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `transaction_key` | INT | FK | oui |
| `v1` | REAL |  | oui |
| `v2` | REAL |  | oui |
| `v3` | REAL |  | oui |
| `v4` | REAL |  | oui |
| `v5` | REAL |  | oui |
| `v6` | REAL |  | oui |
| `v7` | REAL |  | oui |
| `v8` | REAL |  | oui |
| `v9` | REAL |  | oui |
| `v10` | REAL |  | oui |
| `v11` | REAL |  | oui |
| `v12` | REAL |  | oui |
| `v13` | REAL |  | oui |
| `v14` | REAL |  | oui |
| `v15` | REAL |  | oui |
| `v16` | REAL |  | oui |
| `v17` | REAL |  | oui |
| `v18` | REAL |  | oui |
| `v19` | REAL |  | oui |
| `v20` | REAL |  | oui |
| `v21` | REAL |  | oui |
| `v22` | REAL |  | oui |
| `v23` | REAL |  | oui |
| `v24` | REAL |  | oui |
| `v25` | REAL |  | oui |
| `v26` | REAL |  | oui |
| `v27` | REAL |  | oui |
| `v28` | REAL |  | oui |

## `fact_credit_application`

Demandes de crédit allemandes avec décision observée (bon / mauvais payeur).  
**Grain** : 1 ligne = 1 demande · **Lignes** : 1 000

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `application_key` | INT | FK | oui |
| `checking_balance` | TEXT |  | oui |
| `credit_history` | TEXT |  | oui |
| `purpose` | TEXT |  | oui |
| `savings_balance` | TEXT |  | oui |
| `employment_length` | TEXT |  | oui |
| `personal_status` | TEXT |  | oui |
| `other_debtors` | TEXT |  | oui |
| `property` | TEXT |  | oui |
| `other_installment_plans` | TEXT |  | oui |
| `housing` | TEXT |  | oui |
| `job` | TEXT |  | oui |
| `duration_months` | INT |  | oui |
| `amount_dm` | INT |  | oui |
| `installment_rate` | INT |  | oui |
| `residence_years` | INT |  | oui |
| `age` | INT |  | oui |
| `existing_credits` | INT |  | oui |
| `dependents` | INT |  | oui |
| `has_telephone` | INT |  | oui |
| `foreign_worker` | INT |  | oui |
| `is_default` | INT |  | oui |
| `age_band` | TEXT |  | oui |
| `duration_band` | TEXT |  | oui |
| `amount_band` | TEXT |  | oui |
| `monthly_burden_dm` | TEXT |  | oui |

## `fact_marketing_contact`

Contacts de campagne téléphonique avec contexte macro et résultat.  
**Grain** : 1 ligne = 1 contact · **Lignes** : 2 999

| Colonne | Type | Clé | Nullable |
|---|---|---|---|
| `contact_key` | INT | FK | oui |
| `age` | INT |  | oui |
| `job` | TEXT |  | oui |
| `marital_status` | TEXT |  | oui |
| `education` | TEXT |  | oui |
| `has_credit_default` | INT |  | oui |
| `has_housing_loan` | INT |  | oui |
| `has_personal_loan` | INT |  | oui |
| `contact_channel` | TEXT |  | oui |
| `contact_month` | INT |  | oui |
| `contact_weekday` | TEXT |  | oui |
| `call_duration_s` | INT |  | oui |
| `campaign_contacts` | INT |  | oui |
| `days_since_prev_campaign` | INT |  | oui |
| `previous_contacts` | INT |  | oui |
| `previous_outcome` | TEXT |  | oui |
| `euribor3m` | REAL |  | oui |
| `emp_var_rate` | REAL |  | oui |
| `cons_conf_idx` | REAL |  | oui |
| `subscribed` | INT |  | oui |
| `age_band` | TEXT |  | oui |
| `euribor_band` | TEXT |  | oui |
| `pressure_band` | TEXT |  | oui |
| `duration_band` | TEXT |  | oui |
