# ============================================================
# HP MOTOR — STREAMLIT APPLICATION
# Canonical, src-layout safe, CI & Android compatible
# ============================================================

import sys
from pathlib import Path

# ------------------------------------------------------------
# SRC-LAYOUT BOOTSTRAP (NO ASSUMPTIONS)
# ------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

# ------------------------------------------------------------
# STANDARD LIBS
# ------------------------------------------------------------
import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# HP MOTOR IMPORTS
# ------------------------------------------------------------
from hp_motor.pipelines.run_analysis import SovereignOrchestrator
from hp_motor.modules.individual_review import IndividualReviewEngine

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="HP Motor",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("HP Motor — Sovereign Analysis Engine")

# ============================================================
# FILE UPLOAD
# ============================================================
st.sidebar.header("Veri Girişi")

uploaded_file = st.sidebar.file_uploader(
    "CSV veri dosyası yükle",
    type=["csv"],
)

if uploaded_file is None:
    st.info("Analiz başlatmak için bir CSV dosyası yükle.")
    st.stop()

# ============================================================
# LOAD DATA
# ============================================================
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"CSV okunamadı: {e}")
    st.stop()

st.success("Veri başarıyla yüklendi.")
st.caption(f"Satır: {len(df)} | Kolon: {len(df.columns)}")

# ============================================================
# CONTROL PANEL
# ============================================================
st.sidebar.divider()
st.sidebar.header("Analiz Ayarları")
phase = st.sidebar.selectbox("Phase", ["open_play", "set_piece", "transition"], index=0)
role = st.sidebar.selectbox("Role", ["Mezzala", "Pivot", "Winger", "CB", "FB"], index=0)

# ============================================================
# MAIN ANALYSIS (SOVEREIGN PIPELINE)
# ============================================================
st.header("Sistemik Analiz (Sovereign)")

orchestrator = SovereignOrchestrator()

try:
    sovereign_output = orchestrator.run(df, phase=phase, role=role)
except Exception as e:
    st.error(f"Sistemik analiz çalıştırılamadı: {e}")
    st.stop()

# --- verdict header
status = sovereign_output.get("status", "UNKNOWN")
confidence = (sovereign_output.get("evidence_graph") or {}).get("overall_confidence", "unknown")
st.subheader(f"Durum: {status} | Güven: {confidence}")

# --- diagnostics
with st.expander("Diagnostics (neden / sınırlar / kalite)", expanded=(status != "OK")):
    st.json(sovereign_output.get("diagnostics", {}))

# --- evidence
with st.expander("Evidence Graph (hüküm değil: gerekçe)", expanded=True):
    st.json(sovereign_output.get("evidence_graph", {}))

# --- metrics
st.subheader("Metrikler")
st.dataframe(pd.DataFrame(sovereign_output.get("metrics", [])), use_container_width=True)

# --- tables
st.subheader("Tablolar")
tables = sovereign_output.get("tables", {}) or {}
if not tables:
    st.info("Tablo üretilmedi.")
else:
    for k, v in tables.items():
        st.markdown(f"**{k}**")
        try:
            st.dataframe(v, use_container_width=True)
        except Exception:
            st.write(v)

# --- lists
st.subheader("Listeler / Bullet çıktılar")
lists = sovereign_output.get("lists", {}) or {}
if not lists:
    st.info("Liste üretilmedi.")
else:
    for k, v in lists.items():
        st.markdown(f"**{k}**")
        st.write(v)

# --- figures
st.subheader("Figürler")
figs = sovereign_output.get("figure_objects", {}) or {}
if not figs:
    st.info("Figür üretilmedi (x/y kolonu yoksa beklenir).")
else:
    for k, fig in figs.items():
        st.markdown(f"**{k}**")
        try:
            st.pyplot(fig, clear_figure=False, use_container_width=True)
        except Exception:
            st.write(fig)

# ============================================================
# INDIVIDUAL REVIEW MODULE
# ============================================================
st.divider()
st.header("Bireysel İnceleme (Individual Review)")

if "player_id" not in df.columns:
    st.warning(
        "Bu veri setinde 'player_id' sütunu yok.\n\n"
        "Bireysel inceleme için player_id zorunludur."
    )
    st.stop()

player_ids = sorted(df["player_id"].dropna().unique().tolist())
if len(player_ids) == 0:
    st.warning("player_id kolonunda geçerli değer yok.")
    st.stop()

selected_player = st.selectbox("Oyuncu Seç (player_id)", player_ids)

individual_engine = IndividualReviewEngine()

try:
    profile = individual_engine.build_player_profile(
        df=df,
        player_id=int(selected_player),
    )
except Exception as e:
    st.error(f"Bireysel analiz çalıştırılamadı: {e}")
    st.stop()

st.subheader("Özet (Summary)")
st.json(profile.summary)

with st.expander("Diagnostics", expanded=False):
    st.json(profile.diagnostics)

st.subheader("Detaylı Metrikler")
metrics_df = pd.DataFrame(profile.metrics)
st.dataframe(metrics_df, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "HP Motor — Veri yoksa susar. "
    "Çelişki varsa uyarır. "
    "Geometri bozuksa alarm verir."
)