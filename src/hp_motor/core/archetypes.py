from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class ArchetypeMatch:
    archetype_id: str
    name: str
    fit_pct: float
    passed: bool
    passed_rules: List[str]
    failed_rules: List[str]
    missing_metrics: List[str]
    logic: Optional[str] = None


class ArchetypeEngine:
    """
    Archetype evaluation engine (v1):
      - required_metrics with min/max thresholds
      - returns fit percentage and pass/fail with explanations
    """

    def evaluate(self, archetype: Dict[str, Any], metric_map: Dict[str, float]) -> ArchetypeMatch:
        req = archetype.get("required_metrics", {}) or {}
        passed = []
        failed = []
        missing = []

        total = 0
        ok = 0

        for mid, rule in req.items():
            total += 1
            val = metric_map.get(mid, None)
            if val is None:
                missing.append(mid)
                failed.append(f"{mid}:missing")
                continue

            v = float(val)
            r = rule or {}
            # rule can be {min: x} or {max: y} or both
            cond_ok = True
            parts = []

            if "min" in r:
                m = float(r["min"])
                cond_ok = cond_ok and (v >= m)
                parts.append(f">={m:g}")
            if "max" in r:
                m = float(r["max"])
                cond_ok = cond_ok and (v <= m)
                parts.append(f"<={m:g}")

            label = f"{mid}:{v:.3g}({' & '.join(parts)})"
            if cond_ok:
                ok += 1
                passed.append(label)
            else:
                failed.append(label)

        fit = 0.0 if total == 0 else (ok / total) * 100.0
        passed_bool = (ok == total) and (len(missing) == 0)

        return ArchetypeMatch(
            archetype_id=str(archetype.get("id")),
            name=str(archetype.get("name", archetype.get("id"))),
            fit_pct=float(round(fit, 2)),
            passed=bool(passed_bool),
            passed_rules=passed,
            failed_rules=failed,
            missing_metrics=missing,
            logic=archetype.get("logic"),
        )

    def evaluate_all(self, registry: Dict[str, Any], metric_map: Dict[str, float]) -> List[ArchetypeMatch]:
        out = []
        for a in (registry.get("archetypes", []) or []):
            out.append(self.evaluate(a, metric_map))
        out.sort(key=lambda x: x.fit_pct, reverse=True)
        return out