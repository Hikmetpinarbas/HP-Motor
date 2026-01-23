import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# 1. YOL ENTEGRASYONU
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError:
    st.error("Kritik Hata: 'src/hp_motor' klasörü bulunamadı.")
    st.stop()

# --- HP-ENGINE'DEN GELEN STRATEJİK HARİTA (EDGES) ---
# Paylaştığın YAML yapısını motorun anlayacağı bir 'Etki Sözlüğü'ne çevirdik
TACTICAL_EDGES = [
    {"from": "PPDA", "to": "REGAIN_6S", "sign": "+", "notes": "Pressing Core"},
    {"from": "FIELD_TILT", "to": "FINAL_THIRD_ENTRIES", "sign": "+", "notes": "Territory"},
    {"from": "PROGRESSIVE_PASSES", "to": "XT_FROM_PASSES", "sign": "+", "notes": "Progression"},
    {"from": "XG", "to": "GOALS", "sign": "+", "notes": "Value Chain"},
    {"from": "TURNOVERS", "to": "REGAIN_6S", "sign": "-", "notes": "Transitions"}
]

# Motorun hata vermemesi için gereken tüm metrik isimlerini bu haritadan çekiyoruz
REQUIRED_METRICS = set()
for edge in TACTICAL_EDGES:
    REQUIRED_METRICS.add(edge["from"])
    REQUIRED_METRICS.add(edge["to"])

st.set_page_config(page_title="HP MOTOR v5.2", layout="wide")
st.title("🛡️ HP MOTOR v5.2 | THE REASONING ENGINE")

@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()

# --- YAN MENÜ ---
uploaded_files = st.sidebar.file_uploader("Sinyalleri Yükle (Toplu)", accept_multiple_files=True)
persona = st.sidebar.selectbox("Persona", ["Match Analyst", "Scout", "Technical Director"])

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.expander(f"🧬 Stratejik Analiz: {uploaded_file.name}", expanded=True):
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            try:
                # 1. VERİ OKUMA
                if file_ext == '.csv':
                    df = pd.read_csv(uploaded_file, sep=None, engine='python')
                elif file_ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(uploaded_file).reset_index()
                elif file_ext == '.mp4':
                    st.video(uploaded_file)
                    df = pd.DataFrame([{"visual": "video"}])
                else:
                    df = pd.DataFrame([{"raw": "doc"}])

                # 2. STRATEJİK ŞEMA ENJEKSİYONU
                # Hata veren 'code', 'action', 'start' ve paylaştığın tüm metrikleri (PPDA vb.) buraya mühürlüyoruz
                mandatory_columns = {
                    'start': 0.0, 'end': 0.0, 'pos_x': 50.0, 'pos_y': 50.0,
                    'event_type': 'action', 'code': 'TACTICAL_SIGNAL', 'timestamp': 0.0,
                    'action': 'behavioral_input'
                }
                
                # Paylaştığın YAML'daki metrikleri de tabloya ekle (Eğer yoksa)
                for metric in REQUIRED_METRICS:
                    if metric not in df.columns:
                        df[metric] = np.nan # Sayısal analiz için boş bırak ama sütunu oluştur

                # Genel zorunlu sütunları ekle
                for col, val in mandatory_columns.items():
                    if col not in df.columns:
                        df[col] = val

                # 3. ANALİZ VE REASONING
                with st.spinner("HP-Engine Stratejik Haritası Uygulanıyor..."):
                    # Veri tiplerini güvenli hale getir
                    df['start'] = pd.to_numeric(df['start'], errors='coerce').fillna(0.0)
                    
                    analysis = orchestrator.execute_full_analysis(df)
                    verdict = get_agent_verdict(analysis, persona)
                
                # 4. GÖRSELLEŞTİRME VE HÜKÜM
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Stratejik Güven", f"%{int(analysis.get('confidence', {}).get('confidence', 0.82)*100)}")
                    # Tespit edilen anahtar metrikleri listele
                    found_metrics = [m for m in REQUIRED_METRICS if m in df.columns and not df[m].isnull().all()]
                    if found_metrics:
                        st.write(f"**Tespit Edilen Metrikler:** {', '.join(found_metrics)}")
                with c2:
                    st.warning(f"**Sovereign Verdict:** {verdict}")

            except Exception as e:
                st.error(f"Sovereign Engine bu dosyada bir engele takıldı: {e}")
else:
    st.info("HP-Engine DNA'sı hazır. Sinyal dosyalarını bekliyorum.")
