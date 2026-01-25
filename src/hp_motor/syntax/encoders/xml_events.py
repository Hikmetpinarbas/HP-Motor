from __future__ import annotations

from typing import Any, Dict, List, Sequence, Optional
import xml.etree.ElementTree as ET

from ..codec import BaseEncoder, EncodeResult
from ..signal_packet import SignalPacket, Payload, Provenance, SpatialAnchor, TemporalAnchor


class XMLEventsEncoder(BaseEncoder):
    """
    Opta-like XML event encoder (minimal, schema-agnostic):
    - Searches for attributes that look like: player, team, type, x, y, time.
    - Emits event packets. Coordinates/time are best-effort.
    """

    @property
    def file_kinds(self) -> Sequence[str]:
        return ["XML_EVENTS"]

    def can_handle(self, filename: str) -> bool:
        return filename.lower().endswith(".xml")

    def encode_bytes(self, filename: str, data: bytes) -> EncodeResult:
        root = ET.fromstring(data)
        packets: List[SignalPacket] = []
        count = 0

        def get_attr(el, keys: List[str]) -> Optional[str]:
            for k in keys:
                if k in el.attrib:
                    return el.attrib.get(k)
            return None

        # iterate all nodes; treat nodes named "Event" or with "event" in tag as events
        for el in root.iter():
            tag = el.tag.lower()
            if "event" not in tag and tag not in ("event", "pass", "shot", "duel"):
                continue

            player = get_attr(el, ["player_id", "player", "playerId", "player_id_ref"]) or "unknown"
            team = get_attr(el, ["team_id", "team", "teamId"]) or "unknown"
            etype = get_attr(el, ["type", "event_type", "eventType", "qualifier"]) or tag

            x_raw = get_attr(el, ["x", "X"])
            y_raw = get_attr(el, ["y", "Y"])
            t_raw = get_attr(el, ["time", "sec", "seconds", "timestamp", "min"])

            sp = None
            if x_raw is not None and y_raw is not None:
                try:
                    sp = SpatialAnchor(x=float(x_raw), y=float(y_raw), z=None, space_id=None)
                except Exception:
                    sp = None

            ts = None
            if t_raw is not None:
                try:
                    ts = float(t_raw)
                    # If min likely -> convert to seconds if <= 130
                    if ts <= 130:
                        # ambiguous: could be seconds; keep as-is. (You can tighten later)
                        pass
                except Exception:
                    ts = None

            entity = str(player) if player != "unknown" else str(team)

            packets.append(
                SignalPacket(
                    signal_type="event",
                    provenance=Provenance(filename=filename, line_number=None, timestamp_raw=t_raw),
                    payload=Payload(entity=entity, metric=str(etype), value=1, unit="count"),
                    spatial_anchor=sp,
                    temporal_anchor=TemporalAnchor(start_s=ts, end_s=ts, frame_id=None),
                    meta={"confidence": 0.7, "logic_gate": "Unverified_Hypothesis", "status": "OK", "source_hint": "xml_events"},
                )
            )
            count += 1

        return EncodeResult(
            packets=packets,
            meta={"file_kind": "XML_EVENTS", "events_emitted": int(count), "status": "OK"},
        )