from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from hp_motor.core.cognition import extract_cognitive_signals, extract_orientation_signals
from hp_motor.core.template_renderer import TemplateRenderer
from hp_motor.modules.role_mismatch_alarm import RoleMismatchAlarmEngine, Answer


@dataclass
class PlayerProfile:
    player_id: int
    summary: Dict[str, Any]
    metrics: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]
    # v22.x derived artifacts
    player_analysis_markdown: str
    scouting_card_markdown: str
    role_mismatch_alarm_markdown: str
    role_mismatch_alarm: Dict[str, Any]


class IndividualReviewEngine:
    """
    HP ENGINE v22.x — Individual Review (core)

    Contract:
      - No fabricated numeric claims.
      - Returns metrics + diagnostics.
      - Derives downstream artifacts via canonical templates:
          - Player Analysis v22 Markdown
          - Scouting Card v22 Markdown
          - Role Mismatch Alarm Markdown
    """

    ENGINE_VERSION = "HP ENGINE v22.x"

    def __init__(self) -> None:
        self.alarm_engine = RoleMismatchAlarmEngine()
        self.renderer = TemplateRenderer()

    def build_player_profile(
        self,
        df: pd.DataFrame,
        player_id: int,
        *,
        # meta/context is optional; module is name-free by default
        role_id: str = "mezzala",
        alarm_answers: Optional[Dict[str, Answer]] = None,
        alarm_live_triggers: Optional[List[bool]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PlayerProfile:
        diagnostics: Dict[str, Any] = {"role_id": role_id}
        context = context or {}

        # Hard gates
        if df is None or df.empty:
            alarm = self.alarm_engine.score(
                answers=alarm_answers or {},
                live_triggers=alarm_live_triggers or [],
                context_note="empty_df",
            )
            pa_md = self._player_analysis_min(player_id, reason="empty_df")
            sc_md = self._scouting_card_min(player_id, reason="empty_df")
            return PlayerProfile(
                player_id=int(player_id),
                summary={"status": "ABSTAINED", "reason": "empty_df", "confidence": "low"},
                metrics=[],
                diagnostics=diagnostics,
                player_analysis_markdown=pa_md,
                scouting_card_markdown=sc_md,
                role_mismatch_alarm_markdown=alarm.markdown,
                role_mismatch_alarm=alarm.__dict__,
            )

        if "player_id" not in df.columns:
            alarm = self.alarm_engine.score(
                answers=alarm_answers or {},
                live_triggers=alarm_live_triggers or [],
                context_note="missing_player_id_column",
            )
            pa_md = self._player_analysis_min(player_id, reason="missing_player_id_column")
            sc_md = self._scouting_card_min(player_id, reason="missing_player_id_column")
            return PlayerProfile(
                player_id=int(player_id),
                summary={"status": "ABSTAINED", "reason": "missing_player_id_column", "confidence": "low"},
                metrics=[],
                diagnostics={"missing_columns": ["player_id"], **diagnostics},
                player_analysis_markdown=pa_md,
                scouting_card_markdown=sc_md,
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
            pa_md = self._player_analysis_min(player_id, reason="no_rows_for_player")
            sc_md = self._scouting_card_min(player_id, reason="no_rows_for_player")
            return PlayerProfile(
                player_id=int(player_id),
                summary={"status": "ABSTAINED", "reason": "no_rows_for_player", "confidence": "low"},
                metrics=[],
                diagnostics=diagnostics,
                player_analysis_markdown=pa_md,
                scouting_card_markdown=sc_md,
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

        # Role mismatch alarm: unknown -> conservative half-risk
        alarm = self.alarm_engine.score(
            answers=alarm_answers or {},
            live_triggers=alarm_live_triggers or [],
            context_note=f"role_id={role_id}; player_id={player_id}",
        )

        # Render canonical v22 templates (no hallucination)
        player_analysis_md = self._render_player_analysis_v22(
            player_id=int(player_id),
            role_id=role_id,
            summary=summary,
            metrics=metrics,
            cog_note=str(cog.note or ""),
            ori_note=str(ori.note or ""),
            context=context,
        )

        scouting_card_md = self._render_scouting_card_v22(
            player_id=int(player_id),
            role_id=role_id,
            summary=summary,
            metrics=metrics,
            alarm=alarm,
            context=context,
        )

        return PlayerProfile(
            player_id=int(player_id),
            summary=summary,
            metrics=metrics,
            diagnostics=diagnostics,
            player_analysis_markdown=player_analysis_md,
            scouting_card_markdown=scouting_card_md,
            role_mismatch_alarm_markdown=alarm.markdown,
            role_mismatch_alarm=alarm.__dict__,
        )

    # ------------------------------------------------------------
    # Minimal fallbacks (stable)
    # ------------------------------------------------------------
    @staticmethod
    def _player_analysis_min(player_id: int, reason: str) -> str:
        return (
            "# HP ENGINE v22.x — Bireysel Oyuncu Analizi (ABSTAINED)\n\n"
            f"Oyuncu: (player_id={player_id})\n\n"
            f"> Veri yetersiz / gate: {reason}\n"
        )

    @staticmethod
    def _scouting_card_min(player_id: int, reason: str) -> str:
        return (
            "# HP ENGINE v22.x — Scouting Card (ABSTAINED)\n\n"
            f"OYUNCU: (player_id={player_id})\n\n"
            f"> Veri yetersiz / gate: {reason}\n"
        )

    # ------------------------------------------------------------
    # Template renderers (v22)
    # ------------------------------------------------------------
    @staticmethod
    def _mget(metrics: List[Dict[str, Any]], metric_id: str) -> Any:
        for m in metrics:
            if m.get("metric_id") == metric_id:
                return m.get("value")
        return None

    @staticmethod
    def _fmt(v: Any, *, digits: int = 2) -> str:
        if v is None:
            return "—"
        try:
            if isinstance(v, (int, float)):
                return f"{float(v):.{digits}f}"
        except Exception:
            pass
        s = str(v).strip()
        return s if s else "—"

    def _render_player_analysis_v22(
        self,
        *,
        player_id: int,
        role_id: str,
        summary: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        cog_note: str,
        ori_note: str,
        context: Dict[str, Any],
    ) -> str:
        tpl = self.renderer.load("player_analysis_v22.md")
        if not tpl:
            return self._player_analysis_min(player_id, reason="template_missing")

        # We do not have per-90 xG/xA/key passes etc from event logs in this engine.
        # Keep them blank (—). Cognitive/orientation goes into commentary fields.
        ctx = {
            "player_name": context.get("player_name", "—"),
            "club": context.get("club", "—"),
            "league": context.get("league", "—"),
            "season": context.get("season", "—"),
            "analyst": context.get("analyst", "—"),
            "analysis_date": context.get("analysis_date", "—"),
            "engine_version": self.ENGINE_VERSION,

            "age": context.get("age", "—"),
            "height_weight": context.get("height_weight", "—"),
            "dominant_foot": context.get("dominant_foot", "—"),
            "primary_position": context.get("primary_position", "—"),
            "secondary_positions": context.get("secondary_positions", "—"),
            "career_phase": context.get("career_phase", "—"),
            "one_liner_definition": context.get("one_liner_definition", summary.get("headline", "—")),

            "primary_role": context.get("primary_role", role_id),
            "secondary_role": context.get("secondary_role", "—"),
            "bad_roles": context.get("bad_roles", "—"),
            "role_freedom": context.get("role_freedom", "—"),

            # Numeric profile (unknown in this engine → abstain placeholders)
            "dribble_success": "—",
            "dribble_pctile": "—",
            "turnovers": "—",
            "turnovers_pctile": "—",
            "xg": "—",
            "xg_pctile": "—",
            "xa": "—",
            "xa_pctile": "—",
            "key_passes": "—",
            "key_passes_pctile": "—",
            "shots": "—",
            "shots_pctile": "—",

            "numeric_profile_commentary": (
                "Bu veri setinde klasik per90 üretimi (xG/xA/şut/anahtar pas/dripling) için "
                "gerekli provider kolonları yoksa sistem uydurmaz. "
                f"\n\nBilişsel sinyal notu: {cog_note or '—'}"
                f"\n\nOryantasyon sinyal notu: {ori_note or '—'}"
            ),

            # Biomechanics (tracking/video needed)
            "somatotype": context.get("somatotype", "—"),
            "explosiveness": context.get("explosiveness", "—"),
            "max_speed": context.get("max_speed", "—"),
            "repeat_sprint": context.get("repeat_sprint", "—"),
            "stamina": context.get("stamina", "—"),
            "injury_history": context.get("injury_history", "—"),
            "orientation_notes": context.get("orientation_notes", ori_note or "—"),

            # Decision tree
            "common_actions": "—",
            "pressure_behavior": "—",

            # Tactical effect map (needs x/y/end_x/end_y + zones)
            "best_zones": "—",
            "worst_zones": "—",
            "box_contribution": "—",
            "production_geometry": "—",

            # Psychological profile (human input)
            "role_clarity_need": context.get("role_clarity_need", "—"),
            "freedom_tolerance": context.get("freedom_tolerance", "—"),
            "post_error_reaction": context.get("post_error_reaction", "—"),
            "confidence_perf_link": context.get("confidence_perf_link", "—"),

            # Coaching notes
            "how_to_use": context.get("how_to_use", "—"),
            "how_not_to_use": context.get("how_not_to_use", "—"),
            "support_needs": context.get("support_needs", "—"),

            # Risks
            "tactical_risks": context.get("tactical_risks", "—"),
            "physical_risks": context.get("physical_risks", "—"),
            "psych_risks": context.get("psych_risks", "—"),

            # Fit score
            "fit_team": context.get("fit_team", "—"),
            "fit_league": context.get("fit_league", "—"),
            "fit_coach": context.get("fit_coach", "—"),

            # Executive summary
            "executive_summary": context.get("executive_summary", summary.get("headline", "—")),
        }

        return self.renderer.render(tpl, ctx)

    def _render_scouting_card_v22(
        self,
        *,
        player_id: int,
        role_id: str,
        summary: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        alarm: Any,
        context: Dict[str, Any],
    ) -> str:
        tpl = self.renderer.load("scouting_card_v22.md")
        if not tpl:
            return self._scouting_card_min(player_id, reason="template_missing")

        # We can place cognitive proxy into the “one sentence” if no human one-liner exists.
        one_sentence = context.get("one_sentence_verdict")
        if not one_sentence:
            one_sentence = summary.get("headline", "—")

        # Numeric core per 90: not available here -> abstain placeholders.
        ctx = {
            "player_name": context.get("player_name", f"(player_id={player_id})"),
            "club_league_season": context.get("club_league_season", "—"),
            "position_role": context.get("position_role", role_id),
            "dominant_foot": context.get("dominant_foot", "—"),
            "age_height_weight": context.get("age_height_weight", "—"),

            "one_sentence_verdict": one_sentence,

            "xg": "—",
            "xa": "—",
            "key_passes": "—",
            "shots": "—",
            "dribble_success": "—",
            "turnovers": "—",

            "archetype": context.get("archetype", "—"),
            "best_zone": context.get("best_zone", "—"),
            "main_weapons": context.get("main_weapons", "—"),
            "main_limits": context.get("main_limits", "—"),

            "usage_1": context.get("usage_1", "—"),
            "usage_2": context.get("usage_2", "—"),
            "usage_3": context.get("usage_3", "—"),

            "need_overlap": context.get("need_overlap", "BILINMIYOR"),
            "need_wall_station": context.get("need_wall_station", "BILINMIYOR"),
            "need_9_anchor": context.get("need_9_anchor", "BILINMIYOR"),
            "need_far_post_runner": context.get("need_far_post_runner", "BILINMIYOR"),

            # Risks: we can inject role-mismatch band as tactical warning if high
            "risk_tactical": context.get("risk_tactical", f"Rol alarm bandı: {getattr(alarm, 'band_after_triggers', getattr(alarm, 'band', '—'))}"),
            "risk_physical": context.get("risk_physical", "—"),
            "risk_psychological": context.get("risk_psychological", "—"),

            "fit_team": context.get("fit_team", "—"),
            "fit_league": context.get("fit_league", "—"),
            "fit_coach": context.get("fit_coach", "—"),
        }

        return self.renderer.render(tpl, ctx)

    # ------------------------------------------------------------
    # Headline
    # ------------------------------------------------------------
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