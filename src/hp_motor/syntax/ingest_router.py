from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .codec import BaseEncoder, EncodeResult
from .capability_matrix import FileKind
from .signal_packet import SignalPacket


@dataclass
class IngestBundle:
    packets: List[SignalPacket]
    present_kinds: Set[FileKind]
    per_file_meta: Dict[str, Dict[str, Any]]


class IngestRouter:
    def __init__(self, encoders: List[BaseEncoder]) -> None:
        self.encoders = encoders

    def ingest_files(self, files: List[Tuple[str, bytes]]) -> IngestBundle:
        all_packets: List[SignalPacket] = []
        present: Set[FileKind] = set()
        meta_map: Dict[str, Dict[str, Any]] = {}

        for filename, data in files:
            handled = False
            for enc in self.encoders:
                if enc.can_handle(filename):
                    handled = True
                    res: EncodeResult = enc.encode_bytes(filename, data)
                    all_packets.extend(res.packets)
                    meta_map[filename] = res.meta
                    # encoder meta should include "file_kind"
                    fk = res.meta.get("file_kind")
                    if fk:
                        present.add(fk)
                    break

            if not handled:
                meta_map[filename] = {"status": "IGNORED", "reason": "No encoder matched."}

        return IngestBundle(packets=all_packets, present_kinds=present, per_file_meta=meta_map)