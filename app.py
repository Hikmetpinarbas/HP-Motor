import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# 1. YOL TANIMLAMA
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError:
    st.error("Kritik Hata: 'src/hp_motor' klasörü doğrulanamadı.")
    st.stop()

# --- ESKİ PROJEDEN GELEN SEMANTİK KURALLAR ---
# 'action' hatasını çözecek anahtar eşlemeler
SEMANTIC_TAGS = {
    "PHASE_OFFENSIVE": ["pozisyon", "hucum", "hücum", "attack", "offensive", "final third"],
    "PHASE_DEFENSIVE": ["savunma", "defans", "defensive", "baski", "baskı", "block"],
    "PHASE_TRANSITION": ["gecis", "geçiş", "counter", "transition"]
}

st.set_page_config(page_title="HP MOTOR v5.0", layout="wide")
st.title("🛡️ HP MOTOR v5.0 | ACTION ALIGNER")

@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()

# --- YAN MENÜ ---
uploaded_files = st.sidebar.file_uploader("Sinyalleri Yükle", accept_multiple_files=True)
persona = st.sidebar.selectbox("Persona", ["Match Analyst", "Scout", "Technical Director"])

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.expander(f"📄 İşleniyor: {uploaded_file.name}", expanded=True):
            file_name_lower = uploaded_file.name.lower()
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            # Semantik Teşhis
            detected_code = "ACTION_GENERIC"
            for phase, keywords in SEMANTIC_TAGS.items():
                if any(k in file_name_lower for k in keywords):
                    detected_code = phase
                    break

            try:
                # 1. VERİ OKUMA
                if file_ext == '.csv':
                    try: df_raw = pd.read_csv(uploaded_file, sep=';')
                    except: 
                        uploaded_file.seek(0)
                        df_raw = pd.read_csv(uploaded_file, sep=',')
                elif file_ext in ['.xlsx', '.xls']:
                    df_raw = pd.read_excel(uploaded_file).reset_index()
                elif file_ext == '.mp4':
                    st.video(uploaded_file)
                    df_raw = pd.DataFrame([{"visual": "video_stream"}])
                else:
                    df_raw = pd.DataFrame([{"signal": "text_data"}])

                # 2. KRİTİK DÜZELTME: 'action' VE ŞEMA ENJEKSİYONU
                # Motorun hata verdiği 'action' kelimesini event_type sütununa çakıyoruz.
                REQUIRED_MAP = {
                    'start': 0.0, 'end': 0.0, 'pos_x': 50.0, 'pos_y': 50.0,
                    'code': detected_code,       # Örn: PHASE_OFFENSIVE
                    'event_type': 'action',     # İşte bu satır 'action' hatasını çözer
                    'action': detected_code,    # Bazı motorlar direkt sütun ismi olarak arar
                    'timestamp': 0.0,
                    'team_name': 'Galatasaray' if 'galatasaray' in file_name_lower else 'Atletico'
                }

                for col, val in REQUIRED_MAP.items():
                    if col not in df_raw.columns:
                        df_raw[col] = val

                # 3. ANALİZ
                with st.spinner("Sovereign Intelligence İşleniyor..."):
                    # Veri tiplerini zorla
                    df_raw['start'] = pd.to_numeric(df_raw['start'], errors='coerce').fillna(0.0)
                    
                    analysis = orchestrator.execute_full_analysis(df_raw)
                    verdict = get_agent_verdict(analysis, persona)
                
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Tespit Edilen Faz", detected_code)
                    st.caption(f"Dosya: {file_ext.upper()}")
                with c2:
                    st.warning(f"**Sovereign Verdict:** {verdict}")

            except Exception as e:
                st.error(f"Hata detayı: {e}")
else:
    st.info("Sinyal bekleniyor...")
