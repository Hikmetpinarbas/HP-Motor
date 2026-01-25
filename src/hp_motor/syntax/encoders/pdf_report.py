from __future__ import annotations

from typing import Any, Dict, List, Sequence

from ..codec import BaseEncoder, EncodeResult
from ..signal_packet import SignalPacket, Payload, Provenance


class PDFReportEncoder(BaseEncoder):
    """
    PDF -> doc signals.
    Minimal approach:
      - If PyPDF2 exists, extract text.
      - Else: emit a single packet as "doc available" constraint without text.

    This avoids hallucinating PDF content.
    """

    @property
    def file_kinds(self) -> Sequence[str]:
        return ["PDF_REPORT"]

    def can_handle(self, filename: str) -> bool:
        return filename.lower().endswith(".pdf")

    def encode_bytes(self, filename: str, data: bytes) -> EncodeResult:
        text = ""
        extracted = False

        try:
            import PyPDF2  # type: ignore
            reader = PyPDF2.PdfReader(io.BytesIO(data))  # type: ignore
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            text = "\n".join(parts).strip()
            extracted = True
        except Exception:
            extracted = False

        packets: List[SignalPacket] = []
        if extracted and text:
            # emit doc chunks (limit size)
            chunk = text[:4000]
            packets.append(
                SignalPacket(
                    signal_type="doc",
                    provenance=Provenance(filename=filename, line_number=None, timestamp_raw=None),
                    payload=Payload(entity="global", metric="pdf_text", value=chunk, unit=None),
                    spatial_anchor=None,
                    temporal_anchor=None,
                    meta={"confidence": 0.6, "logic_gate": "Unverified_Hypothesis", "status": "OK", "source_hint": "pdf_text"},
                )
            )
        else:
            # safe fallback: we only acknowledge presence
            packets.append(
                SignalPacket(
                    signal_type="doc",
                    provenance=Provenance(filename=filename),
                    payload=Payload(entity="global", metric="pdf_present", value="true", unit=None),
                    spatial_anchor=None,
                    temporal_anchor=None,
                    meta={"confidence": 0.5, "logic_gate": "Unverified_Hypothesis", "status": "DEGRADED", "source_hint": "pdf_present_only"},
                )
            )

        return EncodeResult(
            packets=packets,
            meta={"file_kind": "PDF_REPORT", "extracted_text": bool(extracted and bool(text)), "status": "OK"},
        )