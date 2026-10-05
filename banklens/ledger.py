"""Reconstitution de l'ordre réel des opérations d'un compte.

Constat sur Berka : `trans_id` n'est PAS chronologique et plusieurs opérations partagent le même jour.
Sans ordre, le solde "avant/après" est incohérent (seulement ~50 % des lignes se réconcilient avec trans_id).
Méthode : le solde est une chaîne. Dans un compte-jour, on choisit à chaque pas la ligne dont
    solde_précédent + montant_signé  ≈  solde_après
(tolérance de 0,10 : la banque arrondit les intérêts au dixième).
Résultat : 99,997 % des lignes se chaînent ; le reste est de vraies ruptures (opération manquante à la source).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TOL_CENTS = 15  # 0,15 CZK : couvre l'arrondi des intérêts (écart observé = 0,10)


def sequence_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """df : trans_id, account_id, tx_date (ISO), signed_amount, balance_after.
    Retourne df trié dans l'ordre chaîné + tx_seq (1..n par compte), balance_chain_ok, balance_drift."""
    t = df.sort_values(["account_id", "tx_date", "trans_id"]).reset_index(drop=True)
    cs = (t["signed_amount"] * 100).round().astype("int64").to_numpy()
    cb = (t["balance_after"] * 100).round().astype("int64").to_numpy()
    acc = t["account_id"].to_numpy()
    dt = t["tx_date"].to_numpy()
    n = len(t)
    order, ok, drift = [], np.zeros(n, bool), np.zeros(n, np.int64)
    i, cur_acc, prev = 0, None, 0
    while i < n:
        j = i
        while j < n and acc[j] == acc[i] and dt[j] == dt[i]:
            j += 1
        if acc[i] != cur_acc:          # nouveau compte : le solde d'avant la 1re opération est 0
            cur_acc, prev = acc[i], 0
        rem = list(range(i, j))
        cur = prev
        while rem:
            best = min(rem, key=lambda k: (abs(cur + cs[k] - cb[k]), k))
            e = cur + cs[best] - cb[best]
            ok[best] = abs(e) <= TOL_CENTS
            drift[best] = e
            rem.remove(best)
            order.append(best)
            cur = cb[best]             # on se recale sur le solde observé : une rupture ne se propage pas
        prev = cur
        i = j
    out = t.iloc[order].reset_index(drop=True)
    out["balance_chain_ok"] = ok[order].astype(int)
    out["balance_drift"] = drift[order] / 100.0
    out["tx_seq"] = out.groupby("account_id").cumcount() + 1
    return out
