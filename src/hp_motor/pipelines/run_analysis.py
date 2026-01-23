from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml
import pandas as pd

from hp_motor.core.cdl_models import MetricValue
from hp_motor.core.evidence_models import EvidenceGraph, EvidenceNode, Hypothesis
from hp_motor.core.provenance import RunProvenance


REG_PATH = Path(__file__).resolve().parents[1] / "registries" / "master_registry.yaml"
ANALYSIS_DIR = Path(__file__).resolve().parent / "analysis_objects"


class SovereignOrchestrator:
    def __init__(self, registry_path: Path = REG_PATH):
        with registry_path.open("r", encoding="utf-8") as f:
            self.registry = yaml.safe_load(f)["registry"]

    def _load_analysis_object(self, analysis_id: str) -> Dict[str, Any]:
        path = ANALYSIS_DIR / f"{analysis_id}.yaml"
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)["analysis"]

    def execute(self, analysis_object_id: str, raw_df: pd.DataFrame, entity_id: str, role: str = "Mezzala") -> Dict[str, Any]:
        ao = self._load_analysis_object(analysis_object_id)

        prov = RunProvenance(
            run_id=f"run_{analysis_object_id}_{entity_id}",
            registry_version=self.registry["version"],
        )

        # 1) Metrics (v1.0 minimal): compute only what exists in raw_df; others flagged as missing
        metric_values: List[MetricValue] = []
        missing: List[str] = []

        for mid in ao["metric_bundle"]:
            mv = self._compute_metric(mid, raw_df, entity_id)
            if mv is None:
                missing.append(mid)
            else:
                metric_values.append(mv)

        # fail-closed if required and too many missing
        if ao["evidence_policy"]["fail_closed"] and len(metric_values) < 2:
            return {
                "status": "UNKNOWN",
                "reason": "Insufficient metrics to satisfy evidence policy.",
                "missing_metrics": missing,
            }

        # 2) Evidence graph (v1.0 minimal triangular: metrics + benchmark/doc optional)
        eg = self._build_evidence_graph(metric_values, role)

        # 3) Deliverables (spec ids only; rendering wired later)
        return {
            "status": "OK",
            "analysis_object": ao,
            "metrics": [m.model_dump() for m in metric_values],
            "missing_metrics": missing,
            "evidence_graph": eg.model_dump(),
            "deliverables": ao["deliverables"],
            "provenance": prov.__dict__,
        }

    def _compute_metric(self, metric_id: str, df: pd.DataFrame, entity_id: str) -> MetricValue | None:
        # v1.0: lightweight mapping to existing columns
        # Later: true Metric Factory based on registry.metrics definitions.
        col_map = {
            "ppda": "ppda",
            "xt_value": "xT",
            "progressive_carries_90": "prog_carries_90",
            "line_break_passes_90": "line_break_passes_90",
            "half_space_receives": "half_space_receives_90",
            "turnover_danger_index": "turnover_danger_90",
            "role_benchmark_percentiles": None,  # computed from norms; v1.1
        }
        col = col_map.get(metric_id)
        if col is None:
            return None
        if col not in df.columns:
            return None

        # assume df already filtered to entity; else filter by player_id if present
        if "player_id" in df.columns:
            sdf = df[df["player_id"] == entity_id]
        else:
            sdf = df

        if sdf.empty:
            return None

        value = float(sdf[col].mean())
        return MetricValue(
            metric_id=metric_id,
            entity_type="player",
            entity_id=entity_id,
            value=value,
            unit=None,
            scope="open_play",
            sample_size=float(sdf["minutes"].sum()) if "minutes" in sdf.columns else None,
            source="raw_df",
            uncertainty=None,
        )

    def _build_evidence_graph(self, metrics: List[MetricValue], role: str) -> EvidenceGraph:
        # v1.0: minimal hypotheses + nodes; v1.5 adds contradiction graph and uncertainty engine.
        h1 = Hypothesis(
            hypothesis_id="H1_role_fit",
            claim=f"{role} rol uyumu yüksek.",
            falsifiers=[
                "xt_value low",
                "turnover_danger_index high",
            ],
        )

        nodes = []
        for i, mv in enumerate(metrics):
            nodes.append(
                EvidenceNode(
                    node_id=f"N{i+1}",
                    axis="metrics",
                    ref={"metric_id": mv.metric_id, "value": mv.value},
                    strength=0.6,
                    note=None,
                )
            )

        eg = EvidenceGraph(hypotheses=[h1], nodes=nodes, contradictions=[], overall_confidence="medium")
        return eg