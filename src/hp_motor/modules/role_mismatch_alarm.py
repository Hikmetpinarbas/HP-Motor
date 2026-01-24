from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple


Band = Literal["YESIL", "SARI", "KIRMIZI"]
Answer = Literal["EVET", "HAYIR", "BILINMIYOR"]


# ------------------------------------------------------------
# Model
# ------------------------------------------------------------
@dataclass
class ChecklistItem:
    id: str
    section: str
    text: str
    # points_if_yes / points_if_no define the scoring contract per question
    points_if_yes: int
    points_if_no: int
    # unknown treated conservatively (half-risk by default)
    points_if_unknown: int


@dataclass
class RoleMismatchResult:
    total_score: int
    band: Band
    answers: Dict[str, Answer]
    points: Dict[str, int]
    live_triggers_hit: int
    band_after_triggers: Band
    actions: Dict[str, List[str]]
    judgement_line: str
    markdown: str
    diagnostics: Dict[str, Any]


# ------------------------------------------------------------
# Canonical checklist (v22.x)
# ------------------------------------------------------------
CHECKLIST_V22: List[ChecklistItem] = [
    # A) Role definition fit
    ChecklistItem("q1", "A) ROL TARİFİ UYUMU", "Oyuncunun birincil rolü saha planında net mi?", 0, 2, 1),
    ChecklistItem("q2", "A) ROL TARİFİ UYUMU", "Oyuncu çizgiye hapsediliyor mu? (line-hugging zorunluluğu)", 2, 0, 1),
    ChecklistItem("q3", "A) ROL TARİFİ UYUMU", "Oyuncu “tek başına çöz” moduna itilmiş mi? (izole 1v2–1v3)", 2, 0, 1),
    ChecklistItem("q4", "A) ROL TARİFİ UYUMU", "Top aldığı bölgeler, en verimli bölgeyle örtüşüyor mu?", 0, 1, 1),
    # B) Support & link-up
    ChecklistItem("q5", "B) DESTEK VE BAĞLANTILAR", "Aynı koridorda duvar/istasyon var mı? (10/8, iç oyuncu)", 0, 2, 1),
    ChecklistItem("q6", "B) DESTEK VE BAĞLANTILAR", "Overlap/underlap desteği planlı mı? (bek/kanat arası)", 0, 1, 1),
    ChecklistItem("q7", "B) DESTEK VE BAĞLANTILAR", "9 numara stoperleri sabitliyor mu? (pinning)", 0, 1, 1),
    ChecklistItem("q8", "B) DESTEK VE BAĞLANTILAR", "Ters kanat arka direk koşusu var mı? (space-occupancy)", 0, 1, 1),
    # C) Flow & touches
    ChecklistItem("q9", "C) OYUN AKIŞI VE TOPA DOKUNUŞ", "İlk 20 dakikada oyuncu hedefli 3+ temas aldı mı?", 0, 1, 1),
    ChecklistItem("q10", "C) OYUN AKIŞI VE TOPA DOKUNUŞ", "Oyuncu topu sürekli kapalı vücutla mı alıyor?", 2, 0, 1),
    ChecklistItem("q11", "C) OYUN AKIŞI VE TOPA DOKUNUŞ", "Topu aldığı anlarda “ikinci opsiyon” var mı? (pas çıkışı)", 0, 1, 1),
    # D) Risk management
    ChecklistItem("q12", "D) RİSK YÖNETİMİ", "Oyuncunun yük yönetimi planlı mı? (haftalık dakika/yoğunluk)", 0, 1, 1),
    ChecklistItem("q13", "D) RİSK YÖNETİMİ", "Fiziksel temas yoğunluğu oyuncu profiline göre ayarlanmış mı?", 0, 1, 1),
    ChecklistItem("q14", "D) RİSK YÖNETİMİ", "Rol iletişimi ve güven çerçevesi kurulmuş mu?", 0, 1, 1),
]


