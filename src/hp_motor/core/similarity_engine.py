from __future__ import annotations

from typing import List

import numpy as np


def similarity_score(player_a_vector: List[float], player_b_vector: List[float], weights: List[float]) -> float:
    """
    Ağırlıklı Öklid mesafesi -> 0..1 benzerlik.
    """
    a = np.asarray(player_a_vector, dtype=float)
    b = np.asarray(player_b_vector, dtype=float)
    w = np.asarray(weights, dtype=float)

    if a.shape != b.shape or a.shape != w.shape:
        raise ValueError("Vectors and weights must have same shape.")

    dist = float(np.sqrt(np.sum(w * (a - b) ** 2)))
    return float(1.0 / (1.0 + dist))