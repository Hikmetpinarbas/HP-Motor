from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from hp_motor.core.cognition import extract_cognitive_signals, extract_orientation_signals


@dataclass
class PlayerProfile:
    player_id: int
    summary: Dict[str, Any]
    metrics: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]


class IndividualReviewEngine:
    """
    Individual / Bireysel İnceleme v1.

    Output discipline:
      - If required signals are missing: abstain/degraded in summary, but still return diagnostics.
      - No fabricated numeric claims.
    """

    def build_player_profile(self, df: pd.DataFrame, player_id: int) -> PlayerProfile:
        if df is None or df.empty:
            return PlayerProfile(
                player_id=player_id,
                summary={"status": "ABSTAINED", "reason": "empty_df", "confidence": "low"},
                metrics=[],
                diagnostics={"missing_columns": ["player_id"]},
            )

        if "player_id" not in df.columns:
            return PlayerProfile(
                player_id=player_id,
                summary={"status": "ABSTAINED", "reason": "missing_player_id_column", "confidence": "low"},
                metrics=[],
                diagnostics={"missing_columns": ["player_id"]},
            )

        w = df[df["player_id"].astype(str) == str(player_id)].copy()
        if w.empty:
            return PlayerProfile(
                player_id=player_id,
                summary={"status": "ABSTAINED", "reason": "no_rows_for_player", "confidence": "low"},
                metrics=[],
                diagnostics={"row_count_player": 0},
            )

        diagnostics: Dict[str, Any] = {"row_count_player": int(len(w))}

        # -------------------------
        # Cognitive signals
        # -------------------------
        cog = extract_cognitive_signals(w)
        ori = extract_orientation_signals(w)

        # Pressure-conditioned decision speed if possible
        pressure_metrics, pressure_diag = self._pressure_conditioned_speed(w)
        diagnostics.update(pressure_diag)

        metrics: List[Dict[str, Any]] = []

        if cog.decision_speed_mean_s is not None:
            metrics.append({"metric_id": "decision_speed_mean_s", "value": float(cog.decision_speed_mean_s), "unit": "sec"})
        if cog.scan_freq_10s is not None:
            metrics.append({"metric_id": "scan_freq_10s", "value": float(cog.scan_freq_10s), "unit": "hz"})
        if cog.contextual_awareness_score is not None:
            metrics.append({"metric_id": "contextual_awareness_score", "value": float(cog.contextual_awareness_score), "unit": "0..1"})
        metrics.append({"metric_id": "cognitive_note", "value": cog.note})

        # Orientation signals (only if present in data)
        if ori.defender_side_on_score is not None:
            metrics.append({"metric_id": "defender_side_on_score", "value": float(ori.defender_side_on_score), "unit": "0..1"})
        if ori.square_on_rate is not None:
            metrics.append({"metric_id": "square_on_rate", "value": float(ori.square_on_rate), "unit": "0..1"})
        if ori.channeling_to_wing_rate is not None:
            metrics.append({"metric_id": "channeling_to_wing_rate", "value": float(ori.channeling_to_wing_rate), "unit": "0..1"})
        metrics.append({"metric_id": "orientation_note", "value": ori.note})

        metrics.extend(pressure_metrics)

        # -------------------------
        # Summary: conservative banding
        # -------------------------
        missing = []
        if cog.decision_speed_mean_s is None:
            missing.append("decision_speed_mean_s")
        if cog.scan_freq_10s is None and "scan_count_10s" not in w.columns:
            missing.append("scan_freq_10s")
        if cog.contextual_awareness_score is None:
            missing.append("contextual_awareness_score")

        confidence = "medium"
        if len(missing) >= 2:
            confidence = "low"
        if cog.contextual_awareness_score is not None and cog.contextual_awareness_score >= 0.75 and confidence != "low":
            confidence = "high"

        status = "OK" if len(missing) == 0 else "DEGRADED"
        if len(missing) == 3:
            status = "ABSTAINED"

        summary = {
            "status": status,
            "player_id": int(player_id),
            "confidence": confidence,
            "missing": missing,
            "headline": self._headline(cog.contextual_awareness_score, cog.decision_speed_mean_s, pressure_diag),
            "limits": [
                "Scanning proxy is indirect (event timestamps / provided scan columns).",
                "Body orientation proxy requires tracking/video; only column-based signals are used.",
            ],
        }

        return PlayerProfile(player_id=int(player_id), summary=summary, metrics=metrics, diagnostics=diagnostics)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _pressure_conditioned_speed(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Looks for pressure indicator columns:
          - pressure (0/1 or intensity)
          - under_pressure (0/1)
          - is_pressured (0/1)

        Uses timestamps if available: (timestamp_end - timestamp_start) OR (t2 - t1)
        """
        diag: Dict[str, Any] = {}
        metrics: List[Dict[str, Any]] = []

        # Find delta_t
        if "timestamp_start" in df.columns and "timestamp_end" in df.columns:
            t1 = pd.to_numeric(df["timestamp_start"], errors="coerce")
            t2 = pd.to_numeric(df["timestamp_end"], errors="coerce")
            delta = (t2 - t1).astype("float64")
        elif "t1" in df.columns and "t2" in df.columns:
            t1 = pd.to_numeric(df["t1"], errors="coerce")
            t2 = pd.to_numeric(df["t2"], errors="coerce")
            delta = (t2 - t1).astype("float64")
        else:
            diag["pressure_speed_note"] = "no_timestamp_columns"
            return metrics, diag

        # Pressure flag
        pcol = None
        for c in ["under_pressure", "is_pressured", "pressure"]:
            if c in df.columns:
                pcol = c
                break
        if pcol is None:
            diag["pressure_speed_note"] = "no_pressure_column"
            return metrics, diag

        p = pd.to_numeric(df[pcol], errors="coerce")
        pressured = p.fillna(0) > 0

        base = delta[pd.notna(delta)]
        if base.notna().sum() == 0:
            diag["pressure_speed_note"] = "delta_all_nan"
            return metrics, diag

        dp = delta[pressured & pd.notna(delta)]
        dn = delta[(~pressured) & pd.notna(delta)]

        diag["pressure_column"] = pcol
        diag["pressure_rows"] = int(pressured.sum())
        diag["non_pressure_rows"] = int((~pressured).sum())

        if dp.notna().sum() > 0:
            metrics.append({"metric_id": "decision_speed_pressured_mean_s", "value": float(dp.mean()), "unit": "sec"})
        if dn.notna().sum() > 0:
            metrics.append({"metric_id": "decision_speed_unpressured_mean_s", "value": float(dn.mean()), "unit": "sec"})

        if dp.notna().sum() > 0 and dn.notna().sum() > 0:
            # ratio >1 => slower under pressure
            ratio = float(dp.mean()) / float(dn.mean()) if float(dn.mean()) != 0 else None
            if ratio is not None:
                metrics.append({"metric_id": "pressure_speed_ratio", "value": float(ratio), "unit": "x"})
        return metrics, diag

    @staticmethod
    def _headline(awareness: Optional[float], decision_s: Optional[float], pressure_diag: Dict[str, Any]) -> str:
        if awareness is None and decision_s is None:
            return "Yetersiz bilişsel sinyal: veri bu oyuncu için konuşmuyor."
        parts = []
        if awareness is not None:
            if awareness >= 0.75:
                parts.append("Contextual awareness güçlü")
            elif awareness >= 0.55:
                parts.append("Awareness orta bant")
            else:
                parts.append("Awareness zayıf bant")
        if decision_s is not None:
            if decision_s <= 0.8:
                parts.append("karar hızı elite")
            elif decision_s <= 1.2:
                parts.append("karar hızı ortalama")
            else:
                parts.append("karar hızı yavaş")
        if pressure_diag.get("pressure_column"):
            parts.append("baskı koşullu hız üretildi")
        return " • ".join(parts) 