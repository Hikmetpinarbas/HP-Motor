from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Set, Tuple


FileKind = Literal["CSV_EVENTS", "CSV_STATS", "XLSX_FITNESS", "XML_EVENTS", "PDF_REPORT", "MP4_VIDEO", "TXT_DOC", "DOCX_DOC", "HTML_DOC"]

# Analiz/ürün isimleri: burada sistemin “asla yanlış şeyi denememesi” garanti altına alınır.
Product = Literal[
    "EVENT_METRICS_BASIC",          # PPDA/FieldTilt vb (events ->)
    "PASS_NETWORK",                 # XML/Events
    "HEATMAP_EVENT",                # XML/Events with x,y
    "TSI_TEAM_SOMA_INDEX",          # XI-level A1..A7 (fitness/roster)
    "SOMATOTYPE_ROLE_TAGGING",      # physique/somatotype inputs
    "BIO_TACTICAL_COST_OVERLAY",    # fitness + events time-sync
    "VIDEO_ORIENTATION_SCAN",       # MP4 required
    "GHOSTING_TRACK",               # tracking/video required
    "DOC_CONSTRAINTS_ONLY",         # docs -> constraints
    "STRATEGIC_AUTOPSY",            # events + stats (+ optional fitness)
]

@dataclass(frozen=True)
class CapabilityRule:
    product: Product
    required: Set[FileKind]
    optional: Set[FileKind]
    hard_block_reason: str


# Minimum gereksinimler: yoksa BLOCKED.
CAPABILITIES: List[CapabilityRule] = [
    CapabilityRule(
        product="EVENT_METRICS_BASIC",
        required={"CSV_EVENTS"} | {"XML_EVENTS"},
        optional={"CSV_STATS", "XLSX_FITNESS", "PDF_REPORT", "TXT_DOC", "HTML_DOC", "DOCX_DOC"},
        hard_block_reason="Event verisi yok: PPDA/FieldTilt gibi event-türevi metrikler üretilemez.",
    ),
    CapabilityRule(
        product="PASS_NETWORK",
        required={"XML_EVENTS"},
        optional={"CSV_STATS", "PDF_REPORT", "TXT_DOC"},
        hard_block_reason="XML event yok: pas ağı (passing network) çıkarılamaz.",
    ),
    CapabilityRule(
        product="HEATMAP_EVENT",
        required={"XML_EVENTS"},
        optional={"CSV_STATS"},
        hard_block_reason="XML event yok: ısı haritası için koordinatlı event gerekir.",
    ),
    CapabilityRule(
        product="TSI_TEAM_SOMA_INDEX",
        required={"XLSX_FITNESS"},
        optional={"CSV_STATS", "TXT_DOC"},
        hard_block_reason="Fitness/GPS yok: TSI (Team Soma Index) üretilemez.",
    ),
    CapabilityRule(
        product="SOMATOTYPE_ROLE_TAGGING",
        required={"XLSX_FITNESS"} | {"CSV_STATS"},
        optional={"TXT_DOC", "PDF_REPORT"},
        hard_block_reason="Somatotip/physique sinyali yok: rol/etiket somatik eşlemesi yapılamaz.",
    ),
    CapabilityRule(
        product="BIO_TACTICAL_COST_OVERLAY",
        required={"XLSX_FITNESS"} | {"XML_EVENTS"},
        optional={"CSV_STATS"},
        hard_block_reason="Fitness + Event birlikte yok: biyolojik maliyet ile taktik aksiyon örtüşemez.",
    ),
    CapabilityRule(
        product="VIDEO_ORIENTATION_SCAN",
        required={"MP4_VIDEO"},
        optional={"XML_EVENTS", "XLSX_FITNESS"},
        hard_block_reason="Video yok: scanning/body orientation gibi CV-türevi analizler çalışmaz.",
    ),
    CapabilityRule(
        product="GHOSTING_TRACK",
        required={"MP4_VIDEO"},
        optional={"XML_EVENTS"},
        hard_block_reason="Video yok: ghosting/track tabanlı uzamsal sapma analizleri çalışmaz.",
    ),
    CapabilityRule(
        product="DOC_CONSTRAINTS_ONLY",
        required={"TXT_DOC"} | {"PDF_REPORT"} | {"DOCX_DOC"} | {"HTML_DOC"},
        optional=set(),
        hard_block_reason="Doküman yok: constraint/ontology/definition çıkartılamaz.",
    ),
    CapabilityRule(
        product="STRATEGIC_AUTOPSY",
        required={"XML_EVENTS"} | {"CSV_STATS"},
        optional={"XLSX_FITNESS", "PDF_REPORT", "TXT_DOC"},
        hard_block_reason="Event+MatchStats yok: maç otopsisi (neden/kanıt) yapılamaz.",
    ),
]


def available_products(present: Set[FileKind]) -> Tuple[Set[Product], Dict[Product, str]]:
    ok: Set[Product] = set()
    blocked: Dict[Product, str] = {}
    for rule in CAPABILITIES:
        if rule.required.issubset(present):
            ok.add(rule.product)
        else:
            blocked[rule.product] = rule.hard_block_reason
    return ok, blocked