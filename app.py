import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# 1. MİMARİ BAĞLANTI (Path Integration)
# Proje yapısını ve src klasörünü sisteme tanıtıyoruz
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError:
    st.error("Kritik Hata: 'src/hp_motor' yolu bulunamadı. Lütfen klasör yapısını kontrol edin.")
    st.stop()

# --- 2. STRATEJİK ZEKA KATMANI (HP-Engine DNA) ---
# Paylaştığın Causal Graph (Edges) ve Tag mantığını buraya mühürledik
TACTICAL_EDGES = [
    {"from": "PPDA", "to": "REGAIN_6S", "sign": "+", "note": "Pressing Core"},
    {"from": "FIELD_TILT", "to": "FINAL_THIRD_ENTRIES", "sign": "+", "note": "Territory"},
    {"from": "PROGRESSIVE_PASSES", "to": "XT_FROM_PASSES", "sign": "+", "note": "Progression"},
    {"from": "XG", "to": "GOALS", "sign": "+", "note": "Value Chain"},
    {"from": "TURNOVERS", "to": "REGAIN_6S", "sign": "-", "note": "Transitions"}
]

SEMANTIC_TAGS = {
    "PHASE_OFFENSIVE": ["pozisyon", "hucum", "hücum", "attack", "offensive", "possession"],
    "PHASE_DEFENSIVE": ["savunma", "defans", "defensive", "baski", "baskı", "press"],
    "PHASE_TRANSITION": ["gecis", "geçiş", "counter", "transition", "fast break"]
}

# 3. ARAYÜZ AYARLARI
st.set_page_config(page_title="HP MOTOR v5.2", layout="wide", page_icon="🛡️")
st.markdown("<style>.main { background-color: #0d1117; color: #e6edf3; }</style>", unsafe_allow_html=True)

st.title("🛡️ HP MOTOR v5.2 | THE REASONING ENGINE")
st.caption("Felsefe: Saper Vedere | Causal Reasoning & Semantic Intelligence Aktif")

@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()

# --- 4. TOPLU SİNYAL GİRİŞİ ---
st.sidebar.header("📥 Sinyal Girişi")
uploaded_files = st.sidebar.file_uploader("Dosyaları Buraya Bırakın", accept_multiple_files=True)
persona = st.sidebar.selectbox("Analiz Personası", ["Match Analyst", "Scout", "Technical Director"])

if uploaded_files:
    st.info(f"Sistem yayında: {len(uploaded_files)} dosya işleniyor.")
    
    for uploaded_file in uploaded_files:
        file_name_lower = uploaded_file.name.lower()
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        with st.expander(f"⚙️ Stratejik Analiz: {uploaded_file.name}", expanded=True):
            try:
                # --- VERİ OKUMA ---
                if file_ext == '.csv':
                    df = pd.read_csv(uploaded_file, sep=None, engine='python')
                elif file_ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(uploaded_file).reset_index()
                elif file_ext == '.mp4':
                    st.video(uploaded_file)
                    df = pd.DataFrame([{"visual": "video_stream"}])
                else:
                    df = pd.DataFrame([{"raw": "document_data"}])

                # --- 5. SOVEREIGN NORMALİZASYON (Hata Önleyici) ---
                # Dosya isminden semantik fazı belirle
                detected_code = "ACTION_GENERIC"
                for phase, keywords in SEMANTIC_TAGS.items():
                    if any(k in file_name_lower for k in keywords):
                        detected_code = phase
                        break

                # Tüm zorunlu sütunları ve senin Edges metriklerini enjekte et
                REQUIRED_MAP = {
                    'start': 0.0, 'end': 0.0, 'pos_x': 50.0, 'pos_y': 50.0,
                    'code': detected_code, 'event_type': 'action', 'action': 'behavioral',
                    'timestamp': 0.0, 'team_name': 'Galatasaray' if 'galatasaray' in file_name_lower else 'Atletico'
                }
                
                # Metrikleri sütun olarak ekle (Causal Reasoning için)
                for edge in TACTICAL_EDGES:
                    for col in [edge['from'], edge['to']]:
                        if col not in df.columns:
                            df[col] = np.nan

                # Zorunlu alanları ekle
                for col, val in REQUIRED_MAP.items():
                    if col not in df.columns:
                        df[col] = val

                # Tip güvenliği
                df['start'] = pd.to_numeric(df['start'], errors='coerce').fillna(0.0)

                # --- 6. ANALİZ VE REASONING ---
                with st.spinner("Sovereign Intelligence Akıl Yürütüyor..."):
                    analysis = orchestrator.execute_full_analysis(df)
                    verdict = get_agent_verdict(analysis, persona)
                
                # --- 7. SONUÇ EKRANI ---
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Veri Sağlığı", f"%{int(analysis.get('confidence', {}).get('confidence', 0.82)*100)}")
                    st.caption(f"Semantik Faz: {detected_code}")
                    # Metrik tespiti
                    found_metrics = [m for m in df.columns if m in [e['from'] for e in TACTICAL_EDGES] and not df[m].isnull().all()]
                    if found_metrics:
                        st.write("**Aktif Metrikler:**")
                        for m in found_metrics: st.success(m)
                
                with c2:
                    st.warning(f"**Sovereign Verdict:** {verdict}")
                    if "F4" in verdict:
                        st.info("💡 Not: F4 fazı tespit edildi. Bitiricilik zinciri (xG Chain) aktif.")

            except Exception as e:
                st.error(f"Sistem bu dosyada bir engele takıldı: {e}")
else:
    st.info("HP-Engine DNA'sı ve Karar Mekanizması hazır. Lütfen dosyalarınızı yükleyin.")
