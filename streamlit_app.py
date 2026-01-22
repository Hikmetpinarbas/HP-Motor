import streamlit as st
from engine.validator import SOTValidator
from engine.processor import HPProcessor
from engine.analyst import HPAnalyst

st.set_page_config(page_title="HP Motor v1.1", layout="wide")
st.title("🛡️ HP Motor v1.1 | Sovereign Intelligence")

uploaded_file = st.file_uploader("SportsBase / CSV Yükle", type=['csv'])

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file, sep=';')
    
    # KÜMÜLATİF AKIŞ: Validator -> Processor -> Analyst
    report, data = SOTValidator().validate_and_normalize(raw_df)
    data = HPProcessor().apply_lens(data)
    claim = HPAnalyst().create_evidence_chain("Atletico Savunma Bloğu (F1) Kompakt", "ppda < 10")
    
    # UI: Altın Oran (%61.8 Ana / %38.2 Yan)
    col_main, col_side = st.columns([618, 382])
    with col_main:
        st.subheader("🏟️ Saper Vedere (Görsel Kanıt)")
        st.dataframe(data.head(20))
    with col_side:
        st.subheader("💡 Chiaroscuro Analysis (Sinyal)")
        st.success(f"**Hipotez:** {claim['text']}")
        st.warning(f"**Yanlışlama:** {claim['falsification']['test']}")
