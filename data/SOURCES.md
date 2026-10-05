# Sources de données

Aucune donnée n'est simulée. Les quatre jeux sont des données publiques réelles et anonymisées.
Les fichiers de travail proviennent de **miroirs GitHub à commit figé** des jeux officiels
(`python scripts/fetch_data.py`), car ils sont versionnés et joignables partout. Les empreintes SHA-256 de
`data/MANIFEST.json` permettent de vérifier que les fichiers sont identiques à ceux utilisés pour les résultats ;
pour une vérification contre l'origine, comparez avec le téléchargement officiel.

| Jeu | Origine officielle | Miroir (commit) | Licence |
|---|---|---|---|
| Berka / PKDD'99 : banque tchèque 1993-1998 (8 tables) | https://sorry.vse.cz/~berka/challenge/pkdd1999/berka.htm | jlacko/berka-dataset @ 77e9972 | Données de recherche anonymisées |
| Credit Card Fraud Detection (Kaggle, Worldline & ULB) | https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud | nsethi31/Kaggle-Data-Credit-Card-Fraud-Detection @ 79453d6 | ODbL / DbCL 1.0 |
| Statlog German Credit (UCI) | https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data | stedy/Machine-Learning-with-R-datasets @ ff93323 (version libellée) | CC BY 4.0 |
| Bank Marketing (UCI) | https://archive.ics.uci.edu/dataset/222/bank+marketing | dsrscientist/DSData @ 959d8e4 (échantillon de 2 999 lignes) | CC BY 4.0 |

Citations : Berka P. (1999) PKDD Discovery Challenge ; Dal Pozzolo et al. (2015) *Calibrating Probability with Undersampling for Unbalanced Classification* ;
Hofmann H. (1994) Statlog German Credit ; Moro S., Cortez P., Rita P. (2014) *A Data-Driven Approach to Predict the Success of Bank Telemarketing*.
