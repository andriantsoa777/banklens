# BankLens — plateforme de données bancaires, de la source au tableau de bord

Projet de bout en bout : **ingestion de données publiques réelles → nettoyage traçable → modèle en étoile → 28 questions métier en SQL → 4 modèles de risque → tableau de bord et documentation d'architecture**. Tout se rejoue en une commande.

> Les données sont réelles mais ce sont des **jeux de recherche anonymisés**, pas ceux d'une banque cliente. Les fichiers viennent de **miroirs GitHub à commit figé** des jeux officiels (voir `data/SOURCES.md`) ; les empreintes SHA-256 sont dans `data/MANIFEST.json`.

## Ouvrir d'abord

| Fichier | Contenu |
|---|---|
| `dashboard/architecture.html` | **Présentation du projet** : schéma d'architecture, modèle en étoile, qualité, décisions, correspondance cloud, résultats et méthode |
| `dashboard/index.html` | Tableau de bord (5 vues : Banque, Risque de prêt, Fraude carte, Scoring & marketing, Qualité & lineage) |
| `reports/ANSWERS.md` | Les 28 questions métier : question, réponse chiffrée, lecture, décision, limites |
| `docs/PROJECT_NOTE.md` | Synthèse, indicateurs de référence, points techniques et limites |
| `docs/DATA_DICTIONARY.md` | Dictionnaire des 16 tables gold (grain, clés, types) |

## Architecture

```
 Sources (4 plateformes)      BRONZE (texte brut)        SILVER (typé, propre)        GOLD (étoile)            Consommation
 Berka / PKDD'99      ──┐     bronze_<src>_<table>       silver_*                     dim_* / fact_*           28 requêtes SQL
 Kaggle / ULB fraude  ──┼──►  + _row_num, _source_file,  + PK, CHECK, dates ISO,  ──► 16 tables, grain écrit ──► 4 modèles scikit-learn
 UCI German Credit    ──┤     _batch_id, _loaded_at      codes traduits                                         dashboard HTML
 UCI Bank Marketing   ──┘     meta_load_log (SHA-256)    └─► barrière qualité (32 règles) + quarantaine        architecture.html
```

* **Bronze** : tout est lu en texte, rien n'est perdu ni interprété ; chaque ligne porte son fichier, son numéro et son lot.
* **Silver** : typage, clés, contraintes ; codes tchèques traduits ; `birth_number` décodé ; `?` → NULL (aucune imputation) ; doublons exacts → quarantaine ; **ordre intra-journalier des transactions reconstitué par chaînage des soldes** (99,997 % de lignes chaînées).
* **Barrière qualité** : 32 règles (complétude, unicité, intégrité, validité, cohérence, rapprochements). Un échec bloquant arrête le pipeline ; les 4 avertissements restent visibles.
* **Gold** : dimensions + 3 faits bancaires (mouvement, compte × mois, prêt) + faits fraude, crédit, marketing. Variables de prêt calculées **avant l'octroi** pour éviter la fuite d'information.

## Résultats principaux

* Encours de dépôts 197,2 M CZK ; 4 500 comptes ; 1 056 320 mouvements.
* Prêts : défaut 11,1 % en nombre, 15,1 % en montant ; le taux d'effort (mensualité / entrées) passe de 5,2 % à 26,8 % de défaut selon le niveau.
* Modèle de défaut de prêt : AUC 0,77 en validation croisée 5×5 (IC 95 % [0,69 ; 0,84]) contre 0,62 pour la référence naïve — petit échantillon (76 défauts), présenté comme outil de tri, pas de décision.
* Fraude carte : 473 fraudes = 0,167 % ; 24 % des fraudes la nuit pour 8 % du volume ; PR-AUC 0,77 sur test futur.
* Score de crédit allemand : AUC 0,78, Gini 0,57 ; la politique d'acceptation optimale (coût 5:1) divise le coût de décision par 2,8.
* Marketing : l'AUC « utilisable » est 0,75 ; 0,93 avec la durée d'appel, qui est une **fuite** (connue après l'appel).

Chaque conclusion indique ses limites (effectifs, censure des prêts de 1998, corrélation non significative sur 8 régions, effet Euribor confondu avec la période…).

## Rejouer

```bash
pip install -r requirements.txt
make data      # télécharge les 165 Mo de données (clone des dépôts publics à commit figé, fichiers identiques aux SHA-256 du manifeste)
make all       # ≈ 1 min 20 : manifest → bronze → silver → dq → gold → ml → analysis → dashboard → docs
make test      # 17 tests : réconciliation, clés, intégrité référentielle, chiffres clés
```

Étapes isolées : `python -m banklens.pipeline silver dq gold` (voir `banklens/pipeline.py`).
Python 3.10+ ; SQLite fourni avec Python ; scikit-learn seulement pour l'étape `ml`.

## Organisation

```
banklens/   config, ingest (bronze), silver, ledger, dq, ml, analysis, answers, charts, dashboard, docsgen, pipeline
sql/        silver/00_ddl.sql · gold/01-03 · analysis/ (28 requêtes documentées : id, question, grain)
data/       raw/ (fichiers sources) · MANIFEST.json (SHA-256) · SOURCES.md
warehouse/  banklens.db (reconstruit par le pipeline)
reports/    ANSWERS.md · answers.json · results/*.csv · pipeline.log
dashboard/  index.html · architecture.html (autonomes, sans CDN)
tests/      unittest
```

## Limites assumées

Jeux anonymisés et anciens (Berka 1993-1998, fraude 2013, marketing 2008-2010) ; chargement complet (non incrémental) ; pas d'historisation des dimensions ni de suivi de dérive des modèles ; échantillon de 2 999 lignes pour le marketing. Prochaines étapes : dbt + Airflow, SCD2, modèle de survie pour les prêts, PSI.
