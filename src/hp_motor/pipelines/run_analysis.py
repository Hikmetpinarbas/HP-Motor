from __future__ import annotations

from typing import Dict, Any, List

import pandas as pd

from hp_motor.core.scanning import compute_decision_speed
from hp_motor.core.evidence_models import EvidenceGraph
from hp_motor.core.registry_loader import load_master_registry
from hp_motor.core.report_builder import ReportBuilder
from hp_motor.validation.abstain_gate import AbstainGate
from hp_motor.reasoning.falsifier import PopperGate

from hp_motor.pipelines.input_manifest import InputManifest
from hp_motor.validation.capability_gate import CapabilityGate


class SovereignOrchestrator:
    """
    Canonical orchestrator for HP Motor.

    Public API:
      - execute(df, **kwargs): canonical
      - run(df, **kwargs): backward/CI/UI compatible alias

    Safety contract:
      - Input-gated compute (CapabilityGate)
      - Evidence-only claims (PopperGate)
      - Fail-closed on BLOCKED (no metric computation)
    """

    def __init__(self):
        self.registry = load_master_registry()
        self.report_builder = ReportBuilder()
        self.abstain_gate = AbstainGate()
        self.popper_gate = PopperGate()
        self.capability_gate = CapabilityGate()

    # -------------------------
    # CANONICAL ENTRYPOINT
    # -------------------------
    def execute(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        registry_metrics = self.registry.get("metrics", {})

        # Analysis type is the unit of gating.
        # Default is "generic" (conservative).
        analysis_type = kwargs.get("analysis_type") or "generic"

        # Build input manifest WITHOUT guessing.
        manifest = InputManifest.from_kwargs(df_provided=(df is not None), kwargs=kwargs)

        # Decide capability status based on manifest + SSOT capabilities.
        cap = self.capability_gate.decide_for_analysis(analysis_type=analysis_type, manifest=manifest)

        # Metrics (example bundle - remains registry-driven)
        metrics = {
            "ppda": registry_metrics.get("ppda", {}).get("default"),
            "xg": registry_metrics.get("xg", {}).get("default"),
        }
        used_metric_ids: List[str] = list(metrics.keys())

        # -----------------
        # POPPER GATE (evidence-only)
        # -----------------
        popper = self.popper_gate.check_dataframe(
            df,
            required_columns=["event_type"],
            value_bounds={
                # Common columns (if present). These do not become required.
                "minute": (0.0, 130.0),
                "second": (0.0, 60.0),
                "x": (0.0, 120.0),
                "y": (0.0, 80.0),
            },
        )

        # Cognitive proxy
        decision_speed = compute_decision_speed(df)

        # -----------------
        # FAIL-CLOSED RULES
        # -----------------
        # 1) If capability gate says BLOCKED: abstain from all decision-producing computation.
        if cap.status == "BLOCKED":
            for mid in used_metric_ids:
                self.abstain_gate.abstain(
                    metric_id=mid,
                    reason=f"CAPABILITY_BLOCK: {', '.join(cap.reasons)}",
                )

        # 2) If Popper Gate blocks downstream: abstain too.
        if popper.get("block_downstream"):
            for mid in used_metric_ids:
                self.abstain_gate.abstain(
                    metric_id=mid,
                    reason="POPPER_BLOCK: minimum evidence missing or integrity violation",
                )

        # Evidence graph (always allowed: it's bookkeeping, not a claim of ground truth)
        eg = EvidenceGraph()
        eg.add_claim(
            claim_id="decision_speed",
            value=decision_speed,
            note="Computed decision speed proxy",
        )
        eg.add_claim(
            claim_id="input_manifest",
            value={
                "has_event": manifest.has_event,
                "has_spatial": manifest.has_spatial,
                "has_fitness": manifest.has_fitness,
                "has_video": manifest.has_video,
                "has_tracking": manifest.has_tracking,
                "has_doc": manifest.has_doc,
                "notes": manifest.notes,
            },
            note="Runtime input inventory (no guessing)",
        )
        eg.add_claim(
            claim_id="capability_decision",
            value=cap.to_dict(),
            note="Input-gated compute decision",
        )
        evidence = eg.to_dict()

        # ABSTAIN Gate
        abstain = self.abstain_gate.evaluate(
            registry_metrics=registry_metrics,
            used_metric_ids=used_metric_ids,
        )

        # Popper ERROR-severity issues => ABSTAINED report shell
        popper_blocks = any(i.get("severity") == "ERROR" for i in popper.get("issues", []))

        # Report builder (may still build a shell)
        report = self.report_builder.build(
            df=df,
            metrics=metrics,
            evidence=evidence,
        )

        # Status hierarchy:
        # - BLOCKED capability => ABSTAINED
        # - Popper ERROR => ABSTAINED
        # - Abstain => ABSTAINED
        # - Otherwise OK
        status = "OK"
        if cap.status == "BLOCKED" or abstain.abstained or popper_blocks:
            status = "ABSTAINED"
        elif cap.status == "DEGRADED":
            status = "DEGRADED"

        # UI-friendly safety note
        safety_note = None
        if cap.status == "BLOCKED":
            safety_note = "Missing input → module disabled to prevent hallucination."
        elif cap.status == "DEGRADED":
            safety_note = "Partial input → output degraded; no hard claims beyond evidence."

        return {
            "status": status,
            "analysis_type": analysis_type,
            "capability_gate": cap.to_dict(),
            "input_manifest": {
                "has_event": manifest.has_event,
                "has_spatial": manifest.has_spatial,
                "has_fitness": manifest.has_fitness,
                "has_video": manifest.has_video,
                "has_tracking": manifest.has_tracking,
                "has_doc": manifest.has_doc,
                "notes": manifest.notes,
            },
            "safety_note": safety_note,
            "popper_gate": {
                "passed": popper.passed,
                "issue_count": len(popper.issues),
                "issues": [i.to_dict() for i in popper.issues],
                "note": popper.note,
            },
            "abstain": {
                "abstained": abstain.abstained,
                "reasons": abstain.reasons,
                "blocking_metrics": abstain.blocking_metrics,
                "note": abstain.note,
            },
            "metrics": metrics,
            "evidence": evidence,
            **report,
        }

    # -------------------------
    # COMPATIBILITY ALIAS
    # -------------------------
    def run(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Alias for execute().
        Required for:
          - Streamlit UI
          - CI smoke import tests
          - Legacy calls
        """
        return self.execute(df, **kwargs)