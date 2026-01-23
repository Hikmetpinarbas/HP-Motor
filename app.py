import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# 1. Klasör Yolunu Tanımla
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError as e:
    st.error(f"Kritik Hata: 'src' klasörü altındaki dosyalar okunamıyor. Hata: {e}")
    st.stop()

# --- Arayüz Yapılandırması ---
st.set_page_config(page_title="HP MOTOR v6.0", layout="wide", page_icon="🛡️")
st.title("🛡️ HP MOTOR v6.0 | ARCHITECT")

@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()

# --- Yan Menü ---
st.sidebar.header("📥 Veri Girişi")
uploaded_files = st.sidebar.file_uploader("Sinyalleri Bırakın (CSV, MP4, XLSX)", accept_multiple_files=True)
persona = st.sidebar.selectbox("Analiz Personası", ["Match Analyst", "Scout", "Technical Director"])

# --- Semantik Faz Algılayıcı ---
def detect_phase(filename):
    fname = filename.lower()
    if any(k in fname for k in ["pozisyon", "hucum", "attack", "offensive"]): return "PHASE_OFFENSIVE"
    if any(k in fname for k in ["savunma", "defans", "defensive", "block"]): return "PHASE_DEFENSIVE"
    if any(k in fname for k in ["gecis", "geçiş", "transition", "counter"]): return "PHASE_TRANSITION"
    return "ACTION_GENERIC"

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.expander(f"⚙️ Analiz: {uploaded_file.name}", expanded=True):
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            phase = detect_phase(uploaded_file.name)
            
            try:
                # Veri Okuma
                if file_ext == '.csv': df = pd.read_csv(uploaded_file, sep=None, engine='python')
                elif file_ext in ['.xlsx', '.xls']: df = pd.read_excel(uploaded_file).reset_index()
                elif file_ext == '.mp4': 
                    st.video(uploaded_file)
                    df = pd.DataFrame([{"visual": "stream"}])
                else: df = pd.DataFrame([{"raw": "signal"}])

                # Koordinat Transformasyonu (SportsBase 0-100 -> Canonical 105x68)
                if 'x' in df.columns: df['x_m'] = (df['x'] / 100.0) * 105.0
                if 'y' in df.columns: df['y_m'] = (df['y'] / 100.0) * 68.0

                # Analiz Motorunu Ateşle
                with st.spinner("Sovereign Intelligence İşleniyor..."):
                    analysis = orchestrator.execute_full_analysis(df, phase)
                    verdict = get_agent_verdict(analysis, persona)
                
                # Görselleştirme
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Veri Sağlığı", f"%{int(analysis['confidence']*100)}")
                    st.info(f"Faz: {phase}")
                with c2:
                    st.warning(f"**Sovereign Verdict:** {verdict}")

            except Exception as e:
                st.error(f"Dosya analiz edilemedi: {e}")
else:
    st.info("Sinyal bekleniyor... Saper Vedere.")
