from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


ConfidenceLevel = Literal["low", "medium", "high"]


@dataclass
class Hypothesis:
    """
    Popper-Gate / Evidence Graph tarafında kullanılacak temel hipotez modeli.
    """
    id: str
    claim: str
    confidence: ConfidenceLevel = "medium"
    supporting: List[str] = field(default_factory=list)
    contradicting: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class EvidenceItem:
    """
    Kanıt kayıtları (metrik, kural, gözlem).
    """
    id: str
    kind: Literal["metric", "rule", "observation", "data_quality"] = "metric"
    title: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceGraph:
    """
    Sistemin “neden” katmanı: supporting/contradicting kanıtları bir arada taşır.
    """
    overall_confidence: ConfidenceLevel = "medium"
    items: List[EvidenceItem] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)


@dataclass
class RawArtifact:
    """
    Orchestrator’ın beslendiği ham paket.
    df = event/tablo temsili; meta = dosya ve bağlam.
    """
    df: Any
    meta: Dict[str, Any] = field(default_factory=dict)