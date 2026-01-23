from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from hp_motor.core.cdl_models import MetricValue
from hp_motor.core.evidence_models import EvidenceGraph


class TableFactory:
    def build_evidence_table(self, metrics: List[MetricValue]) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for mv in metrics:
            rows.append({
                "metric": mv.metric_id,
                "value": mv.value,
                "percentile": None,  # v1.1 norms
                "scope": mv.scope,
                "sample": mv.sample_size,
                "source": mv.source,
                "uncertainty": mv.uncertainty,
            })
        return pd.DataFrame(rows)

    def build_role_fit_table(
        self,
        role: str,
        fit_score: Optional[float],
        strengths: List[str],
        risks: List[str],
        confidence: str,
    ) -> pd.DataFrame:
        return pd.DataFrame([{
            "role": role,
            "fit_score": fit_score,
            "strengths": ", ".join(strengths) if strengths else "",
            "risks": ", ".join(risks) if risks else "",
            "confidence": confidence,
        }])

    def build_risk_uncertainty_table(self, evidence_graph: EvidenceGraph, missing_metrics: List[str]) -> pd.DataFrame:
        findings = []
        if missing_metrics:
            findings.append({
                "finding": "Missing metrics reduce confidence",
                "data_risk": "medium",
                "model_risk": "low",
                "why": f"Missing: {', '.join(missing_metrics[:8])}" + ("..." if len(missing_metrics) > 8 else ""),
                "mitigation": "Provide event/tracking fields; or enable proxies with explicit uncertainty.",
            })
        # contradictions in v1.5; placeholder now
        if evidence_graph.contradictions:
            findings.append({
                "finding": "Conflicting evidence detected",
                "data_risk": "low",
                "model_risk": "medium",
                "why": f"{len(evidence_graph.contradictions)} contradictions present",
                "mitigation": "Review alternative explanations (ACM∞) and increase axes for triangulation.",
            })
        if not findings:
            findings.append({
                "finding": "No major risks flagged (v1.0)",
                "data_risk": "low",
                "model_risk": "low",
                "why": "Sufficient metrics present for minimal triangulation",
                "mitigation": "Add benchmarks (norms) for stronger claims.",
            })
        return pd.DataFrame(findings)