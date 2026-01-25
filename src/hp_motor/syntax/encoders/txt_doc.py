from __future__ import annotations

from typing import Any, Dict, List, Sequence

from ..codec import BaseEncoder, EncodeResult
from ..signal_packet import SignalPacket, Payload, Provenance


class TextDocEncoder(BaseEncoder):
    """
    TXT/MD/HTML/DOCX (best effort) -> doc/constraint signals.

    - For .txt/.md/.html: decode bytes and emit text.
    - For .docx: safe fallback (presence only) unless python-docx is available.
    """

    @property
    def file_kinds(self) -> Sequence[str]:
        return ["TXT_DOC", "HTML_DOC", "DOCX_DOC"]

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith(".txt") or lower.endswith(".md") or lower.endswith(".html") or lower.endswith(".docx")

    def encode_bytes(self, filename: str, data: bytes) -> EncodeResult:
        lower = filename.lower()
        packets: List[SignalPacket] = []

        if lower.endswith(".txt") or lower.endswith(".md") or lower.endswith(".html"):
            try:
                text = data.decode("utf-8", errors="replace")
            except Exception:
                text = ""

            packets.append(
                SignalPacket(
                    signal_type="doc",
                    provenance=Provenance(filename=filename),
                    payload=Payload(entity="global", metric="doc_text", value=text[:8000], unit=None),
                    spatial_anchor=None,
                    temporal_anchor=None,
                    meta={"confidence": 0.65, "logic_gate": "Unverified_Hypothesis", "status": "OK", "source_hint": "text_doc"},
                )
            )

            fk = "HTML_DOC" if lower.endswith(".html") else "TXT_DOC"
            return EncodeResult(packets=packets, meta={"file_kind": fk, "status": "OK", "chars": len(text)})

        if lower.endswith(".docx"):
            # Try extract
            extracted = False
            text = ""
            try:
                from docx import Document  # type: ignore
                import io as _io
                doc = Document(_io.BytesIO(data))
                text = "\n".join([p.text for p in doc.paragraphs]).strip()
                extracted = True
            except Exception:
                extracted = False

            if extracted and text:
                packets.append(
                    SignalPacket(
                        signal_type="doc",
                        provenance=Provenance(filename=filename),
                        payload=Payload(entity="global", metric="doc_text", value=text[:8000], unit=None),
                        meta={"confidence": 0.6, "logic_gate": "Unverified_Hypothesis", "status": "OK", "source_hint": "docx_text"},
                    )
                )
            else:
                packets.append(
                    SignalPacket(
                        signal_type="doc",
                        provenance=Provenance(filename=filename),
                        payload=Payload(entity="global", metric="docx_present", value="true", unit=None),
                        meta={"confidence": 0.5, "logic_gate": "Unverified_Hypothesis", "status": "DEGRADED", "source_hint": "docx_present_only"},
                    )
                )

            return EncodeResult(packets=packets, meta={"file_kind": "DOCX_DOC", "status": "OK", "extracted_text": bool(extracted and bool(text))})

        # unreachable
        return EncodeResult(packets=[], meta={"file_kind": "TXT_DOC", "status": "IGNORED"})