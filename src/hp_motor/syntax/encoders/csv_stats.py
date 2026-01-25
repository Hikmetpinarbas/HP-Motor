from __future__ import annotations

import io
from typing import Any, Dict, List, Sequence

import pandas as pd

from ..codec import BaseEncoder, EncodeResult
from ..signal_packet import SignalPacket, Payload, Provenance, TemporalAnchor


class CSVStatsEncoder(BaseEncoder):
    """
    Generic CSV aggregated stats encoder.
    Produces packets like:
      entity=player/team, metric=column_name, value=numeric, unit=best-effort
    """

    @property
    def file_kinds(self) -> Sequence[str]:
        return ["CSV_STATS"]

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith(".csv") and ("events" not in lower) and ("maçın tamamı" not in lower)

    def encode_bytes(self, filename: str, data: bytes) -> EncodeResult:
        df = pd.read_csv(io.BytesIO(data))
        packets: List[SignalPacket] = []

        # Decide entity column
        entity_col = None
        for c in ["player", "player_name", "Oyuncu", "team", "team_name", "Takım"]:
            if c in df.columns:
                entity_col = c
                break

        # numeric columns -> metrics
        num_cols = [c for c in df.columns if c != entity_col]

        for idx, row in df.iterrows():
            entity = str(row[entity_col]) if entity_col else "unknown"
            for c in num_cols:
                val = row[c]
                # Only emit numeric-like
                try:
                    fval = float(val)
                except Exception:
                    continue
                packets.append(
                    SignalPacket(
                        signal_type="event",
                        provenance=Provenance(filename=filename, line_number=int(idx) + 1, timestamp_raw=None),
                        payload=Payload(entity=entity, metric=str(c), value=fval, unit=None),
                        temporal_anchor=TemporalAnchor(start_s=None, end_s=None, frame_id=None),
                        meta={"confidence": 0.55, "logic_gate": "Unverified_Hypothesis", "status": "OK", "source_hint": "csv_stats"},
                    )
                )

        return EncodeResult(
            packets=packets,
            meta={"file_kind": "CSV_STATS", "rows": int(len(df)), "columns": list(df.columns), "status": "OK"},
        )