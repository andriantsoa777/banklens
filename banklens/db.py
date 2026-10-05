"""Accès SQLite + exécution de scripts SQL versionnés."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import DB_PATH, SQL


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA foreign_keys=OFF")  # contrôlées explicitement par les tests d'intégrité
    return con


def run_sql_file(con: sqlite3.Connection, rel: str) -> None:
    """Exécute un fichier .sql (plusieurs instructions) situé sous sql/."""
    script = (SQL / rel).read_text(encoding="utf-8")
    con.executescript(script)
    con.commit()


def run_sql_dir(con: sqlite3.Connection, rel_dir: str) -> list[str]:
    done = []
    for f in sorted((SQL / rel_dir).glob("*.sql")):
        run_sql_file(con, f"{rel_dir}/{f.name}")
        done.append(f.name)
    return done


def scalar(con: sqlite3.Connection, sql: str, params: tuple = ()):
    row = con.execute(sql, params).fetchone()
    return None if row is None else row[0]
