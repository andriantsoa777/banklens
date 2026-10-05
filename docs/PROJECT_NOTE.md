# Note de présentation BankLens

## Synthèse

BankLens est une plateforme de données bancaires reproductible construite à partir de quatre jeux publics réels (1 056 320 mouvements bancaires, fraude carte, crédit et marketing). Les données brutes sont conservées, nettoyées avec 32 contrôles qualité, modélisées en étoile, interrogées par 28 requêtes SQL et utilisées pour des modèles évalués sans fuite d'information. L'ensemble se rejoue avec `make all`.

## Indicateurs de référence

- 1 368 486 lignes ingérées, 11 fichiers, 4 sources
- 1 081 lignes en quarantaine, 26 corrections tracées
- Défaut de prêt : 11,1 % (nombre), 15,1 % (montant)
- Fraude carte : 0,167 % ; PR-AUC 0,77
- AUC défaut de prêt 0,77 (référence 0,62) ; AUC score allemand 0,78
- Soldes chaînés : 99,997 %

## Points techniques

### Choix de SQLite pour l'entrepôt analytique

Parce que le volume (≈ 1,4 M de lignes, ≈ 160 Mo) ne justifie pas un entrepôt cloud, et que SQLite rend le projet reproductible en une commande, sans compte ni coût. Ce qui compte, c'est l'architecture et le SQL, qui sont portables : tout est en SQL standard (CTE, fenêtres) et la page « correspondance cloud » montre où chaque brique irait. Le passage à BigQuery ou Snowflake est un changement de connecteur et de dialecte, pas de conception.

### Architecture en médaillon : bronze, silver et gold

Chaque couche répond à une question différente. Bronze : « qu'ai-je reçu ? » (tout en texte, rien perdu, lot et empreinte SHA-256). Silver : « que vaut cette donnée ? » (types, règles, corrections tracées, rejets en quarantaine). Gold : « comment l'analyser ? » (modèle en étoile). On peut rejouer silver ou gold sans re-télécharger, et on peut toujours remonter d'un chiffre du dashboard jusqu'à la ligne source.

### Réconciliation et conservation des données

Par une réconciliation automatique : bronze = silver + quarantaine pour chaque table (règles C01-C06, bloquantes). Les 1 081 lignes écartées (doublons exacts du jeu de fraude) sont conservées avec leur motif. Les 26 corrections (dates, libellés tchèques, valeurs « ? ») sont listées avec le nombre de lignes touchées. Si une règle bloquante échoue, le pipeline s'arrête.

### Reconstitution de l'ordre des transactions Berka

L'ordre des transactions. L'identifiant n'est pas chronologique et plusieurs opérations tombent le même jour : un tri par date seule ne reconstitue pas le solde. J'ai reconstitué l'ordre intra-journalier en chaînant les soldes (chaque solde = solde précédent + montant) : 99,997 % des lignes se chaînent. Les 28 ruptures restantes (14 comptes) sont signalées par la règle B01 en avertissement et non masquées.

### Prévention de la fuite d'information

Trois endroits. (1) Pour le modèle de défaut de prêt, les variables sont calculées uniquement sur la période précédant l'octroi (préfixe pre_). (2) Pour la fraude, le découpage est temporel (apprentissage sur le passé, test sur le futur) et non aléatoire. (3) Pour le marketing, la durée d'appel est exclue du modèle : elle n'est connue qu'après l'appel et fait passer l'AUC de 0,75 à 0,93, ce que je montre comme un contre-exemple.

### Interprétation de la performance du modèle de défaut

C'est honnête, pas spectaculaire. Sur 682 prêts dont 76 défauts, l'AUC en validation croisée 5×5 est 0,77 avec un intervalle de confiance large, contre 0,62 pour la référence naïve (montant seul). Je le présente comme un outil de tri du risque (le cinquième quintile concentre plus de la moitié des défauts), pas comme un modèle prêt à décider seul. L'échantillon est petit : je le dis.

### Métrique d'évaluation adaptée à la fraude

Parce que la fraude représente 0,167 % des transactions : un modèle qui répond toujours « légitime » aurait 99,8 % d'exactitude et ne servirait à rien. Je mesure donc la PR-AUC (0,77) sur un test futur, et je convertis le seuil en coût : combien d'alertes, combien de fraudes captées, pour un coût de traitement par alerte.

### Provenance et statut des données

Rien n'est simulé. Les quatre jeux sont des données publiques réelles et anonymisées (Berka, Kaggle/ULB, UCI German Credit, UCI Bank Marketing). Les fichiers viennent de miroirs GitHub des jeux officiels, car le poste de travail ne pouvait pas joindre directement les sites d'origine ; la provenance exacte (dépôt, commit) et l'empreinte SHA-256 de chaque fichier sont dans le manifeste. Ce ne sont pas les données d'une banque cliente : ce sont des jeux de recherche, et je ne prétends pas le contraire.

### Traitement des variables protégées

C'est une variable protégée. Elle est décodée dans la dimension client pour l'analyse descriptive, mais exclue de tous les scores. Même logique pour la tranche d'âge dans le scoring de crédit allemand : je la signale comme point d'attention réglementaire.

### Trajectoire vers la production

Orchestration avec Airflow ou Dagster, transformations SQL en dbt (les fichiers sql/ deviennent des modèles, les règles de qualité deviennent des tests), stockage objet pour la couche bronze, entrepôt cloud pour gold, BI via Power BI ou Looker. Il faudrait ajouter le chargement incrémental (aujourd'hui rechargement complet par lot), le suivi de dérive des modèles et la gestion des accès par ligne.

### Évolutions identifiées

Un chargement incrémental avec SCD2 sur les dimensions, un modèle de survie pour les prêts (au lieu d'un indicateur binaire de défaut) afin de traiter la censure des prêts récents, un test de stabilité des variables (PSI) entre périodes, et un calibrage des probabilités avant tout usage décisionnel.

### Reproductibilité du pipeline

Trois commandes : installer les dépendances, `make data` si les fichiers ne sont pas présents, puis `make all`. Le pipeline reconstruit l'entrepôt, exécute les 32 contrôles qualité, les 28 requêtes, les modèles, puis régénère le dashboard et cette page. Les tests unitaires vérifient la réconciliation, les clés et les chiffres clés.

## Périmètre et limites

- Ce sont des jeux de recherche anonymisés, pas les données d'une banque cliente.
- Les fichiers viennent de miroirs de dépôts publics ; les empreintes SHA-256 sont vérifiables.
- Les limites statistiques et opérationnelles sont détaillées dans la page d'architecture.
