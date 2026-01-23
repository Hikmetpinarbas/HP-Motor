from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import yaml

# ---- Type alias (prevents NameError in type hints)
RawArtifact = Union[pd.DataFrame, Dict[str, Any], Any]

from hp_motor.core.cdl_models import MetricValue
from hp_motor.core.evidence_models import EvidenceGraph, EvidenceNode, Hypothesis
from hp_motor.core.provenance import RunProvenance

# Viz layer (if present)
from hp_motor.viz.renderer import PlotRenderer, RenderContext
from hp_motor.viz.table_factory import TableFactory
from hp_motor.viz.list_factory import ListFactory

# Optional: mapping + validation (if you added them)
try:
    from hp_motor.ingest.provider_registry import ProviderRegistry
    from hp_motor.mapping.canonical_mapper import CanonicalMapper
    from hp_motor.validation.sot_validator import SOTValidator
except Exception:
    ProviderRegistry = None
    CanonicalMapper = None
    SOTValidator = None


BASE_DIR = Path(__file__).resolve().parents[1]  # .../src/hp_motor
REG_PATH = BASE_DIR / "registries" / "master_registry.yaml"
AO_DIR = BASE_DIR / "pipelines" / "analysis_objects"
PROVIDER_MAP_PATH = BASE_DIR / "registries" / "mappings" / "provider_generic_csv.yaml"


def _confidence_from_level(level: str) -> float:
    level = str(level or "medium").lower()
    return {"low": 0.35, "medium": 0.65, "high": 0.85}.get(level, 0.55)