LIVE_TRIGGERS_V22: List[str] = [
    "Oyuncu 10 dakikada 2+ kez 1v2/1v3’e zorlanıyor.",
    "Top kaybı sonrası geri koşu/itiraz artıyor (psikodinamik stres).",
    "Topu aldığı her pozisyonda çizgiye sıkışma ve geri pas zorunluluğu.",
    "Duvar oyuncu yokluğu nedeniyle sürekli “ters tarafa şişirme” veya düşük kaliteli şut.",
    "Bek desteği yok; oyuncu sürekli dur-kalk yapıyor (yük artışı).",
]


# ------------------------------------------------------------
# Template I/O (no external deps)
# ------------------------------------------------------------
def _load_template() -> str:
    base = Path(__file__).resolve().parent.parent  # hp_motor/
    p = base / "templates" / "role_mismatch_alarm_v22.md"
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _render(template_text: str, ctx: Dict[str, Any]) -> str:
    out = template_text or ""
    for k, v in (ctx or {}).items():
        out = out.replace("{{" + k + "}}", "" if v is None else str(v))
    return out


# ------------------------------------------------------------
# Engine
# ------------------------------------------------------------
class RoleMismatchAlarmEngine:
    """
    HP ENGINE v22.x — Role Mismatch Alarm Checklist (Risk Scoring)

    Contract:
      - Input answers are EVET/HAYIR/BILINMIYOR per question id (q1..q14)
      - Output:
          total_score (0..14),
          band (YESIL/SARI/KIRMIZI),
          plus band_after_triggers,
          plus action matrix + filled markdown.

    Epistemic discipline:
      - Unknown is not treated as “safe”; unknown -> conservative half-risk.
    """

    ENGINE_VERSION = "HP ENGINE v22.x"

    def score(
        self,
        *,
        answers: Dict[str, Answer],
        live_triggers: Optional[List[bool]] = None,
        context_note: str = "",
    ) -> RoleMismatchResult:
        pts: Dict[str, int] = {}
        normalized: Dict[str, Answer] = {}
        diagnostics: Dict[str, Any] = {"context_note": context_note}

        # 1) score checklist
        total = 0
        for item in CHECKLIST_V22:
            raw = answers.get(item.id, "BILINMIYOR")
            a: Answer = raw if raw in ("EVET", "HAYIR", "BILINMIYOR") else "BILINMIYOR"
            normalized[item.id] = a

            if a == "EVET":
                p = int(item.points_if_yes)
            elif a == "HAYIR":
                p = int(item.points_if_no)
            else:
                p = int(item.points_if_unknown)

            pts[item.id] = p
            total += p

        band = self._band(total)

        # 2) live triggers raise band by 1 step if >=2 hit
        live_triggers = live_triggers or [False] * len(LIVE_TRIGGERS_V22)
        hit = int(sum(1 for x in live_triggers if bool(x)))

        band_after = band
        if hit >= 2:
            band_after = self._raise_band(band)

        # 3) actions (always returned)
        actions = self._actions()

        # 4) judgement line
        judgement = self._judgement_line(total_score=total, band=band, band_after=band_after, hit=hit)

        # 5) markdown render
        md = self.render_markdown(
            answers=normalized,
            points=pts,
            total_score=total,
            band=band,
            band_after_triggers=band_after,
            live_triggers=live_triggers,
            actions=actions,
            judgement_line=judgement,
        )

        diagnostics.update(
            {
                "engine_version": self.ENGINE_VERSION,
                "total_score": total,
                "band": band,
                "live_triggers_hit": hit,
                "band_after_triggers": band_after,
            }
        )

        return RoleMismatchResult(
            total_score=total,
            band=band,
            answers=normalized,
            points=pts,
            live_triggers_hit=hit,
            band_after_triggers=band_after,
            actions=actions,
            judgement_line=judgement,
            markdown=md,
            diagnostics=diagnostics,
        )

    def render_markdown(
        self,
        *,
        answers: Dict[str, Answer],
        points: Dict[str, int],
        total_score: int,
        band: Band,
        band_after_triggers: Band,
        live_triggers: List[bool],
        actions: Dict[str, List[str]],
        judgement_line: str,
    ) -> str:
        tpl = _load_template()

        # live triggers block
        lines = []
        for i, t in enumerate(LIVE_TRIGGERS_V22):
            hit = "EVET" if (i < len(live_triggers) and live_triggers[i]) else "HAYIR"
            lines.append(f"- {t} — **{hit}**")
        live_block = "\n".join(lines) if lines else "- (tetikleyici listesi yok)"

        def _block(xs: List[str]) -> str:
            if not xs:
                return "- (aksiyon yok)"
            return "\n".join([f"- {x}" for x in xs])

        ctx: Dict[str, Any] = {
            # answers & points
            **{f"q{i}_answer": answers.get(f"q{i}", "BILINMIYOR") for i in range(1, 15)},
            **{f"q{i}_points": f"+{points.get(f'q{i}', 0)}" for i in range(1, 15)},
            "total_score": total_score,
            "band": band_after_triggers if band_after_triggers != band else band,
            "live_triggers_block": live_block,
            "green_actions_block": _block(actions["YESIL"]),
            "yellow_actions_block": _block(actions["SARI"]),
            "red_actions_block": _block(actions["KIRMIZI"]),
            "judgement_line": judgement_line,
        }

        # if template missing, return minimal stable text
        if not tpl:
            return (
                f"# {self.ENGINE_VERSION} — Rol Uyumsuzluğu Alarm Checklist’i\n\n"
                f"Toplam Skor: {total_score}/14 | Seviye: {band_after_triggers}\n\n"
                f"> {judgement_line}\n"
            )

        return _render(tpl, ctx)

    # ------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------
    @staticmethod
    def _band(score: int) -> Band:
        if score <= 3:
            return "YESIL"
        if score <= 7:
            return "SARI"
        return "KIRMIZI"

    @staticmethod
    def _raise_band(band: Band) -> Band:
        if band == "YESIL":
            return "SARI"
        if band == "SARI":
            return "KIRMIZI"
        return "KIRMIZI"

    @staticmethod
    def _actions() -> Dict[str, List[str]]:
        return {
            "YESIL": [
                "Mevcut rol korunur. Üretim hedefi ve varyasyonlar artırılır.",
            ],
            "SARI": [
                "Aynı koridora duvar oyuncu ekle (10/8 veya iç forvet).",
                "Bek bindirmesini planla (overlap/underlap) → oyuncuyu half-space’e sok.",
                "Ters kanadı arka direğe gönder → cut-back hedefi yarat.",
            ],
            "KIRMIZI": [
                "Oyuncuyu çizgiden çıkar; half-space top alış sayısını artır.",
                "İzolasyonu kaldır; 2. opsiyon (pas çıkışı) garanti et.",
                "Dakika/yük yönetimini maç planına entegre et.",
                "Rol iletişimini netleştir: “Ne yapması isteniyor / ne istenmiyor?”",
            ],
        }

    @staticmethod
    def _judgement_line(total_score: int, band: Band, band_after: Band, hit: int) -> str:
        if band_after != band:
            return (
                f"Skor {total_score}/14 → {band}; canlı tetikleyiciler {hit} adet, seviye {band_after}’a yükseltildi. "
                "Hüküm oyuncuya değil bağlama yazılır."
            )

        if band == "YESIL":
            return "Rol doğru. Performans yorumu geçerli; varyasyon artırılabilir."
        if band == "SARI":
            return "Performans dalgalanması beklenir. 1–2 destek/rol düzeltmesi şart."
        return "“Yanlış bağlam” alarmı. Rol revizyonu olmadan oyuncu hükmü verilmez."