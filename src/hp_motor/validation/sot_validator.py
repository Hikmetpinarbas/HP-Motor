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
            if self.allow_empty:
                issues.append(ValidationIssue("DF_EMPTY", "Input dataframe is empty (allowed)", "WARN"))
            else:
                issues.append(ValidationIssue("DF_EMPTY", "Input dataframe is empty", "ERROR"))
            return self._finalize(report, issues)

        # Required columns presence
        missing = [c for c in self.required_columns if c not in df.columns]
        report["missing_required"] = missing
        if missing:
            issues.append(
                ValidationIssue(
                    "MISSING_REQUIRED",
                    f"Missing required columns: {missing}",
                    "ERROR",
                )
            )

        # Null distribution report (do not drop!)
        nulls = {}
        for c in df.columns:
            try:
                nulls[c] = float(pd.to_numeric(df[c], errors="ignore").isna().mean())
            except Exception:
                nulls[c] = float(df[c].isna().mean())
        report["null_report"] = nulls

        # Coordinate bounds checks (if present)
        xcol, ycol = self.coordinate_columns
        if xcol in df.columns and ycol in df.columns:
            x_min, x_max = self.coordinate_bounds[0]
            y_min, y_max = self.coordinate_bounds[1]

            x = pd.to_numeric(df[xcol], errors="coerce")
            y = pd.to_numeric(df[ycol], errors="coerce")

            oob_x = int(((x < x_min) | (x > x_max)).fillna(False).sum())
            oob_y = int(((y < y_min) | (y > y_max)).fillna(False).sum())

            report["bounds_report"] = {
                "x_out_of_bounds": oob_x,
                "y_out_of_bounds": oob_y,
                "bounds": {"x": [x_min, x_max], "y": [y_min, y_max]},
            }

            if oob_x > 0 or oob_y > 0:
                issues.append(
                    ValidationIssue(
                        "COORD_OOB",
                        f"Coordinate out-of-bounds detected (x:{oob_x}, y:{oob_y}). Expected x∈[{x_min},{x_max}] y∈[{y_min},{y_max}]",
                        "WARN",
                    )
                )

        return self._finalize(report, issues)

    def _finalize(self, report: Dict, issues: List[ValidationIssue]) -> Dict:
        report["issues"] = [i.__dict__ for i in issues]
        report["ok"] = not any(i.severity == "ERROR" for i in issues)
        return report