def _pick_entity_id(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "entity"
    if "player_id" in df.columns:
        uniq = df["player_id"].dropna().unique().tolist()
        if len(uniq) == 1:
            return str(uniq[0])
    return "entity"


class SovereignOrchestrator:
    """
    Backward compatible orchestrator.

    - Keeps execute_full_analysis(artifact, phase) for your current app.py.
    - Provides execute(...) with richer outputs (tables/lists/figures).
    """

    def __init__(self, registry_path: Path = REG_PATH):
        self.registry_path = registry_path
        self.registry = self._load_registry(registry_path)

        # Optional mapping stack
        self.provider_registry = None
        self.mapper = None
        if ProviderRegistry is not None and PROVIDER_MAP_PATH.exists():
            self.provider_registry = ProviderRegistry(PROVIDER_MAP_PATH)
            self.mapper = CanonicalMapper(self.provider_registry) if CanonicalMapper is not None else None

        # Optional validator
        self.validator = SOTValidator(required_columns=[], allow_empty=False) if SOTValidator is not None else None

        # Renderers
        self.renderer = PlotRenderer()
        self.tf = TableFactory()
        self.lf = ListFactory()

    def _load_registry(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _load_analysis_object(self, analysis_object_id: str) -> Dict[str, Any]:
        p = AO_DIR / f"{analysis_object_id}.yaml"
        if not p.exists():
            raise FileNotFoundError(f"Analysis object not found: {p}")
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    # ---------------------------------------------------------------------
    # Backward-compat wrapper (your current Streamlit app uses this)
    # ---------------------------------------------------------------------
    def execute_full_analysis(self, artifact: RawArtifact, phase: str):
        """
        Old interface expected by older app.py:
          analysis = orchestrator.execute_full_analysis(df, phase)
          analysis['confidence'] used in UI.
        """
        if isinstance(artifact, pd.DataFrame):
            df = artifact
        else:
            # If something else arrives, try to coerce
            df = pd.DataFrame(artifact) if artifact is not None else pd.DataFrame()

        entity_id = _pick_entity_id(df)

        out = self.execute(
            analysis_object_id="player_role_fit",
            raw_df=df,
            entity_id=entity_id,
            role="Mezzala",
            phase=phase,
            source="artifact",
        )

        # Backward compatible "analysis" object for get_agent_verdict + UI
        # Your old agent likely expects: analysis['metrics'] and analysis['confidence']
        eg = out.get("evidence_graph") or {}
        overall = eg.get("overall_confidence", "medium")

        # Minimal legacy metrics
        metrics_map = {}
        for m in out.get("metrics", []) or []:
            mid = m.get("metric_id")
            val = m.get("value")
            if mid is not None:
                metrics_map[mid] = val

        legacy_metrics = {
            "PPDA": float(metrics_map.get("ppda", 12.0)) if metrics_map.get("ppda") is not None else 12.0,
            "xG": 0.0,
        }

        analysis = {
            "confidence": _confidence_from_level(overall),
            "metrics": legacy_metrics,
            "metadata": {"phase": phase, "entity_id": entity_id},
            # carry-through for richer UI if needed
            "tables": out.get("tables", {}),
            "lists": out.get("lists", {}),
            "figure_objects": out.get("figure_objects", {}),
            "raw": out,
        }
        return analysis

    # ---------------------------------------------------------------------
    # New interface (rich output)
    # ---------------------------------------------------------------------
    def execute(
        self,
        analysis_object_id: str,
        raw_df: pd.DataFrame,
        entity_id: str,
        role: Optional[str] = None,
        phase: str = "ACTION_GENERIC",
        source: str = "raw_df",
    ) -> Dict[str, Any]:
        ao = self._load_analysis_object(analysis_object_id)

        df = raw_df

        # Mapping (optional)
        mapping_report = {"ok": True, "provider_id": None, "mapping_hits": [], "rename_map": {}, "missing_required": []}
        if self.mapper is not None and isinstance(df, pd.DataFrame) and not df.empty:
            df, mapping_report = self.mapper.map_df(df, rename=True)

        # Validation (optional)
        data_quality = {"ok": True, "row_count": int(len(df)) if isinstance(df, pd.DataFrame) else 0, "issues": []}
        if self.validator is not None:
            # If AO declares required columns, apply
            required_cols = []
            ic = ao.get("input_contract") or {}
            if isinstance(ic, dict):
                required_cols = ic.get("required_columns", []) or []
            self.validator.required_columns = required_cols
            data_quality = self.validator.validate(df)

        if not data_quality.get("ok", True):
            return {
                "status": "BLOCKED",
                "analysis_object_id": analysis_object_id,
                "entity_id": str(entity_id),
                "role": role,
                "phase": phase,
                "data_quality": data_quality,
                "mapping_report": mapping_report,
                "missing_metrics": [],
                "metrics": [],
                "evidence_graph": {},
                "deliverables": {},
                "tables": {},
                "lists": {},
                "figure_objects": {},
                "figures": [],
            }

        # ---- Metric extraction (v1: mean of available columns)
        deliver = ao.get("deliverables", {}) or {}
        col_map = (ao.get("input", {}) or {}).get("col_map", {}) or {}

        def _col(mid: str) -> str:
            return col_map.get(mid, mid)

        required_metrics = deliver.get("required_metrics") or []
        if not required_metrics:
            required_metrics = [
                "xt_value",
                "ppda",
                "progressive_carries_90",
                "line_break_passes_90",
                "half_space_receives_90",
                "turnover_danger_index",
            ]

        metric_values: List[MetricValue] = []
        missing: List[str] = []

        for mid in required_metrics:
            c = _col(mid)
            if isinstance(df, pd.DataFrame) and c in df.columns:
                s = pd.to_numeric(df[c], errors="coerce")
                val = float(s.mean(skipna=True)) if s.notna().any() else None
            else:
                val = None

            if val is None:
                missing.append(mid)
                continue

            metric_values.append(
                MetricValue(
                    metric_id=mid,
                    entity_type="player",
                    entity_id=str(entity_id),
                    value=float(val),
                    unit=None,
                    scope=phase,
                    sample_size=int(df["minutes"].sum()) if isinstance(df, pd.DataFrame) and "minutes" in df.columns else None,
                )
            )

        # ---- Evidence graph (light v1)
        eg = EvidenceGraph(
            hypotheses=[
                Hypothesis(
                    hypothesis_id="H1",
                    claim=f"{role or 'Player'} role fit under {phase} constraints.",
                    scope={"phase": phase, "role": role, "entity_id": str(entity_id)},
                    falsifiers=[f"missing_metric:{m}" for m in missing],
                )
            ],
            nodes=[
                EvidenceNode(
                    node_id=f"M::{m.metric_id}",
                    axis="metrics",
                    ref={"metric_id": m.metric_id, "value": m.value},
                    strength=0.55,
                    note="Observed metric value",
                )
                for m in metric_values
            ],
            contradictions=[],
            overall_confidence="low" if len(missing) > 2 else "medium",
        )

        metric_map = {m.metric_id: m.value for m in metric_values}
        sample_minutes = next((m.sample_size for m in metric_values if getattr(m, "sample_size", None) is not None), None)

        ctx = RenderContext(theme=self.renderer.theme, sample_minutes=sample_minutes, source=source, uncertainty=None)

        figures: Dict[str, Any] = {}
        plot_ids = (deliver.get("plots") or []) if isinstance(deliver.get("plots"), list) else []
        for pid in plot_ids:
            if pid == "risk_scatter":
                spec = {"plot_id": pid, "type": "scatter", "axes": {"x": "xt_value", "y": "turnover_danger_index"}}
            elif pid == "role_radar":
                spec = {
                    "plot_id": pid,
                    "type": "radar",
                    "required_metrics": ["xt_value", "progressive_carries_90", "line_break_passes_90", "turnover_danger_index"],
                }
            elif pid == "half_space_touchmap":
                spec = {"plot_id": pid, "type": "pitch_heatmap"}
            elif pid == "xt_zone_overlay":
                spec = {"plot_id": pid, "type": "pitch_overlay"}
            else:
                continue
            figures[pid] = self.renderer.render(spec, df, metric_map, ctx)

        tables = {
            "evidence_table": self.tf.build_evidence_table(metric_values),
            "role_fit_table": self.tf.build_role_fit_table(
                role=role,
                fit_score=None,
                strengths=[],
                risks=[],
                confidence=eg.overall_confidence,
            ),
            "risk_uncertainty_table": self.tf.build_risk_uncertainty_table(eg, missing),
        }

        lists = {
            "role_tasks_checklist": self.lf.mezzala_tasks_pass_fail(metric_map),
            "top_sequences": self.lf.top_sequences_by_xt_involvement(df),
            "top_turnovers": self.lf.top_turnovers_by_danger(df),
        }

        prov = RunProvenance(
            run_id="run_v1",
            analysis_object_id=analysis_object_id,
            entity_id=str(entity_id),
            notes={"role": role, "phase": phase},
        )

        return {
            "status": "OK",
            "analysis_object_id": analysis_object_id,
            "entity_id": str(entity_id),
            "role": role,
            "phase": phase,
            "provenance": prov.model_dump(),
            "data_quality": data_quality,
            "mapping_report": mapping_report,
            "missing_metrics": missing,
            "metrics": [m.model_dump() for m in metric_values],
            "evidence_graph": eg.model_dump(),
            "deliverables": deliver,
            "tables": {k: v.to_dict(orient="records") for k, v in tables.items()},
            "lists": lists,
            "figure_objects": figures,
            "figures": list(figures.keys()),
        }