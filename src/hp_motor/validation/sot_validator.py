from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "WARN"  # WARN | ERROR


class SOTValidator:
    """
    SOT (Single Source of Truth) veri kalite kapısı.

    Core rules:
      - NO silent dropping rows.
      - 0.0 is valid.
      - Produce a Data Quality Report.
    """

    def __init__(
        self,
        required_columns: Optional[List[str]] = None,
        coordinate_columns: Tuple[str, str] = ("x", "y"),
        coordinate_bounds: Tuple[Tuple[float, float], Tuple[float, float]] = ((0.0, 105.0), (0.0, 68.0)),
        allow_empty: bool = False,
    ):
        self.required_columns = required_columns or []
        self.coordinate_columns = coordinate_columns
        self.coordinate_bounds = coordinate_bounds
        self.allow_empty = allow_empty

    def validate(self, df: pd.DataFrame) -> Dict:
        issues: List[ValidationIssue] = []
        report: Dict = {
            "ok": True,
            "row_count": int(len(df)) if df is not None else 0,
            "missing_required": [],
            "null_report": {},
            "bounds_report": {},
            "issues": [],
        }

        if df is None:
            issues.append(ValidationIssue("DF_NONE", "Input dataframe is None", "ERROR"))
            return self._finalize(report, issues)

        if df.empty:
            if self.allow_empty