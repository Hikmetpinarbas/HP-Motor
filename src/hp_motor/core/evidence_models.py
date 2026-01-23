from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvidenceNode(BaseModel):
    node_id: str
    metric_id: str
    value: Optional[float] = None
    source: str = "unknown"
    note: Optional[str] = None


class EvidenceEdge(BaseModel):
    from_node: str
    to_node: str
    relation: Literal["supports", "contradicts", "depends_on", "derived_from"] = "supports"
    strength: float = Field(0.5, ge=0.0, le=1.0)
    rationale: Optional[str] = None


class Hypothesis(BaseModel):
    """
    Popper uyumlu: yanlışlanabilir, net iddia.
    v1: minimal şema (ileride test/threshold bağları eklenecek).
    """
    hypothesis_id: str
    statement: str
    falsifiable: bool = True
    tests: List[Dict[str, Any]] = Field(default_factory=list)


class EvidenceGraph(BaseModel):
    overall_confidence: Literal["low", "medium", "high"] = "medium"
    nodes: List[EvidenceNode] = Field(default_factory=list)
    edges: List[EvidenceEdge] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)