from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    csv = "csv"
    xlsx = "xlsx"
    xml = "xml"
    json = "json"
    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    video = "video"


class RawArtifact(BaseModel):
    artifact_id: str
    type: ArtifactType
    source: str = Field(default="unknown")
    path: Optional[str] = None

    # What we think is inside (lightweight)
    content_schema: Optional[Dict[str, Any]] = None
    entities_detected: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Provenance
    sha256: Optional[str] = None
    created_utc: Optional[str] = None