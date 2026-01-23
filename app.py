import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# 1. ADIM: YOL TANIMLAMA
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError:
    st.error("Kritik Hata: Modül yolu bulunamadı.")
    st.stop()

# --- ARAYÜZ ---
st.set_page_config(page_title="HP MOTOR v5.0", layout="wide")
st.title("🛡️ HP MOTOR v5.0 | BULK INTELLIGENCE")

@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()

# --- YAN MENÜ ---
uploaded_files = st.sidebar.file_uploader("Dosyaları Yükle", accept_multiple_files=True)
persona = st.sidebar.selectbox("Persona", ["Match Analyst", "Scout", "Technical Director"])

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.expander(f"📄 İşleniyor: {uploaded_file.name}", expanded=True):
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            df_for_analysis = None

            # 1. VERİ OKUMA
            try:
                if file_ext in ['.csv', '.xlsx']:
                    if file_ext == '.csv':
                        try: df_for_analysis = pd.read_csv(uploaded_file, sep=';')
                        except: 
                            uploaded_file.seek(0)
                            df_for_analysis = pd.read_csv(uploaded_file, sep=',')
                    else:
                        df_for_analysis = pd.read_excel(uploaded_file)
                
                # 2. VİDEO VE BELGE İÇİN "HAYALET ŞEMA" OLUŞTURMA (Hata Önleyici)
                else:
                    # Koordinat tabanlı olmayan dosyalar için sahte koordinat sütunları ekliyoruz
                    df_for_analysis = pd.DataFrame({
                        'pos_x': [np.nan], 
                        'pos_y': [np.nan],
                        'event_type': ['non_tabular_signal'],
                        'player_name': ['Generic_Unit'],
                        'timestamp': [0]
                    })
                    if file_ext == '.mp4': st.video(uploaded_file)
                    else: st.write(f"{file_ext} formatında belge algılandı.")

                # 3. MOTOR ANALİZİ (GÜVENLİ MOD)
                if df_for_analysis is not None:
                    # Eksik koordinat sütunları varsa ekle (KeyError önleyici)
                    for col in ['pos_x', 'pos_y']:
                        if col not in df_for_analysis.columns:
                            df_for_analysis[col] = np.nan

                    with st.spinner("Sovereign Intelligence Analiz Ediyor..."):
                        analysis = orchestrator.execute_full_analysis(df_for_analysis)
                        verdict = get_agent_verdict(analysis, persona)
                    
                    st.warning(f"**Sovereign Verdict:** {verdict}")
                    st.info(f"Analiz Modu: {'Sayısal' if file_ext in ['.csv','.xlsx'] else 'Görsel/Metinsel'}")

            except Exception as e:
                st.error(f"Bu dosya işlenirken bir hata oluştu: {e}")
else:
    st.info("Sinyal bekleniyor...")