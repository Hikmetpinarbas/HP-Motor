from __future__ import annotations
import pandas as pd

def load_inventory(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def allowed_sheets_for_corr(inv: pd.DataFrame, max_corr_pairs: int = 15000) -> list[tuple[str,str]]:
    """
    Returns list of (file, sheet) where corr_pairs <= max_corr_pairs.
    """
    ok = inv[inv["corr_pairs"] <= max_corr_pairs]
    return list(zip(ok["file"].astype(str), ok["sheet"].astype(str)))
