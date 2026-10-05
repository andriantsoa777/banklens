"""Orchestrateur : enchaîne les étapes, mesure leur durée, s'arrête sur un contrôle bloquant.

Usage :  python -m banklens.pipeline [etape ...]      (aucune étape = tout)
Étapes :  manifest, bronze, silver, dq, gold, analysis, ml, dashboard, docs
"""
from __future__ import annotations

import sys
import time

from . import analysis, dq, ingest, silver
from .config import DB_PATH
from .db import connect, run_sql_dir
from .log import get_logger

log = get_logger()
STEPS = ["manifest", "bronze", "silver", "dq", "gold", "ml", "analysis", "dashboard", "docs"]


def _gold(con):
    for f in run_sql_dir(con, "gold"):
        log.info("gold    %s", f)
    for t in ("dim_account", "dim_client", "dim_district", "fact_transaction", "fact_account_month", "fact_loan",
              "fact_card_tx", "fact_credit_application", "fact_marketing_contact"):
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        log.info("gold    %-26s %9s lignes", t, f"{n:,}".replace(",", " "))


def run(steps: list[str] | None = None) -> None:
    steps = steps or STEPS
    unknown = [s for s in steps if s not in STEPS]
    if unknown:
        raise SystemExit(f"Étape(s) inconnue(s) : {unknown}. Étapes valides : {STEPS}")
    t_all = time.time()
    con = connect()
    results = None
    for step in STEPS:
        if step not in steps:
            continue
        t0 = time.time()
        log.info("=" * 20 + f" {step.upper()} " + "=" * 20)
        if step == "manifest":
            ingest.build_manifest()
        elif step == "bronze":
            ingest.load_bronze(con)
        elif step == "silver":
            silver.build_silver(con)
        elif step == "dq":
            dq.run_rules(con)
        elif step == "gold":
            _gold(con)
        elif step == "ml":
            from .ml import run_ml
            run_ml(con)
        elif step == "analysis":
            results = analysis.run_analysis(con)
            analysis.write_answers_md(results)
        elif step == "dashboard":
            from .dashboard import build_dashboard
            build_dashboard(con)
        elif step == "docs":
            from .docsgen import build_docs
            build_docs(con)
        log.info("étape %s terminée en %.1f s", step, time.time() - t0)
    con.close()
    log.info("pipeline terminé en %.1f s -> %s", time.time() - t_all, DB_PATH)


if __name__ == "__main__":
    run(sys.argv[1:] or None)
