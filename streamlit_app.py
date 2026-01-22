import streamlit as st
import pandas as pd
from engine.validator import SOTValidator
from engine.processor import HPProcessor
from engine.analyst import HPAnalyst

st.set_page_config(page_title="HP Motor v1.2", layout="wide")

# Chiaroscuro CSS (Caravaggio Teması)
st.markdown("<style>.main { background-color: #050505; color: #ffffff; }</style>", unsafe_allow_html=True)

st.title("🛡️ HP Motor v1.2 | Master Build")

uploaded_file = st.file_uploader("Veri Yükle", type=['csv'])

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file, sep=';')
    
    # MASTER FLOW: validator -> processor -> analyst
    report, data = SOTValidator().validate_and_normalize(raw_df)
    data = HPProcessor().process(data)
    claim = HPAnalyst().generate_claim("Atletico Savunma Bloğu Kompakt", "ppda < 10", data)
    
    # UI: Altın Oran Yerleşimi
    col_main, col_side = st.columns([618, 382])
    
    with col_main:
        st.subheader("🏟️ Saper Vedere (Anatomik Gözlem)")
        st.dataframe(data.head(25))

    with col_side:
        st.subheader("💡 Chiaroscuro Analysis")
        st.success(f"**Hipotez:** {claim['text']}")
        st.warning(f"**Yanlışlama:** {claim['falsification']['test']}")
