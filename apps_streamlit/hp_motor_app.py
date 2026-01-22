import streamlit as st
import pandas as pd
from src.engine.validator import SOTValidator
from src.engine.processor import HPProcessor
from src.engine.analyst import HPAnalyst

st.set_page_config(page_title="HP Motor v1.4", layout="wide")

# Caravaggio Chiaroscuro Style
st.markdown("<style>.main { background-color: #050505; color: #ffffff; }</style>", unsafe_allow_html=True)

st.title("🛡️ HP Motor v1.4 | Sovereign Intelligence")

uploaded_file = st.file_uploader("Veri Yükle (CSV/XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # KÜMÜLATİF AKIŞ
    report, clean_df = SOTValidator().clean_and_normalize(df)
    processed_df = HPProcessor().apply_lens_and_logic(clean_df)
    analysis = HPAnalyst().generate_report(
        "Forvet Bitiricilik (SGA) Performansı Beklentinin Üstünde.",
        "SGA < 0 ise hipotez yanlışlanır."
    )
    
    # UI: ALTIN ORAN YERLEŞİMİ
    col_main, col_side = st.columns([618, 382])
    
    with col_main:
        st.subheader("🏟️ Saper Vedere (Gözlem)")
        st.dataframe(processed_df.head(20))

    with col_side:
        st.subheader("💡 Chiaroscuro Panel (Sinyal)")
        for c in analysis['claims']:
            st.info(f"**Hipotez:** {c['text']}")
            st.warning(f"**Yanlışlama:** {c['falsification']['test']}")
            st.write(f"**Referans:** {c['citations'][0]['ref_id']}")
