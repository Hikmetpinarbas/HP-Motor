from __future__ import annotations

from typing import Any, Dict, Optional


class SomatotypeAuditor:
    """
    SRU (Somatotype–Role–Usage) çatışması:
      - somatotype: {"ecto":0..1,"meso":0..1,"endo":0..1} veya string
      - role: Mezzala, Pivot, CB, FB, Winger, 9 vs.
      - usage: sprint-heavy, duel-heavy, aerial-heavy vs. (opsiyonel)

    v1: rule-based alignment. Sonra learned calibration gelebilir.
    """

    def calculate_alignment(self, somatotype: Dict[str, float], role: str) -> float:
        r = (role or "").strip().lower()
        ecto = float(somatotype.get("ecto", 0.33))
        meso = float(somatotype.get("meso", 0.33))
        endo = float(somatotype.get("endo", 0.33))

        # Simple role priors (normalize değil, sadece yön)
        if r in ("cb", "stoper", "centerback"):
            target = {"meso": 0.55, "endo": 0.25, "ecto": 0.20}
        elif r in ("pivot", "6", "dm", "defensive_mid"):
            target = {"meso": 0.45, "endo": 0.20, "ecto": 0.35}
        elif r in ("mezzala", "8", "cm", "box_to_box"):
            target = {"meso": 0.40, "endo": 0.15, "ecto": 0.45}
        elif r in ("winger", "10", "trequartista", "am"):
            target = {"meso": 0.30, "endo": 0.10, "ecto": 0.60}
        elif r in ("9", "striker", "cf"):
            target = {"meso": 0.50, "endo": 0.25, "ecto": 0.25}
        else:
            target = {"meso": 0.40, "endo": 0.20, "ecto": 0.40}

        # Alignment = 1 - L1 distance / 2 (range 0..1)
        l1 = abs(meso - target["meso"]) + abs(endo - target["endo"]) + abs(ecto - target["ecto"])
        alignment = max(0.0, 1.0 - (l1 / 2.0))
        return float(alignment)

    def _parse_somatotype(self, raw: Any) -> Dict[str, float]:
        if isinstance(raw, dict):
            return raw
        # string fallback
        s = str(raw or "").lower()
        # very rough
        if "ecto" in s:
            return {"ecto": 0.55, "meso": 0.30, "endo": 0.15}
        if "meso" in s:
            return {"ecto": 0.25, "meso": 0.55, "endo": 0.20}
        if "endo" in s:
            return {"ecto": 0.20, "meso": 0.35, "endo": 0.45}
        return {"ecto": 0.33, "meso": 0.33, "endo": 0.33}

    def check_sru_conflict(self, event: Dict[str, Any]) -> Dict[str, Any]:
        # event içinden mümkün olduğunca çıkar
        role = str(event.get("role", event.get("player_role", "unknown")))
        som_raw = event.get("somatotype", event.get("player_somatotype"))
        som = self._parse_somatotype(som_raw)

        alignment = self.calculate_alignment(som, role)

        status = "STABLE"
        alarm = None
        if alignment < 0.70:
            status = "ALARM"
            alarm = "Somatotip-Rol Uyuşmazlığı"

        return {
            "status": status,
            "alarm": alarm,
            "role": role,
            "somatotype": som,
            "alignment": float(round(alignment, 3)),
        }