from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class SOTValidator:
    """
    Minimal SOT validator for canonical dataframes.
    It must NEVER drop rows/columns. It only reports.
    """

    required_columns: List[str]

    def validate(self, df: Optional[pd.DataFrame]) -> Dict[str, Any]:
        if df is None:
            return {
                "ok": False,
                "issues": [{"code": "NO_DF", "severity": "ERROR", "message": "No dataframe provided"}],
                "bounds_report": {},
            }

        issues: List[Dict[str, Any]] = []

        for c in self.required_columns:
            if c not in df.columns:
                issues.append({"code": "MISSING_REQUIRED_COLUMN", "severity": "ERROR", "message": f"Missing: {c}"})

        bounds_report: Dict[str, Any] = {}
        if "x" in df.columns:
            x = pd.to_numeric(df["x"], errors="coerce").dropna()
            bounds_report["x_out_of_bounds"] = int(((x < 0) | (x > 130)).sum()) if not x.empty else 0
        if "y" in df.columns:
            y = pd.to_numeric(df["y"], errors="coerce").dropna()
            bounds_report["y_out_of_bounds"] = int(((y < 0) | (y > 100)).sum()) if not y.empty else 0

        ok = not any(i["severity"] == "ERROR" for i in issues)

        return {
            "ok": ok,
            "issues": issues,
            "bounds_report": bounds_report,
        }