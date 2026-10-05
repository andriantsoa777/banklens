"""Configuration centrale : chemins, identifiants de lot, règles métier partagées."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("BANKLENS_ROOT", Path(__file__).resolve().parents[1]))
RAW = ROOT / "data" / "raw"
SQL = ROOT / "sql"
REPORTS = ROOT / "reports"
DASH = ROOT / "dashboard"
DOCS = ROOT / "docs"
DB_PATH = Path(os.environ.get("BANKLENS_DB", ROOT / "warehouse" / "banklens.db"))

# Date de référence du jeu Berka : la dernière transaction est au 1998-12-31.
# Tous les âges et ancienneté sont calculés à cette date (jamais "aujourd'hui"),
# sinon les résultats changeraient chaque jour.
BERKA_REF_DATE = "1998-12-31"

# Statuts de prêt Berka : A/C = sain, B/D = défaut (fini non remboursé / en cours en impayé)
LOAN_BAD_STATUS = ("B", "D")

