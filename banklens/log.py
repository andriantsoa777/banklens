"""Journalisation homogène (console + fichier) pour chaque étape du pipeline."""
import logging
import sys

from .config import REPORTS


def get_logger(name: str = "banklens") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    try:
        REPORTS.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(REPORTS / "pipeline.log", mode="w", encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(fh)
    except OSError:
        pass
    return log
