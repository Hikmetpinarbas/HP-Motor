from dataclasses import dataclass
from typing import Optional, Dict, Any


# -------- Anchors --------

@dataclass
class SpatialAnchor:
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    zone_id: Optional[str] = None


@dataclass
class TemporalAnchor:
    start_s: Optional[float] = None
    end_s: Optional[float] = None
    frame_id: Optional[int] = None


# -------- Core Payload --------

@dataclass
class Provenance:
    source_file: str
    source_line: Optional[int] = None
    raw_timestamp: Optional[str] = None


@dataclass
class Payload:
    entity: str
    metric: str
    value: Any
    unit: Optional[str] = None


@dataclass
class Meta:
    confidence: float = 1.0
    logic_gate: str = "Unverified_Hypothesis"
    status: str = "OK"  # OK | DEGRADED | BLOCKED


# -------- Signal Packet (SSOT) --------

@dataclass
class SignalPacket:
    id: str
    signal_type: str  # event | fitness | track | doc | constraint
    provenance: Provenance
    payload: Payload

    spatial_anchor: Optional[SpatialAnchor] = None
    temporal_anchor: Optional[TemporalAnchor] = None
    meta: Meta = Meta()

    raw: Optional[Dict[str, Any]] = None  # no silent drop