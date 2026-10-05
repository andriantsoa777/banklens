-- id: Q01
-- domain: banque
-- title: Les chiffres clés de la banque
-- question: Quelle est la taille de la banque en décembre 1998 : combien de comptes, de clients, de transactions, quel encours ?
-- grain: 1 ligne par indicateur
SELECT 'Comptes ouverts' AS indicateur, COUNT(*) AS valeur, 'comptes' AS unite FROM dim_account
UNION ALL SELECT 'Clients (titulaires + disposants)', COUNT(*), 'personnes' FROM dim_client
UNION ALL SELECT 'Transactions enregistrées', COUNT(*), 'opérations' FROM fact_transaction
UNION ALL SELECT 'Encours de dépôts au 31/12/1998', ROUND(SUM(closing_balance) / 1e6, 1), 'M CZK' FROM fact_account_month WHERE year_month = '1998-12'
UNION ALL SELECT 'Solde moyen par compte au 31/12/1998', ROUND(AVG(closing_balance), 0), 'CZK' FROM fact_account_month WHERE year_month = '1998-12'
UNION ALL SELECT 'Prêts accordés', COUNT(*), 'prêts' FROM fact_loan
UNION ALL SELECT 'Montant total prêté', ROUND(SUM(amount) / 1e6, 1), 'M CZK' FROM fact_loan
UNION ALL SELECT 'Cartes émises', COUNT(*), 'cartes' FROM dim_card
UNION ALL SELECT 'Districts couverts', COUNT(*), 'districts' FROM dim_district;
