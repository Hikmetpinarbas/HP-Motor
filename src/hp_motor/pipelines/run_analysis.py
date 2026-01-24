from __future__ import annotations

from typing import Dict, Any, List
import pandas as pd

from hp_motor.core.scanning import compute_decision_speed
from hp_motor.core.evidence_models import EvidenceGraph
from hp_motor.core.registry_loader import load_master_registry
from hp_motor.core.report_builder import ReportBuilder
from hp_motor.validation.abstain_gate import AbstainGate
from hp_motor.modules.individual_v22 import IndividualAnalysisV22


class SovereignOrchestrator:
    def __init__(self):
        self.registry = load_master_registry()
        self.report_builder = ReportBuilder()
        self.abstain_gate = AbstainGate()
        self.individual_v22 = IndividualAnalysisV22(engine_version="HP ENGINE v22.x")

    def execute(self, df: pd.DataFrame) -> Dict[str, Any]:
        # --- Metrics (still placeholder-aware)
        registry_metrics = self.registry.get("metrics", {})
        metrics = {
            "ppda": registry_metrics.get("ppda", {}).get("default"),
            "xg": registry_metrics.get("xg", {}).get("default"),
        }
        used_metric_ids: List[str] = list(metrics.keys())

        # --- Cognitive proxy
        decision_speed = compute_decision_speed(df)

        # --- Evidence graph
        eg = EvidenceGraph()
        eg.add_claim(
            claim_id="decision_speed",
            value=decision_speed,
            note="Computed decision speed proxy",
        )
        evidence = eg.to_dict()

        # --- ABSTAIN Gate
        abstain = self.abstain_gate.evaluate(
            registry_metrics=registry_metrics,
            used_metric_ids=used_metric_ids,
        )
        status = "ABSTAINED" if abstain.abstained else "OK"

        # --- Report builder
        report = self.report_builder.build(
            df=df,
            metrics=metrics,
            evidence=evidence,
        )

        # --- Individual v22 outputs (NEW)
        lists: Dict[str, Any] = report.get("lists", {}) if isinstance(report.get("lists"), dict) else {}
        individual_outputs: List[Dict[str, Any]] = []

        if "player_id" in df.columns:
            # Choose top-3 players by event count (deterministic default)
            top_players = (
                df.groupby("player_id").size().sort_values(ascending=False).head(3).index.tolist()
            )
            for pid in top_players:
                individual_outputs.append(
                    self.individual_v22.generate_for_player(df=df, player_id=pid, context={})
                )
        else:
            # No player_id -> do not hallucinate; provide a single degraded profile
            individual_outputs.append(
                self.individual_v22.generate_for_player(df=df.assign(player_id="UNKNOWN"), player_id="UNKNOWN", context={})
            )

        lists["individual_v22_profiles"] = individual_outputs

        return {
            "status": status,
            "abstain": {
                "abstained": abstain.abstained,
                "reasons": abstain.reasons,
                "blocking_metrics": abstain.blocking_metrics,
                "note": abstain.note,
            },
            "metrics": metrics,
            "evidence": evidence,
            "tables": report.get("tables", {}),
            "figure_objects": report.get("figure_objects", {}),
            "lists": lists,
        }