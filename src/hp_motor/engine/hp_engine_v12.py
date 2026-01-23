from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from hp_motor.engine.protocols import ProtocolManager
from hp_motor.engine.somatotype import SomatotypeAuditor
from hp_motor.engine.regime import RegimeDetector


@dataclass
class EngineOutput:
    status: str
    h_score: float
    regime: str
    bio_risk: Dict[str, Any]
    protocols: Dict[str, Any]
    uncertainty: float
    notes: Optional[str] = None


class HPEngineV12:
    """
    HP Engine v12:
      - Veto/validation
      - Regime detection (Control vs Chaos)
      - Biomechanics audit (Somatotype SRU gate)
      - Protocol stack (P1..P10)
      - Uncertainty buffer (epistemic)

    Bu sınıf event-by-event veya event-batch çalışabilir.
    """

    def __init__(self):
        self.protocols = ProtocolManager()
        self.bio_auditor = SomatotypeAuditor()
        self.tactical_detector = RegimeDetector()
        self.uncertainty_buffer = 0.0  # 0..1

    def validate_event(self, event: Dict[str, Any]) -> bool:
        """
        Veto koşulları:
          - entity_id / team_id gibi kimlikler var mı?
          - timestamp var mı?
          - event_type var mı?
        """
        required = ["event_type"]
        for k in required:
            if k not in event or event[k] in (None, ""):
                return False
        return True

    def process_match_event(self, event: Dict[str, Any]) -> EngineOutput:
        # 1) Data validation (veto)
        if not self.validate_event(event):
            self.uncertainty_buffer = min(1.0, self.uncertainty_buffer + 0.15)
            return EngineOutput(
                status="ERROR",
                h_score=0.0,
                regime="UNKNOWN",
                bio_risk={"status": "UNKNOWN"},
                protocols={"status": "SKIPPED"},
                uncertainty=self.uncertainty_buffer,
                notes="HATA: Veri Güven Aralığı İhlali (event veto).",
            )

        # 2) Regime detection (light Bayes update)
        h_score, regime, h_debug = self.tactical_detector.calculate_h_score(event)

        # 3) Biomechanics audit
        bio_risk = self.bio_auditor.check_sru_conflict(event)

        # 4) Protocol stack
        analysis = self.protocols.run_all(event, h_score=h_score, bio=bio_risk)

        # 5) Uncertainty update (epistemic)
        # missing fields / low evidence -> uncertainty ↑
        miss = 0
        for k in ["timestamp", "player_id", "x", "y"]:
            if k not in event:
                miss += 1
        self.uncertainty_buffer = float(min(1.0, max(0.0, self.uncertainty_buffer + 0.03 * miss - 0.02)))

        return EngineOutput(
            status="OK",
            h_score=float(h_score),
            regime=str(regime),
            bio_risk=bio_risk,
            protocols=analysis,
            uncertainty=self.uncertainty_buffer,
            notes=h_debug,
        )

    def format_output(self, out: EngineOutput) -> Dict[str, Any]:
        return {
            "status": out.status,
            "regime": out.regime,
            "h_score": out.h_score,
            "uncertainty": out.uncertainty,
            "bio_risk": out.bio_risk,
            "protocols": out.protocols,
            "notes": out.notes,
        }