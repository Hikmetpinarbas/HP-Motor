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
    Runtime gate for:
      - Input-Gated Compute
      - Missing input -> module disabled (BLOCKED) OR degraded.

    It is conservative: if catalog entry is missing, it will not allow the run to
    pretend it is safe. It will degrade with explicit reason, never silently pass.
    """

    def __init__(self, capabilities_yaml_path: Optional[str] = None):
        self.capabilities_yaml_path = capabilities_yaml_path or "src/hp_motor/registries/capabilities.yaml"
        self._capabilities = self._load_capabilities_safely(self.capabilities_yaml_path)

    @staticmethod
    def _load_capabilities_safely(path: str) -> Dict[str, object]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            # Fail-closed in a controlled way: we can still run, but will degrade decisions.
            return {"_error": f"capabilities.yaml missing at {path}"}
        except Exception as e:
            return {"_error": f"capabilities.yaml load error: {e}"}

    def decide_for_analysis(self, analysis_type: str, manifest: InputManifest) -> GateDecision:
        """
        The capabilities.yaml is expected to define:
          analyses:
            <analysis_type>:
              hard_requires: [event, video, fitness, tracking, doc, spatial]
              soft_requires: [ ... ]  # optional -> DEGRADED if missing
        """
        cap_error = self._capabilities.get("_error")
        analyses = (self._capabilities or {}).get("analyses", {})

        if cap_error:
            return GateDecision(
                status="DEGRADED",
                reasons=[f"CAPABILITY_MATRIX_UNAVAILABLE: {cap_error}"],
                missing_inputs=[],
            )

        entry = analyses.get(analysis_type)
        if not entry:
            return GateDecision(
                status="DEGRADED",
                reasons=[f"CAPABILITY_MATRIX_MISSING_ENTRY: analysis_type={analysis_type}"],
                missing_inputs=[],
            )

        hard = entry.get("hard_requires", []) or []
        soft = entry.get("soft_requires", []) or []

        missing_hard = [k for k in hard if not self._has_input(k, manifest)]
        missing_soft = [k for k in soft if not self._has_input(k, manifest)]

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
    def _has_input(key: str, manifest: InputManifest) -> bool:
        key = key.strip().lower()
        if key == "event":
            return manifest.has_event
        if key == "spatial":
            return manifest.has_spatial
        if key == "fitness":
            return manifest.has_fitness
        if key == "video":
            return manifest.has_video
        if key == "tracking":
            return manifest.has_tracking
        if key == "doc":
            return manifest.has_doc
        return False