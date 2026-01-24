from __future__ import annotations

from typing import Any, Dict, Optional, List

import pandas as pd

from hp_motor.core.evidence_models import EvidenceGraph, Hypothesis, RawArtifact
from hp_motor.core.registry_loader import load_master_registry
from hp_motor.core.scanning import compute_decision_speed
from hp_motor.core.report_builder import ReportBuilder
from hp_motor.validation.sot_validator import SOTValidator
from hp_motor.validation.biomechanic_gate import BiomechanicGate


class SovereignOrchestrator:
    """
    Registry-driven orchestration layer.

    Design goals (HP contract):
      - If data is insufficient: ABSTAIN (no default "talking").
      - Always return artifacts shell: tables/lists/figure_objects, even when abstaining.
      - Produce "why" via diagnostics + evidence graph.
    """

    def __init__(self) -> None:
        self.registry = load_master_registry() or {}
        self.report_builder = ReportBuilder(registry=self.registry)

        # v1: keep required set minimal; coverage table will be the primary truth.
        self.sot_validator = SOTValidator(required_columns=[], allow_empty=False)
        self.biomech_gate = BiomechanicGate()

    # ------------------------------------------------------------------
    # Public API (Streamlit / legacy callers)
    # ------------------------------------------------------------------
    def run(self, raw_df: pd.DataFrame, *, phase: str = "open_play", role: str = "Mezzala") -> Dict[str, Any]:
        """
        Streamlit-friendly wrapper.
        """
        return self.execute(
            analysis_object_id="player_role_fit",
            raw_df=raw_df,
            entity_id="entity",
            role=role,
            phase=phase,
        )

    def execute_full_analysis(self, artifact: RawArtifact, phase: str) -> Dict[str, Any]:
        """
        Legacy uyumu: app.py eski çağrıları için.
        """
        df = artifact.df if isinstance(artifact, RawArtifact) else artifact
        return self.run(df, phase=phase)

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------
    def execute(
        self,
        analysis_object_id: str,
        raw_df: pd.DataFrame,
        entity_id: str,
        role: str,
        phase: str,
        archetype_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 0) Hard stop: no data
        if raw_df is None or len(raw_df) == 0:
            return self.report_builder.build_abstained_output(
                analysis_object_id=analysis_object_id,
                entity_id=entity_id,
                role=role,
                phase=phase,
                reason="Empty dataframe",
                diagnostics={"missing_metrics": ["ppda", "xg"]},
            )

        df = raw_df.copy()

        # 1) SOT validation (data quality report; NEVER drop rows)
        dq = self.sot_validator.validate(df)
        if not dq.get("ok", False):
            return self.report_builder.build_abstained_output(
                analysis_object_id=analysis_object_id,
                entity_id=entity_id,
                role=role,
                phase=phase,
                reason="Data quality gate failed",
                diagnostics={"data_quality": dq},
            )

        # 2) Biomechanic gate (soft gate; reduces confidence or produces issues)
        biomech = self.biomech_gate.evaluate(df)

        # 3) Compute metrics (NO defaults when missing)
        metrics: List[Dict[str, Any]] = []
        missing_metrics: List[str] = []

        # --- PPDA: accept precomputed column if provided
        ppda_val = self._extract_numeric_mean(df, ["ppda", "PPDA"])
        if ppda_val is None:
            missing_metrics.append("ppda")
        else:
            metrics.append({"metric_id": "ppda", "value": ppda_val, "unit": "ratio", "source": "raw_df"})

        # --- xG: accept precomputed columns if provided
        xg_val = self._extract_numeric_sum(df, ["xg", "xG", "shot_xg", "shot_xG"])
        if xg_val is None:
            missing_metrics.append("xg")
        else:
            metrics.append({"metric_id": "xg", "value": xg_val, "unit": "goals", "source": "raw_df"})

        # --- Cognitive speed proxy (scanning inference)
        cog = compute_decision_speed(df, entity_id=entity_id)
        if cog.get("avg_decision_speed_sec") is not None:
            metrics.append(
                {
                    "metric_id": "cognitive_speed_sec",
                    "value": float(cog["avg_decision_speed_sec"]),
                    "unit": "sec",
                    "source": "derived",
                }
            )
            metrics.append({"metric_id": "cognitive_speed_status", "value": cog.get("status"), "source": "derived"})
        else:
            missing_metrics.append("cognitive_speed_sec")

        # 4) Evidence graph (why)
        overall = self._combine_confidence(
            cognitive_status=str(cog.get("status") or "UNKNOWN"),
            biomech_band=str(biomech.get("confidence_band") or "medium"),
            missing_metrics=missing_metrics,
        )

        eg = EvidenceGraph(
            overall_confidence=overall,
            hypotheses=[
                Hypothesis(
                    id="H_COG",
                    claim="Player shows decision-speed proxy consistent with scanning readiness.",
                    confidence=overall,
                    supporting=["cognitive_speed_sec"] if cog.get("avg_decision_speed_sec") is not None else [],
                    contradicting=[],
                    notes=cog.get("note"),
                ),
                Hypothesis(
                    id="H_BIO",
                    claim="Biomechanical gate: posture/orientation signals are consistent enough to reason about.",
                    confidence=str(biomech.get("confidence_band") or "medium"),
                    supporting=biomech.get("supporting") or [],
                    contradicting=biomech.get("contradicting") or [],
                    notes=biomech.get("note"),
                ),
            ],
        )

        # 5) Archetype check (registry-based)
        archetype_report = None
        if archetype_id:
            archetype_report = self._evaluate_archetype(archetype_id, metrics)

        # 6) Popper rule: if core metrics missing -> degraded; if too many -> abstain
        # v1 policy: if ALL of ppda/xg missing AND no cognitive -> abstain
        core_missing = set(missing_metrics) & {"ppda", "xg", "cognitive_speed_sec"}
        if core_missing == {"ppda", "xg", "cognitive_speed_sec"}:
            return self.report_builder.build_abstained_output(
                analysis_object_id=analysis_object_id,
                entity_id=entity_id,
                role=role,
                phase=phase,
                reason="Insufficient signals to produce a falsifiable output",
                diagnostics={"data_quality": dq, "biomech": biomech, "missing_metrics": missing_metrics},
            )

        status = "OK" if len(missing_metrics) == 0 else "DEGRADED"

        # 7) Build artifacts (tables/lists/figures) deterministically
        artifacts = self.report_builder.build(
            df=df,
            role=role,
            metrics=metrics,
            missing_metrics=missing_metrics,
            evidence_graph={
                "overall_confidence": eg.overall_confidence,
                "hypotheses": [
                    {
                        "id": h.id,
                        "claim": h.claim,
                        "confidence": h.confidence,
                        "supporting": h.supporting,
                        "contradicting": h.contradicting,
                        "notes": h.notes,
                    }
                    for h in eg.hypotheses
                ],
            },
            diagnostics={"data_quality": dq, "biomech": biomech, "cognitive": cog},
        )

        return {
            "status": status,
            "analysis_object_id": analysis_object_id,
            "entity_id": entity_id,
            "role": role,
            "phase": phase,
            "metrics": metrics,
            "missing_metrics": missing_metrics,
            "tables": artifacts["tables"],
            "lists": artifacts["lists"],
            "figure_objects": artifacts["figure_objects"],
            "evidence_graph": artifacts["evidence_graph"],
            "diagnostics": artifacts["diagnostics"],
            "registry_version": self.registry.get("version", "unknown"),
            "registry_name": self.registry.get("name", "hp_master_registry"),
            "archetype": archetype_report,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_numeric_mean(df: pd.DataFrame, candidates: List[str]) -> Optional[float]:
        for c in candidates:
            if c in df.columns:
                s = pd.to_numeric(df[c], errors="coerce")
                if s.notna().sum() > 0:
                    return float(s.mean())
        return None

    @staticmethod
    def _extract_numeric_sum(df: pd.DataFrame, candidates: List[str]) -> Optional[float]:
        for c in candidates:
            if c in df.columns:
                s = pd.to_numeric(df[c], errors="coerce")
                if s.notna().sum() > 0:
                    return float(s.sum())
        return None

    @staticmethod
    def _combine_confidence(cognitive_status: str, biomech_band: str, missing_metrics: List[str]) -> str:
        # Deterministic, conservative policy
        band = "medium"
        cs = (cognitive_status or "").upper().strip()
        bb = (biomech_band or "").lower().strip()

        if cs == "ELITE":
            band = "high"
        elif cs == "SLOW":
            band = "medium"
        else:
            band = "medium"

        if bb == "low":
            band = "low" if band != "high" else "medium"

        if len(missing_metrics) >= 3:
            band = "low"
        elif len(missing_metrics) >= 1 and band == "high":
            band = "medium"

        return band

    def _evaluate_archetype(self, archetype_id: str, metrics: list) -> Dict[str, Any]:
        archetypes = (self.registry or {}).get("archetypes", []) or []
        spec = next((a for a in archetypes if a.get("id") == archetype_id), None)
        if not spec:
            return {"id": archetype_id, "status": "UNKNOWN_ARCHETYPE"}

        # metrics list -> dict
        m = {}
        for row in metrics:
            mid = row.get("metric_id")
            if mid is not None:
                m[mid] = row.get("value")

        req = spec.get("required_metrics", {}) or {}
        checks = []
        passed = True

        for k, rule in req.items():
            val = m.get(k)
            rmin = rule.get("min")
            rmax = rule.get("max")

            ok = True
            if val is None:
                ok = False
            if rmin is not None and val is not None and float(val) < float(rmin):
                ok = False
            if rmax is not None and val is not None and float(val) > float(rmax):
                ok = False

            checks.append({"metric": k, "value": val, "rule": rule, "ok": ok})
            if not ok:
                passed = False

        return {
            "id": spec.get("id"),
            "name": spec.get("name"),
            "status": "PASS" if passed else "FAIL",
            "checks": checks,
        }