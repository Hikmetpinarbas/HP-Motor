import streamlit as st
import pandas as pd
from engine.orchestrator import MasterOrchestrator
from engine.processor import HPProcessor
from engine.analysis import HPAnalysisEngine

st.set_page_config(page_title="HP Motor v1.0", layout="wide")

# Caravaggio UI: Chiaroscuro (Siyah zemin, altın vurgu)
st.markdown("""
    <style>
    .main { background-color: #050505; color: #ffffff; }
    .stExpander { background-color: #111111; border: 1px solid #FFD700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ HP Motor v1.0 | Sovereign Intelligence")

uploaded_file = st.file_uploader("Dosyayı Yükle (CSV/XLSX/ZIP)", type=['csv', 'xlsx', 'zip'])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    
    # 1. Processing (6 Faz & Katman)
    processor = HPProcessor()
    df = processor.segment_phases(df)
    df = processor.apply_layers(df)
    
    # 2. Analysis (Claims)
    analyst = HPAnalysisEngine()
    # Örnek hipotez üretimi
    claim = analyst.create_claim(
        "Atletico duran top (F5) organizasyonunda domine ediyor.",
        df,
        "set_piece_xg > 0.3"
    )
    
    # UI Yerleşimi: Altın Oran (%61.8 - %38.2)
    col_main, col_side = st.columns([618, 382])
    
    with col_main:
        st.subheader("🏟️ Saper Vedere (Görmeyi Bilmek)")
        # Buraya Da Vinci hassasiyetinde saha çizimleri gelecek
        st.dataframe(df[['action', 'phase_hp', 'layer_hp', 'x_std', 'y_std']].head(20))

    with col_side:
        st.subheader("💡 Chiaroscuro Analysis")
        for c in claim['claims']:
            with st.expander(f"İddia: {c['text']}", expanded=True):
                st.write(f"**Güven Skoru:** %{c['confidence']['score']*100}")
                st.warning(f"**Yanlışlama Testi:** {c['falsification']['tests'][0]['name']}")
                st.info(f"**Durum:** {c['status']}")

st.sidebar.markdown("---")
st.sidebar.write("HP Motor v1.0 | Karl Popper Epistemolojisi ile Çalışır.")
