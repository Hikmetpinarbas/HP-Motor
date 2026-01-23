from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class SimilarityResult:
    candidate_id: str
    similarity: float
    distance: float
    used_features: int
    missing_features: List[str]


class SimilarityEngine:
    """
    Driblab-style Similarity Tool (v1):
      - weighted euclidean distance
      - feature scaling (z-score) if norms provided, else robust min/max fallback
      - missing handling: ignore missing dims but penalize if too many missing
    """

    def __init__(self, min_features: int = 3, missing_penalty: float = 0.08):
        self.min_features = min_features
        self.missing_penalty = missing_penalty

    def _normalize_weight(self, weights: Dict[str, float]) -> Dict[str, float]:
        s = sum(abs(float(w)) for w in (weights or {}).values()) or 1.0
        return {k: float(v) / s for k, v in (weights or {}).items()}

    def _scale_value(self, x: float, mean: Optional[float], std: Optional[float], vmin: Optional[float], vmax: Optional[float]) -> float:
        # Prefer z-score if mean/std exists and std>0
        if mean is not None and std is not None and std > 1e-9:
            return (x - mean) / std
        # fallback min-max
        if vmin is not None and vmax is not None and (vmax - vmin) > 1e-9:
            return (x - vmin) / (vmax - vmin)
        return x

    def similarity(
        self,
        target_vector: Dict[str, float],
        candidate_vector: Dict[str, float],
        weights: Dict[str, float],
        norms: Optional[Dict[str, Dict[str, float]]] = None,
        bounds: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> SimilarityResult:
        """
        norms: {metric_id: {mean:..., std:...}}
        bounds: {metric_id: {min:..., max:...}} for fallback scaling
        """
        w = self._normalize_weight(weights)
        norms = norms or {}
        bounds = bounds or {}

        missing = []
        used = 0
        dist2 = 0.0

        for mid, wi in w.items():
            a = target_vector.get(mid, None)
            b = candidate_vector.get(mid, None)
            if a is None or b is None:
                missing.append(mid)
                continue

            used += 1
            a = float(a)
            b = float(b)

            n = norms.get(mid, {})
            bd = bounds.get(mid, {})
            a_s = self._scale_value(a, n.get("mean"), n.get("std"), bd.get("min"), bd.get("max"))
            b_s = self._scale_value(b, n.get("mean"), n.get("std"), bd.get("min"), bd.get("max"))

            dist2 += float(wi) * (a_s - b_s) ** 2

        if used < self.min_features:
            # Not enough overlap: force low similarity
            distance = 9.9
            sim = 0.0
            return SimilarityResult(
                candidate_id=str(candidate_vector.get("entity_id", "candidate")),
                similarity=sim,
                distance=distance,
                used_features=used,
                missing_features=missing,
            )

        distance = math.sqrt(dist2)

        # Missing penalty: reduce similarity if many dims missing
        miss_ratio = len(missing) / max(1, len(w))
        distance = distance * (1.0 + self.missing_penalty * miss_ratio)

        sim = 1.0 / (1.0 + distance)
        cid = str(candidate_vector.get("entity_id", "candidate"))

        return SimilarityResult(
            candidate_id=cid,
            similarity=float(sim),
            distance=float(distance),
            used_features=int(used),
            missing_features=missing,
        )

    def rank_candidates(
        self,
        target_id: str,
        vectors: Dict[str, Dict[str, float]],
        weights: Dict[str, float],
        top_k: int = 10,
        norms: Optional[Dict[str, Dict[str, float]]] = None,
        bounds: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> List[SimilarityResult]:
        target = vectors.get(str(target_id), None)
        if target is None:
            return []

        results = []
        for cid, vec in vectors.items():
            if str(cid) == str(target_id):
                continue
            candidate = dict(vec)
            candidate["entity_id"] = str(cid)
            r = self.similarity(target, candidate, weights=weights, norms=norms, bounds=bounds)
            results.append(r)

        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[: int(top_k)]