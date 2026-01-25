# ============================================================
# HP MOTOR — Single-File App Layer (Manifest + Ontology + Audit)
# Streamlit-first. No FastAPI.
# Purpose:
#  - Provide a stable "single entrypoint" UI
#  - Expose manifest / ontology / audit / dictionary in one place
#  - Keep optional bridges to hp_motor modules without breaking boot
# ============================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

# -----------------------------
# SRC-LAYOUT BOOTSTRAP
# -----------------------------
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

# -----------------------------
# 0) HARD RULES (Popper-like audit contract)
# -----------------------------
POPPER_AUDIT_CONTRACT: Dict[str, Any] = {
    "zero_prediction": True,
    "evidence_requirement": "evidence_only",
    "audit_mode": "falsification_first",
    "no_default_speaking": True,   # if data missing -> abstain/degraded, never default claims
    "absence_is_not_evidence": True,
}

# -----------------------------
# 1) “WHAT WE DID HERE” (single text)
# -----------------------------
HP_MOTOR_CONVERSATION_CORE = """
HP MOTOR — Conversation Consolidation (Working Summary)

HP Motor; futbolu mevki etiketlerinden bağımsız olarak oyun fazları, rol fonksiyonu, bağlam ve kanıt üzerinden modelleyen;
veri yoksa susan (ABSTAIN), kanıt zayıfsa degrade olan (DEGRADED), kanıt tutarlıysa konuşan (OK) bir analiz motorudur.

Bu çalışmada:
- Repo/CI seviyesinde import ve smoke test stabilitesi sağlandı (yeşil).
- “Veri okunuyor ama tablo/figür boş” probleminin kök nedeni belirlendi:
  Ingest → Canonical Mapping → Metric Compute → Deliverables zincirinin ortası eksikti.
- v22 bireysel şablonlar (Bireysel Analiz / Scouting Card / Role Mismatch Alarm) sistemin kalıcı çıktıları olarak konumlandı.
- “Default ile konuşma” epistemik kırmızı çizgi yapıldı: veri yoksa sus, uydurma yok.

Sıradaki kritik iş:
- Canonical mapping'in pipeline'a bağlanması ve compute hattının report builder'ı beslemesi.
""".strip()

# -----------------------------
# 2) ONTOLOGY (phases + minimal calibration)
# -----------------------------
PHASE_INDEX = [
    {"id": 1, "key": "IP",  "name": "IN-POSSESSION",        "goal": "Manipulation"},
    {"id": 2, "key": "AD",  "name": "A-D TRANSITION",       "goal": "5-Second Rule"},
    {"id": 3, "key": "OP",  "name": "OUT-OF-POSSESSION",    "goal": "Compactness"},
    {"id": 4, "key": "DA",  "name": "D-A TRANSITION",       "goal": "Verticality"},
    {"id": 5, "key": "ASP", "name": "ATTACKING SET-PIECE",  "goal": "Set-design"},
    {"id": 6, "key": "DSP", "name": "DEFENDING SET-PIECE",  "goal": "Clean-exit"},
]

METRIC_CALIBRATION = {
    "compactness_threshold_m": 25,
    "scan_elite_rate_s_per_scan": 0.6,
    "body_angle_limit_deg": 30,
}

# -----------------------------
# 3) OPTIONAL BRIDGES to hp_motor (do not break boot)
# -----------------------------
SovereignOrchestrator = None
IndividualReviewEngine = None

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator as _SO  # type: ignore
    SovereignOrchestrator = _SO
except Exception:
    SovereignOrchestrator = None

try:
    from hp_motor.modules.individual_review import IndividualReviewEngine as _IE  # type: ignore
    IndividualReviewEngine = _IE
except Exception:
    IndividualReviewEngine = None


