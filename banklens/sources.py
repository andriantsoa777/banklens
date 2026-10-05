"""Registre des sources : d'où vient chaque fichier, sous quelle licence, quel séparateur."""
from __future__ import annotations

from dataclasses import dataclass, field

# Les fichiers sont des copies miroirs (dépôts GitHub publics) des jeux officiels.
# L'origine officielle est indiquée pour la traçabilité ; l'empreinte SHA-256 est dans data/MANIFEST.json.
SOURCES = {
    "berka": dict(
        title="PKDD'99 Discovery Challenge - Financial data (Berka)",
        platform="PKDD'99 / CTU Prague Relational Dataset Repository",
        origin="https://sorry.vse.cz/~berka/challenge/pkdd1999/berka.htm",
        mirror="https://github.com/jlacko/berka-dataset @ 77e9972",
        licence="Données publiques de recherche, anonymisées (Banque tchèque, 1993-1998)",
        sep=";", folder="berka",
        tables={"account": "account.asc", "client": "client.asc", "disp": "disp.asc",
                "district": "district.asc", "loan": "loan.asc", "order": "order.asc",
                "card": "card.asc", "trans": "trans.asc"},
    ),
    "fraud": dict(
        title="Credit Card Fraud Detection (transactions européennes, sept. 2013)",
        platform="Kaggle (Worldline & ULB Machine Learning Group)",
        origin="https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud",
        mirror="https://github.com/nsethi31/Kaggle-Data-Credit-Card-Fraud-Detection @ 79453d6",
        licence="Open Database License (ODbL) / DbCL v1.0 - variables V1-V28 anonymisées par ACP",
        sep=",", folder="creditcard_fraud", tables={"card_tx": "creditcard.csv"},
    ),
    "german": dict(
        title="Statlog (German Credit Data)",
        platform="UCI Machine Learning Repository (Prof. Hans Hofmann)",
        origin="https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
        mirror="https://github.com/stedy/Machine-Learning-with-R-datasets @ ff93323 (version libellée)",
        licence="CC BY 4.0",
        sep=",", folder="german_credit", tables={"credit": "credit.csv"},
    ),
    "marketing": dict(
        title="Bank Marketing (campagnes téléphoniques d'une banque portugaise, 2008-2010)",
        platform="UCI Machine Learning Repository (Moro, Cortez, Rita 2014)",
        origin="https://archive.ics.uci.edu/dataset/222/bank+marketing",
        mirror="https://github.com/dsrscientist/DSData @ 959d8e4 (échantillon de 2 999 lignes de bank-additional)",
        licence="CC BY 4.0",
        sep=",", folder="bank_marketing", tables={"contact": "bank_additional_data.csv"},
    ),
}
