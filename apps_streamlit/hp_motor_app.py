import streamlit as st
import pandas as pd
from src.engine.validator import SOTValidator
from src.engine.processor import HPProcessor
from src.engine.analyst import HPAnalyst

st.set_page_config(page_title="HP Motor v1.3", layout="wide")

# Chiaroscuro UI (Caravaggio Teması)
st.markdown("<style>.main { background-color: #050505; color: #ffffff; }</style>", unsafe_allow_html=True)

st.title("🛡️ HP Motor v1.3 | Sovereign Intelligence")

uploaded_file = st.file_uploader("SportsBase / CSV / XLSX Verisi Yükle", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 1. VALIDATE (Kazanım: 0.0 Koruma)
    report, clean_df = SOTValidator().clean_and_normalize(df)
    
    # 2. PROCESS (Kazanım: 6 Faz & 3 Katman)
    processed_df = HPProcessor().apply_lens(clean_df)
    
    # 3. ANALYZE (Kazanım: Popperian Claims)
    # Örnek: Atletico Madrid - Galatasaray Pre-match verisini simüle ediyoruz
    analyst = HPAnalyst()
    claim = analyst.generate_evidence_chain(
        "Atletico Madrid duran top (F6) dominansı ile avantajlı.",
        "SetPiece_xG > 0.3",
        {"set_piece_goals": 4}
    )
    
    # UI: ALTIN ORAN YERLEŞİMİ (%61.8 - %38.2)
    col_main, col_side = st.columns([618, 382])
    
    with col_main:
        st.subheader("🏟️ Saper Vedere (Anatomik Gözlem)")
        st.dataframe(processed_df[['action', 'phase_hp', 'layer_hp', 'x_std', 'y_std']].head(20))

    with col_side:
        st.subheader("💡 Chiaroscuro Analysis (Sinyal)")
        for c in claim['claims']:
            with st.expander(f"İddia: {c['text']}", expanded=True):
                st.write(f"**Güven:** %{c['confidence']['score']*100}")
                st.warning(f"**Test:** {c['falsification']['tests'][0]['name']}")
                st.info(f"**Koşul:** {c['falsification']['tests'][0]['pass_condition']}")
