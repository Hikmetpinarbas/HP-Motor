from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from hp_motor.core.cognition import extract_cognitive_signals, extract_orientation_signals
from hp_motor.modules.role_mismatch_alarm import RoleMismatchAlarmEngine, Answer


@dataclass
class PlayerProfile:
    player_id: int
    summary: Dict[str, Any]
    metrics: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]
    # v22.x derived artifacts
    scouting_card_markdown: str
    role_mismatch_alarm_markdown: str
    role_mismatch_alarm: Dict[str, Any]


class IndividualReviewEngine:
    """
    HP ENGINE v22.x — Individual Review (core)

    Contract:
      - No fabricated numeric claims.
      - Returns metrics + diagnostics.
      - Derives downstream artifacts:
          - Scouting Card (already in system)
          - Role Mismatch Alarm Checklist (this request)
    """

    ENGINE_VERSION = "HP ENGINE v22.x"

    def __init__(self) -> None:
        self.alarm_engine = RoleMismatchAlarmEngine()

    def build_player_profile(
        self,
        df: pd.DataFrame,
        player_id: int,
        *,
        # meta/context is optional; module is name-free by default
        role_id: str = "mezzala",
        alarm_answers: Optional[Dict[str, Answer]] = None,
        alarm_live_triggers: Optional[List[bool]] = None,
    ) -> PlayerProfile:
        diagnostics: Dict[str, Any] = {"role_id": role_id}

        # Hard gates
        if df is None or df.empty:
            alarm = self.alarm_engine.score(
                answers=alarm_answers or {},
                live_triggers=alarm_live_triggers or [],
                context_note="empty_df",
            )
            return PlayerProfile(
                player_id=int(player_id),
                summary={"status": "ABSTAINED", "reason": "empty_df", "confidence": "low"},
                metrics=[],
                diagnostics=diagnostics,
                scouting_card_markdown=self._scouting_card_min(player_id),
                role_mismatch_alarm_markdown=alarm.markdown,
                role_mismatch_alarm=alarm.__dict__,
            )

        if "player_id" not in df.columns:
            alarm = self.alarm_engine.score(
                answers=alarm_answers or {},
                live_triggers=alarm_live_triggers or [],
                context_note="missing_player_id_column",
            )
            return PlayerProfile(
                player_id=int(player_id),
                summary={"status": "ABSTAINED", "reason": "missing_player_id_column", "confidence": "low"},
                metrics=[],
                diagnostics={"missing_columns": ["player_id"], **diagnostics},
                scouting_card_markdown=self._scouting_card_min(player_id),
                role_mismatch_alarm_markdown=alarm.markdown,
                role_mismatch_alarm=alarm.__dict__,
            )

        w = df[df["player_id"].astype(str) == str(player_id)].copy()
        diagnostics["row_count_player"] = int(len(w))

        if w.empty:
            alarm = self.alarm_engine.score(
                answers=alarm_answers or {},
                live_triggers=alarm_live_triggers or [],
                context_note="no_rows_for_player",
            )
            return PlayerProfile(
                player_id=int(player_id),
                summary={"status": "ABSTAINED", "reason": "no_rows_for_player", "confidence": "low"},
                metrics=[],
                diagnostics=diagnostics,
                scouting_card_markdown=self._scouting_card_min(player_id),
                role_mismatch_alarm_markdown=alarm.markdown,
                role_mismatch_alarm=alarm.__dict__,
            )

        # Extract signals
        cog = extract_cognitive_signals(w)
        ori = extract_orientation_signals(w)

        metrics: List[Dict[str, Any]] = []
        missing: List[str] = []

        if cog.decision_speed_mean_s is not None:
            metrics.append({"metric_id": "decision_speed_mean_s", "value": float(cog.decision_speed_mean_s), "unit": "sec"})
        else:
            missing.append("decision_speed_mean_s")

        if cog.scan_freq_10s is not None:
            metrics.append({"metric_id": "scan_freq_10s", "value": float(cog.scan_freq_10s), "unit": "hz"})
        else:
            missing.append("scan_freq_10s")

        if cog.contextual_awareness_score is not None:
            metrics.append({"metric_id": "contextual_awareness_score", "value": float(cog.contextual_awareness_score), "unit": "0..1"})
        else:
            missing.append("contextual_awareness_score")

        metrics.append({"metric_id": "cognitive_note", "value": cog.note})

        if ori.defender_side_on_score is not None:
            metrics.append({"metric_id": "defender_side_on_score", "value": float(ori.defender_side_on_score), "unit": "0..1"})
        if ori.square_on_rate is not None:
            metrics.append({"metric_id": "square_on_rate", "value": float(ori.square_on_rate), "unit": "0..1"})
        if ori.channeling_to_wing_rate is not None:
            metrics.append({"metric_id": "channeling_to_wing_rate", "value": float(ori.channeling_to_wing_rate), "unit": "0..1"})
        metrics.append({"metric_id": "orientation_note", "value": ori.note})

        # Summary bands (conservative)
        confidence = "medium"
        if len(missing) >= 2:
            confidence = "low"
        if cog.contextual_awareness_score is not None and cog.contextual_awareness_score >= 0.75 and confidence != "low":
            confidence = "high"

        status = "OK" if len(missing) == 0 else "DEGRADED"
        if len(missing) >= 3:
            status = "ABSTAINED"

        summary = {
            "status": status,
            "player_id": int(player_id),
            "confidence": confidence,
            "missing": missing,
            "headline": self._headline(cog.contextual_awareness_score, cog.decision_speed_mean_s),
        }

        diagnostics["missing_metrics"] = missing

        # Derived artifacts
        scouting_card_md = self._scouting_card_from_metrics(player_id=int(player_id), role_id=role_id, summary=summary, metrics=metrics)

        # Role mismatch alarm: answer set may be empty; unknown -> conservative half-risk
        alarm = self.alarm_engine.score(
            answers=alarm_answers or {},
            live_triggers=alarm_live_triggers or [],
            context_note=f"role_id={role_id}; player_id={player_id}",
        )

        return PlayerProfile(
            player_id=int(player_id),
            summary=summary,
            metrics=metrics,
            diagnostics=diagnostics,
            scouting_card_markdown=scouting_card_md,
            role_mismatch_alarm_markdown=alarm.markdown,
            role_mismatch_alarm=alarm.__dict__,
        )

    # ------------------------------------------------------------
    # Minimal Scouting Card (stable placeholder; the full card is already tracked in your template module)
    # ------------------------------------------------------------
    @staticmethod
    def _scouting_card_min(player_id: int) -> str:
        return (
            "# HP ENGINE v22.x — Scouting Card (ABSTAINED)\n\n"
            f"OYUNCU: (player_id={player_id})\n\n"
            "> Veri yetersiz: tek sayfalık karar kartı bağlam gerektirir.\n"
        )

    @staticmethod
    def _scouting_card_from_metrics(player_id: int, role_id: str, summary: Dict[str, Any], metrics: List[Dict[str, Any]]) -> str:
        # deliberately conservative; numeric core is not fabricated
        def _get(mid: str) -> str:
            for m in metrics:
                if m.get("metric_id") == mid:
                    v = m.get("value")
                    return "" if v is None else str(v)
            return ""

        return (
            "# HP ENGINE v22.x — Scouting Card (Auto / Conservative)\n\n"
            f"OYUNCU: (player_id={player_id})\n"
            f"POZİSYON / ROL: {role_id}\n\n"
            "## 1) TEK CÜMLELİK HÜKÜM\n\n"
            f"> {summary.get('headline','')}\n\n"
            "## 2) SAYISAL ÇEKİRDEK (Proxy)\n\n"
            "| DecisionSpeed(s) | Awareness(0..1) | ScanFreq(Hz) |\n"
            "|---:|---:|---:|\n"
            f"| {_get('decision_speed_mean_s')} | {_get('contextual_awareness_score')} | {_get('scan_freq_10s')} |\n"
        )

    @staticmethod
    def _headline(awareness: Optional[float], decision_s: Optional[float]) -> str:
        if awareness is None and decision_s is None:
            return "Yetersiz bilişsel sinyal: veri bu oyuncu için konuşmuyor."
        parts = []
        if awareness is not None:
            if awareness >= 0.75:
                parts.append("Awareness güçlü bant")
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
        return " • ".join(parts)