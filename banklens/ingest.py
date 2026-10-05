"""Couche BRONZE : copie fidèle des fichiers sources, tout en texte, avec métadonnées de chargement.

Principe : on ne corrige RIEN ici. Si la source est sale, bronze est sale ; c'est la preuve de ce qui est arrivé.
Chaque ligne reçoit _batch_id, _source_file, _row_num et _loaded_at pour la traçabilité (lineage).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pandas as pd

from .config import RAW, ROOT
from .db import connect
from .log import get_logger
from .sources import SOURCES

log = get_logger()


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_raw(src: str, table: str) -> pd.DataFrame:
    spec = SOURCES[src]
    path = RAW / spec["folder"] / spec["tables"][table]
    # dtype=str + keep_default_na=False : "N/A", "NA", "" restent du texte, rien n'est deviné par pandas.
    return pd.read_csv(path, sep=spec["sep"], dtype=str, keep_default_na=False, encoding="utf-8")


def build_manifest() -> dict:
    manifest = {}
    for src, spec in SOURCES.items():
        files = {}
        for table, fname in spec["tables"].items():
            p = RAW / spec["folder"] / fname
            n = sum(1 for _ in open(p, "rb")) - 1
            files[fname] = {"table": table, "bytes": p.stat().st_size, "rows": n, "sha256": sha256(p)}
        manifest[src] = {k: spec[k] for k in ("title", "platform", "origin", "mirror", "licence")} | {"files": files}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def load_bronze(con=None) -> dict[str, int]:
    own = con is None
    con = con or connect()
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    loaded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.execute("DROP TABLE IF EXISTS meta_load_log")
    con.execute("""CREATE TABLE meta_load_log(batch_id TEXT, source TEXT, tbl TEXT, source_file TEXT,
                   rows_in_file INTEGER, rows_loaded INTEGER, sha256 TEXT, loaded_at TEXT)""")
    counts = {}
    for src, spec in SOURCES.items():
        for table, fname in spec["tables"].items():
            df = read_raw(src, table)
            rows_file = len(df)
            df.columns = [c.strip().strip('"').replace(".", "_") for c in df.columns]
            df.insert(0, "_row_num", range(1, len(df) + 1))
            df["_source_file"] = fname
            df["_batch_id"] = batch_id
            df["_loaded_at"] = loaded_at
            name = f"bronze_{src}_{table}"
            con.execute(f"DROP TABLE IF EXISTS {name}")
            df.to_sql(name, con, index=False, chunksize=50_000)
            n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            con.execute("INSERT INTO meta_load_log VALUES (?,?,?,?,?,?,?,?)",
                        (batch_id, src, table, fname, rows_file, n, sha256(RAW / spec["folder"] / fname), loaded_at))
            counts[name] = n
            log.info("bronze  %-28s %9s lignes", name, f"{n:,}".replace(",", " "))
    con.commit()
    if own:
        con.close()
    return counts
