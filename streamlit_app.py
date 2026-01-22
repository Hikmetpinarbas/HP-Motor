import streamlit as st
import pandas as pd
from engine.orchestrator import MasterOrchestrator

st.set_page_config(page_title="HP Motor v1.0", layout="wide", initial_sidebar_state="expanded")

# UI Stil Ayarları
st.markdown("<style>.main { background-color: #050505; color: #ffffff; }</style>", unsafe_allow_html=True)

st.title("🛡️ HP Motor v1.0 | Sovereign Intelligence")

uploaded_file = st.file_uploader("SportsBase / CSV / Excel Verisi Yükle", type=['csv', 'xlsx'])

if uploaded_file:
    # Veri Okuma
    df = pd.read_csv(uploaded_file, sep=';') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    engine = MasterOrchestrator()
    output = engine.run_analysis(df)
    
    # 6 Fazlı Lens Paneli
    st.sidebar.header("🔍 6 Fazlı Lens")
    selected_phase = st.sidebar.selectbox("Analiz Fazı Seçin", 
                                        ["Tümü", "F1: Organized Defense", "F2: Defensive Transition", 
                                         "F3: Organized Attack", "F4: Offensive Transition", 
                                         "F5: Set Pieces (Att)", "F6: Set Pieces (Def)"])

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Klinik Tespit")
        st.metric("Veri Kapsamı", f"%{output['report']['health_score']*100:.1f}")
        st.write(f"SOT Durumu: **{output['report']['status']}**")
        
    with col2:
        st.subheader("📊 Kanıt Zinciri (Popperian Claims)")
        if not output['claims']:
            st.info("Henüz yeterli kanıt zinciri oluşturulmadı. Daha fazla veri bekleniyor.")
        for claim in output['claims']:
            st.success(f"**Hipotez:** {claim['hypothesis']}")
            st.write(f"**Kanıtlar:** {', '.join(claim['evidence'])}")
            st.warning(f"**Yanlışlama Testi:** {claim['falsification']}")

    st.divider()
    st.subheader("İşlenmiş Veri (HP-CDL Standart)")
    st.dataframe(output['data'].head(20))
