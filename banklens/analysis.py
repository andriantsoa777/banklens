"""Exécute les requêtes d'analyse (sql/analysis/*.sql), sauvegarde les résultats et rédige les réponses.

Chaque fichier SQL porte un en-tête (id, domaine, titre, question). Les textes de lecture sont générés à partir des
résultats eux-mêmes (answers.py) : si les données changent, la phrase change, elle ne devient jamais fausse.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from .config import REPORTS, SQL
from .log import get_logger

log = get_logger()


def parse_header(sql: str) -> dict:
    meta = {}
    for line in sql.splitlines():
        m = re.match(r"--\s*(\w+):\s*(.*)", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def md_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    d = df.head(max_rows)
    cols = list(d.columns)
    def fmt(v):
        if v is None or (isinstance(v, float) and v != v):
            return "—"
        if isinstance(v, (int, np.integer)):
            return f"{int(v):,}".replace(",", " ")
        if isinstance(v, (float, np.floating)):
            return f"{int(v):,}".replace(",", " ") if float(v).is_integer() else f"{v:,.2f}".replace(",", " ").rstrip("0").rstrip(".")
        return str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(fmt(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def run_analysis(con) -> dict[str, dict]:
    from .answers import ANSWERS  # import tardif : answers.py dépend des résultats

    out_dir = REPORTS / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    for f in sorted((SQL / "analysis").glob("*.sql")):
        sql = f.read_text(encoding="utf-8")
        meta = parse_header(sql)
        df = pd.read_sql(sql, con)
        qid = meta["id"]
        df.to_csv(out_dir / f"{qid}.csv", index=False, encoding="utf-8")
        ans = ANSWERS[qid](df) if qid in ANSWERS else {}
        results[qid] = {"meta": meta, "df": df, "answer": ans, "sql": sql, "file": f.name}
        log.info("analyse %-4s %-12s %3d ligne(s) -> %s", qid, meta.get("domain", ""), len(df), meta.get("title", ""))
    (REPORTS / "answers.json").write_text(json.dumps(
        {k: {"meta": v["meta"], "answer": v["answer"], "rows": v["df"].to_dict(orient="records")} for k, v in results.items()},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return results


def write_answers_md(results: dict[str, dict]) -> None:
    domains = {"banque": "Banque de détail (Berka)", "fraude": "Fraude carte bancaire", "credit": "Scoring de crédit", "marketing": "Marketing bancaire"}
    lines = ["# Réponses aux questions métier", "",
             "Toutes les valeurs ci-dessous sont **calculées par le pipeline** (SQL dans `sql/analysis/`) : aucune n'est saisie à la main.", ""]
    for dom, label in domains.items():
        lines += [f"## {label}", ""]
        for qid, r in results.items():
            if r["meta"].get("domain") != dom:
                continue
            a = r["answer"]
            lines += [f"### {qid} — {r['meta']['title']}", "", f"**Question.** {r['meta']['question']}", ""]
            if a.get("reponse"):
                lines += [f"**Réponse.** {a['reponse']}", ""]
            lines += [md_table(r["df"]), ""]
            if a.get("lecture"):
                lines += [f"**Lecture.** {a['lecture']}", ""]
            if a.get("action"):
                lines += [f"**Décision / action.** {a['action']}", ""]
            if a.get("limite"):
                lines += [f"**Limite.** {a['limite']}", ""]
    (REPORTS / "ANSWERS.md").write_text("\n".join(lines), encoding="utf-8")