# -----------------------------
# 4) Helpers
# -----------------------------
def _safe_read_json(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _download_json(name: str, payload: Dict[str, Any]) -> None:
    st.download_button(
        label=f"Download: {name}",
        data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=name,
        mime="application/json",
        use_container_width=True,
    )


def _build_manifest() -> Dict[str, Any]:
    return {
        "product": "HP Motor",
        "entrypoint": "app.py (Streamlit)",
        "contracts": {
            "popper_audit": POPPER_AUDIT_CONTRACT,
            "ontology": {"phases": PHASE_INDEX, "calibration": METRIC_CALIBRATION},
        },
        "modules": {
            "sovereign_orchestrator_available": bool(SovereignOrchestrator),
            "individual_review_available": bool(IndividualReviewEngine),
        },
        "status_notes": {
            "core_goal": "No empty deliverables. No default speaking. Evidence-first.",
            "next_step": "Bind canonical mapping to pipeline; feed report builder with computed metrics.",
        },
    }


# -----------------------------
# 5) Streamlit UI
# -----------------------------
st.set_page_config(page_title="HP Motor — Manifest & Clinic", layout="wide")
st.title("HP Motor — Manifest / Ontology / Audit / Clinic")

manifest = _build_manifest()

tabs = st.tabs([
    "About",
    "Conversation Core",
    "Ontology",
    "Dictionary",
    "Audit",
    "Health",
    "Analysis (Optional)",
])

# --- About
with tabs[0]:
    st.subheader("Net Tanım + Modül Sayısı + Amaç")
    st.write(
        "HP Motor, faz–rol–bağlam–kanıt ekseninde çalışan; veri yoksa susan ve çıktıyı "
        "kanıt zinciriyle mühürleyen bir Streamlit analiz uygulamasıdır."
    )
    st.markdown("### Manifest")
    st.json(manifest)
    _download_json("hp_motor_manifest.json", manifest)

# --- Conversation Core
with tabs[1]:
    st.subheader("Bu sayfada neler yaptık / nereden nereye geldik?")
    st.code(HP_MOTOR_CONVERSATION_CORE, language="markdown")
    _download_json("hp_motor_conversation_core.json", {"text": HP_MOTOR_CONVERSATION_CORE})

# --- Ontology
with tabs[2]:
    st.subheader("Faz Ontolojisi + Kalibrasyon")
    st.json({"phases": PHASE_INDEX, "calibration": METRIC_CALIBRATION})
    _download_json("hp_motor_ontology.json", {"phases": PHASE_INDEX, "calibration": METRIC_CALIBRATION})

# --- Dictionary
with tabs[3]:
    st.subheader("Dictionary (opsiyonel)")
    st.caption("Repo kökünde dictionary.json varsa okur; yoksa boş döner.")
    data = _safe_read_json(str(ROOT / "dictionary.json"))
    st.json({"dictionary": data})
    _download_json("hp_motor_dictionary.json", {"dictionary": data})

# --- Audit
with tabs[4]:
    st.subheader("Popper / Audit Sözleşmesi")
    st.json(POPPER_AUDIT_CONTRACT)
    st.caption("Bu sözleşme: veri yoksa susmayı, yokluğu kanıt saymamayı ve default ile konuşmamayı zorunlu kılar.")
    _download_json("hp_motor_audit_contract.json", {"audit": POPPER_AUDIT_CONTRACT})

# --- Health
with tabs[5]:
    st.subheader("Health")
    health = {
        "status": "ok",
        "modules": {
            "SovereignOrchestrator": bool(SovereignOrchestrator),
            "IndividualReviewEngine": bool(IndividualReviewEngine),
        },
        "paths": {
            "root": str(ROOT),
            "src_exists": SRC.exists(),
        },
    }
    st.json(health)
    _download_json("hp_motor_health.json", health)

# --- Analysis (Optional)
with tabs[6]:
    st.subheader("Analysis (Optional Bridges)")
    st.caption(
        "Bu bölüm, repo'da ilgili motor modülleri varsa çalışır. "
        "Yoksa uygulama yine ayağa kalkar ve sadece manifest/ontology servis eder."
    )

    if SovereignOrchestrator is None:
        st.warning("SovereignOrchestrator import edilemedi. (Normal: bu bir iskelet katmanı.)")
    else:
        st.markdown("### Sovereign Orchestrator — Minimal Run")
        uploaded = st.file_uploader("CSV yükle (opsiyonel)", type=["csv"])
        if uploaded is not None:
            import pandas as pd  # local import to avoid unnecessary dependency cost

            df = pd.read_csv(uploaded)
            st.caption(f"Rows: {len(df)} | Cols: {len(df.columns)}")
            phase = st.selectbox("Phase", ["open_play", "set_piece", "transition"], index=0)
            role = st.selectbox("Role", ["mezzala", "pivot", "winger_solver", "cb", "fb"], index=0)

            orch = SovereignOrchestrator()
            try:
                out = orch.run(df, phase=phase, role=role)
            except Exception as e:
                st.error(f"Orchestrator error: {e}")
                out = {}

            st.json(out)

    st.divider()

    if IndividualReviewEngine is None:
        st.warning("IndividualReviewEngine import edilemedi. (Normal: bu bir iskelet katmanı.)")
    else:
        st.markdown("### Individual Review — v22 Template Output")
        uploaded2 = st.file_uploader("CSV yükle (bireysel analiz için)", type=["csv"], key="ind_csv")
        if uploaded2 is not None:
            import pandas as pd

            df2 = pd.read_csv(uploaded2)
            if "player_id" not in df2.columns:
                st.error("Bu veri setinde 'player_id' yok. Bireysel analiz için zorunlu.")
            else:
                player_ids = sorted(df2["player_id"].dropna().unique().tolist())
                pid = st.selectbox("player_id", player_ids)
                role2 = st.selectbox("role_id", ["mezzala", "pivot", "winger_solver", "cb", "fb"], index=0, key="ind_role")

                engine = IndividualReviewEngine()
                profile = engine.build_player_profile(df=df2, player_id=int(pid), role_id=role2)

                st.json(profile.summary)
                with st.expander("Player Analysis v22", expanded=False):
                    st.markdown(profile.player_analysis_markdown)
                with st.expander("Scouting Card v22", expanded=False):
                    st.markdown(profile.scouting_card_markdown)
                with st.expander("Role Mismatch Alarm", expanded=True):
                    st.markdown(profile.role_mismatch_alarm_markdown)