"""Télécharge les jeux de données publics (clone git d'un commit figé) vers data/raw/.

Pourquoi des miroirs GitHub : ils sont versionnés (commit figé) et accessibles partout ; les empreintes SHA-256
de data/MANIFEST.json permettent de vérifier que les fichiers sont identiques à ceux utilisés pour les résultats.

Usage :  python scripts/fetch_data.py [--force]
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

# (dossier cible, dépôt, commit, fichiers recherchés par nom dans le dépôt)
JOBS = [
    ("berka", "https://github.com/jlacko/berka-dataset", "77e9972",
     ["account.asc", "client.asc", "disp.asc", "district.asc", "loan.asc", "order.asc", "card.asc", "trans.asc"]),
    ("creditcard_fraud", "https://github.com/nsethi31/Kaggle-Data-Credit-Card-Fraud-Detection", "79453d6", ["creditcard.csv"]),
    ("german_credit", "https://github.com/stedy/Machine-Learning-with-R-datasets", "ff93323", ["credit.csv"]),
    ("bank_marketing", "https://github.com/dsrscientist/DSData", "959d8e4", ["bank_additional_data.csv"]),
]


def main(force: bool = False) -> None:
    for folder, repo, commit, files in JOBS:
        dest = RAW / folder
        if not force and all((dest / f).exists() for f in files):
            print(f"= {folder}: déjà présent")
            continue
        dest.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "clone", "--quiet", repo, tmp + "/r"], check=True)
            subprocess.run(["git", "-C", tmp + "/r", "checkout", "--quiet", commit], check=True)
            for f in files:
                found = next(Path(tmp, "r").rglob(f), None)
                if found is None:
                    raise SystemExit(f"{f} introuvable dans {repo}@{commit}")
                shutil.copy2(found, dest / f)
                print(f"+ {folder}/{f}")
    print("Terminé. Les empreintes SHA-256 attendues sont dans data/MANIFEST.json.")


if __name__ == "__main__":
    main("--force" in sys.argv)
