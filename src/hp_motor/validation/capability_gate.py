from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml

from hp_motor.pipelines.input_manifest import InputManifest


@dataclass
class GateDecision:
    status: str  # OK | DEGRADED | BLOCKED
    reasons: List[str]
    missing_inputs: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "reasons": self.reasons,
            "missing_inputs": self.missing_inputs,
        }


class CapabilityGate:
    """
    Input-Gated Compute.
    Reads SSOT from registries/capabilities.yaml -> analyses section.
    Fail-closed policy:
      - Missing catalog entry => DEGRADED (never silent pass)
      - Missing hard inputs => BLOCKED
    """

    def __init__(self, capabilities_yaml_path: Optional[str] = None):
        self.capabilities_yaml_path = capabilities_yaml_path or "src/hp_motor/registries/capabilities.yaml"
        self._cap = self._load(self.capabilities_yaml_path)

    @staticmethod
    def _load(path: str) -> Dict[str, object]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {"_error": f"capabilities.yaml missing at {path}"}
        except Exception as e:
            return {"_error": f"capabilities.yaml load error: {e}"}

    def decide(self, analysis_type: str, manifest: InputManifest) -> GateDecision:
        err = self._cap.get("_error")
        if err:
            return GateDecision(
                status="DEGRADED",
                reasons=[f"CAPABILITY_MATRIX_UNAVAILABLE: {err}"],
                missing_inputs=[],
            )

        analyses = (self._cap or {}).get("analyses", {}) or {}
        entry = analyses.get(analysis_type)

        if not entry:
            return GateDecision(
                status="DEGRADED",
                reasons=[f"CAPABILITY_MATRIX_MISSING_ENTRY: analysis_type={analysis_type}"],
                missing_inputs=[],
            )

        hard = entry.get("hard_requires", []) or []
        soft = entry.get("soft_requires", []) or []

        missing_hard = [k for k in hard if not self._has(k, manifest)]
        missing_soft = [k for k in soft if not self._has(k, manifest)]

        if missing_hard:
            return GateDecision(
                status="BLOCKED",
                reasons=[f"MISSING_REQUIRED_INPUTS: {', '.join(missing_hard)}"],
                missing_inputs=missing_hard,
            )

        if missing_soft:
            return GateDecision(
                status="DEGRADED",
                reasons=[f"MISSING_OPTIONAL_INPUTS: {', '.join(missing_soft)}"],
                missing_inputs=missing_soft,
            )

        return GateDecision(status="OK", reasons=[], missing_inputs=[])

    @staticmethod
    def _has(key: str, m: InputManifest) -> bool:
        k = key.strip().lower()
        if k == "event":
            return m.has_event
        if k == "spatial":
            return m.has_spatial
        if k == "fitness":
            return m.has_fitness
        if k == "video":
            return m.has_video
        if k == "tracking":
            return m.has_tracking
        if k == "doc":
            return m.has_doc
        return False