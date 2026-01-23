from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from hp_motor.viz.renderer import PlotRenderer, RenderContext
from hp_motor.viz.table_factory import TableFactory
from hp_motor.viz.list_factory import ListFactory


# -----------------------------
# Lightweight data models
# -----------------------------
@dataclass
class MetricValue:
    metric_id: str
    value: float
    sample_size: Optional[float] = None
    source: str = "raw_df"
    notes: Optional[str] = None


# -----------------------------
# Mapping + canonicalization
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
MAPPINGS_DIR = REPO_ROOT / "src" / "hp_motor" / "registries" / "mappings"


def _load_mapping(provider: str) -> Dict[str, List[str]]:
    p = MAPPINGS_DIR / f"provider_{provider}.yaml"
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
    return (data.get("columns") or {}) if isinstance(data, dict) else {}


def _canonicalize_columns(df: pd.DataFrame, provider: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Maps provider columns to canonical internal column names expected by metric extraction.
    Returns (canonical_df, report).
    """
    mapping = _load_mapping(provider)
    report = {"provider": provider, "hits": {}, "misses": [], "available_columns": list(df.columns)}

    if not mapping:
        # No mapping file; pass-through
        report["warning"] = f"Mapping file not found for provider={provider}. Using pass-through columns."
        return df.copy(), report

    out = df.copy()
    rename_map = {}

    # For each canonical key, find first matching existing column
    lower_cols = {str(c).lower(): c for c in out.columns}
    for canonical_key, aliases in mapping.items():
        found = None
        for a in aliases:
            a_l = str(a).lower()
            if a_l in lower_cols:
                found = lower_cols[a_l]
                break
        if found is not None:
            rename_map[found] = canonical_key
            report["hits"][canonical_key] = found
        else:
            report["misses"].append(canonical_key)

    out = out.rename(columns=rename_map)
    return out, report


def _choose_provider(df: pd.DataFrame) -> str:
    """
    Heuristic: try generic_csv mapping first; if it yields more hits, use it.
    """
    c_df, rep_csv = _canonicalize_columns(df, "generic_csv")
    c2_df, rep_xml = _canonicalize_columns(df, "generic_xml")

    hits_csv = len(rep_csv.get("hits", {}))
    hits_xml = len(rep_xml.get("hits", {}))

    return "generic_xml" if hits_xml > hits_csv else "generic_csv"


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _safe_mean(x: pd.Series) -> float:
    x = _to_numeric(x)
    if x.dropna().empty:
        return float("nan")
    return float(x.dropna().mean())


def _safe_sum(x: pd.Series) -> float:
    x = _to_numeric(x)
    if x.dropna().empty:
        return float("nan")
    return float(x.dropna().sum())


# -----------------------------
# Orchestrator
# -----------------------------
class SovereignOrchestrator:
    """
    v1.0: Minimal but real pipeline:
      - canonicalize columns via mapping YAML (generic_csv / generic_xml)
      - compute player_role_fit metric set
      - build evidence_graph + missing_metrics
      - generate tables/lists/figures for Streamlit UI
    """

    def __init__(self):
        self.renderer = PlotRenderer()
        self.table_factory = TableFactory()
        self.list_factory = ListFactory()

    def execute_full_analysis(self, artifact: pd.DataFrame, phase: str) -> Dict[str, Any]:
        # Backward-compatible wrapper (older UI paths)
        return self.execute(
            analysis_object_id="player_role_fit",
            raw_df=artifact,
            entity_id=str(artifact["player_id"].iloc[0]) if "player_id" in artifact.columns and len(artifact) else "entity",
            role="Mezzala",
            phase=phase,
        )

    def execute(
        self,
        analysis_object_id: str,
        raw_df: pd.DataFrame,
        entity_id: str,
        role: str = "Mezzala",
        phase: str = "ACTION_GENERIC",
    ) -> Dict[str, Any]:
        if raw_df is None or not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
            return {
                "status": "BLOCKED",
                "error": "raw_df is empty or invalid",
                "metrics": [],
                "missing_metrics": [],
                "evidence_graph": {"overall_confidence": "low", "notes": ["empty_input"]},
                "tables": {},
                "lists": {},
                "figure_objects": {},
                "mapping_report": {},
            }

        provider = _choose_provider(raw_df)
        df, mapping_report = _canonicalize_columns(raw_df, provider)

        # --- Filter entity if player_id exists
        if "player_id" in df.columns:
            df_entity = df[df["player_id"].astype(str) == str(entity_id)].copy()
            if df_entity.empty:
                # fallback: if entity not found, keep full df
                df_entity = df.copy()
        else:
            df_entity = df.copy()

        # --- Sample size (minutes)
        sample_minutes = None
        if "minutes" in df_entity.columns:
            sample_minutes = _safe_sum(df_entity["minutes"])
            if np.isnan(sample_minutes):
                sample_minutes = None

        # --- Compute metrics (player_role_fit minimal set)
        metric_values, missing = self._compute_player_role_fit_metrics(df_entity, sample_minutes)

        # --- Evidence graph (v1: simple)
        overall_conf = self._confidence_from_missing(missing, metric_values)
        evidence_graph = {
            "overall_confidence": overall_conf,
            "triangular_validation": {
                "axes": ["metrics", "benchmark", "document"],
                "min_axes": 2,
                "active_axes": ["metrics"],  # v1
            },
            "notes": [],
        }

        # --- Renderables
        metric_map = {m.metric_id: m.value for m in metric_values}
        ctx = RenderContext(
            theme=self.renderer.theme,
            sample_minutes=sample_minutes,
            source=provider,
            uncertainty=None,
        )

        # Plots requested (minimal v1)
        figures: Dict[str, Any] = {}
        plot_ids = ["risk_scatter", "role_radar", "half_space_touchmap", "xt_zone_overlay"]
        for pid in plot_ids:
            spec = self._plot_spec(pid)
            if spec is None:
                continue
            fig = self.renderer.render(spec, df_entity, metric_map, ctx)
            if fig is not None:
                figures[pid] = fig

        # Tables
        tables = {
            "evidence_table": self.table_factory.build_evidence_table(metric_values, evidence_graph),
            "role_fit_table": self.table_factory.build_role_fit_table(role=role, metric_map=metric_map, confidence=overall_conf),
            "risk_uncertainty_table": self.table_factory.build_risk_uncertainty_table(missing, evidence_graph),
        }

        # Lists
        lists = {
            "role_tasks_checklist": self.list_factory.mezzala_tasks_pass_fail(metric_map),
            "top_sequences": self.list_factory.top_sequences_by_xt_involvement(df_entity),
            "top_turnovers": self.list_factory.top_turnovers_by_danger(df_entity),
        }

        return {
            "status": "OK",
            "analysis_object_id": analysis_object_id,
            "entity_id": str(entity_id),
            "role": role,
            "phase": phase,
            "provider": provider,
            "mapping_report": mapping_report,
            "missing_metrics": missing,
            "metrics": [m.__dict__ for m in metric_values],
            "evidence_graph": evidence_graph,
            "tables": {k: v.to_dict(orient="records") for k, v in tables.items()},
            "lists": lists,
            "figure_objects": figures,  # Streamlit st.pyplot can use this directly
        }

    # -----------------------------
    # Internals
    # -----------------------------
    def _compute_player_role_fit_metrics(self, df: pd.DataFrame, sample_minutes: Optional[float]) -> Tuple[List[MetricValue], List[str]]:
        """
        Expects canonical columns (after mapping):
          minutes, xT, ppda, prog_carries_90, line_break_passes_90,
          half_space_receives_90, turnover_danger_90, x, y
        """
        out: List[MetricValue] = []
        missing: List[str] = []

        def add(metric_id: str, val: float):
            if val is None or (isinstance(val, float) and np.isnan(val)):
                missing.append(metric_id)
            else:
                out.append(MetricValue(metric_id=metric_id, value=float(val), sample_size=sample_minutes))

        # xT total (if event-level, sum is sensible; if already per90, you can later switch)
        if "xT" in df.columns:
            add("xt_value", _safe_sum(df["xT"]))
        else:
            add("xt_value", float("nan"))

        # ppda (team-level normally; if present in df, average)
        if "ppda" in df.columns:
            add("ppda", _safe_mean(df["ppda"]))
        else:
            add("ppda", float("nan"))

        # turnover danger per90 index
        if "turnover_danger_90" in df.columns:
            add("turnover_danger_index", _safe_mean(df["turnover_danger_90"]))
        else:
            add("turnover_danger_index", float("nan"))

        if "prog_carries_90" in df.columns:
            add("progressive_carries_90", _safe_mean(df["prog_carries_90"]))
        else:
            add("progressive_carries_90", float("nan"))

        if "line_break_passes_90" in df.columns:
            add("line_break_passes_90", _safe_mean(df["line_break_passes_90"]))
        else:
            add("line_break_passes_90", float("nan"))

        # half-space receives
        if "half_space_receives_90" in df.columns:
            add("half_space_receives", _safe_mean(df["half_space_receives_90"]))
        elif "half_space_receives" in df.columns:
            add("half_space_receives", _safe_mean(df["half_space_receives"]))
        else:
            add("half_space_receives", float("nan"))

        # role_benchmark_percentiles is placeholder v1 (not computable from raw df without norms)
        # Keep it present but mark missing so UI shows it.
        add("role_benchmark_percentiles", float("nan"))

        return out, missing

    def _confidence_from_missing(self, missing: List[str], metric_values: List[MetricValue]) -> str:
        # simple policy:
        # - high if >=5 metrics present and benchmark missing only
        # - medium if 3-4 present
        # - low otherwise
        present = len(metric_values)
        if present >= 5:
            return "high"
        if present >= 3:
            return "medium"
        return "low"

    def _plot_spec(self, plot_id: str) -> Optional[Dict[str, Any]]:
        if plot_id == "risk_scatter":
            return {"plot_id": plot_id, "type": "scatter", "axes": {"x": "xt_value", "y": "turnover_danger_index"}}
        if plot_id == "role_radar":
            return {
                "plot_id": plot_id,
                "type": "radar",
                "required_metrics": ["xt_value", "progressive_carries_90", "line_break_passes_90", "turnover_danger_index"],
            }
        if plot_id == "half_space_touchmap":
            return {"plot_id": plot_id, "type": "pitch_heatmap"}
        if plot_id == "xt_zone_overlay":
            return {"plot_id": plot_id, "type": "pitch_overlay"}
        return None