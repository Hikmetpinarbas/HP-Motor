from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Tuple, Union, List
import uuid


SignalType = Literal["event", "fitness", "track", "doc", "constraint"]
LogicGate = Literal["Popper_Verified", "Unverified_Hypothesis"]
Status = Literal["OK", "DEGRADED", "BLOCKED"]


@dataclass(frozen=True)
class SpatialAnchor:
    x: float
    y: float
    z: Optional[float] = None
    space_id: Optional[str] = None  # e.g., "pitch_zone_14"


@dataclass(frozen=True)
class TemporalAnchor:
    start_s: Optional[float] = None
    end_s: Optional[float] = None
    frame_id: Optional[int] = None


@dataclass(frozen=True)
class Provenance:
    filename: str
    line_number: Optional[int] = None
    timestamp_raw: Optional[str] = None


@dataclass(frozen=True)
class Payload:
    entity: str  # player_id / team_id / match_id
    metric: str  # e.g., "HSR", "Pass_Acc", "PPDA", "Scanning_Rate"
    value: Union[float, int, str]
    unit: Optional[str] = None  # "m/s", "count", "%", "m", "s", ...


@dataclass
class SignalPacket:
    """
    HP Motor Universal Syntax: every modality -> SignalPacket

    Rule:
      - spatial_anchor and temporal_anchor can be None if not provided by source.
      - status governs whether downstream analysis can consume the packet.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_type: SignalType = "event"
    provenance: Provenance = field(default_factory=lambda: Provenance(filename="unknown"))
    payload: Payload = field(default_factory=lambda: Payload(entity="unknown", metric="unknown", value=float("nan"), unit=None))
    spatial_anchor: Optional[SpatialAnchor] = None
    temporal_anchor: Optional[TemporalAnchor] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def set_meta_defaults(self) -> None:
        self.meta.setdefault("confidence", 0.5)
        self.meta.setdefault("logic_gate", "Unverified_Hypothesis")
        self.meta.setdefault("status", "OK")
        self.meta.setdefault("notes", [])

    @property
    def status(self) -> Status:
        self.set_meta_defaults()
        return self.meta.get("status", "OK")

    @property
    def confidence(self) -> float:
        self.set_meta_defaults()
        return float(self.meta.get("confidence", 0.5))

    def mark(self, status: Status, logic_gate: Optional[LogicGate] = None, note: Optional[str] = None) -> "SignalPacket":
        self.set_meta_defaults()
        self.meta["status"] = status
        if logic_gate is not None:
            self.meta["logic_gate"] = logic_gate
        if note:
            self.meta.setdefault("notes", []).append(note)
        return self