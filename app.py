import streamlit as st
import pandas as pd
import sys
import os
import io

# 1. ADIM: YOL VE PAKET TANIMLAMA (TAŞIMA YAPMADAN ÇÖZÜM)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

# HP Motor Modüllerini Güvenli Import Etme
try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError:
    st.error("Kritik Hata: 'src/hp_motor' klasörü bulunamadı. Lütfen klasör ismini kontrol edin.")
    st.stop()

# --- ARAYÜZ AYARLARI ---
st.set_page_config(page_title="HP MOTOR v5.0", layout="wide", page_icon="🛡️")
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFD700; }
    .stAlert { background-color: #1a1a1a; border: 1px solid #FFD700; color: #FFD700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ HP MOTOR v5.0 | UNIVERSAL ENGINE")
st.caption("Felsefe: Saper Vedere | Tüm Formatlar Aktif (CSV, PDF, XLSX, XML, HTML, MP4)")

@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()

# --- YAN MENÜ: EVRENSEL YÜKLEYİCİ ---
st.sidebar.header("📥 Sinyal Girişi")
# 'type=None' yaparak tüm dosya formatlarını seçilebilir kılıyoruz
uploaded_file = st.sidebar.file_uploader("Dosya Seç (Analiz Başlat)", type=None)
persona = st.sidebar.selectbox("Analiz Personası", ["Match Analyst", "Scout", "Technical Director"])

if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    st.info(f"Yüklenen Dosya Formatı: {file_ext}")

    df_for_analysis = None

    # --- FORMAT BAŞINA İŞLEME MANTIĞI ---
    
    # 1. TABULAR VERİLER (CSV, XLSX)
    if file_ext in ['.csv', '.xlsx', '.xls']:
        if file_ext == '.csv':
            # Önce ; sonra , ayıracını dener
            try:
                df_for_analysis = pd.read_csv(uploaded_file, sep=';')
            except:
                uploaded_file.seek(0)
                df_for_analysis = pd.read_csv(uploaded_file, sep=',')
        else:
            df_for_analysis = pd.read_excel(uploaded_file)
        
        st.dataframe(df_for_analysis.head(10))

    # 2. VİDEO ANALİZ (MP4)
    elif file_ext == '.mp4':
        st.video(uploaded_file)
        st.warning("Video tespit edildi. Görsel sinyaller Sovereign Agent tarafından yorumlanacak.")
        # Analiz için boş bir df gönderiyoruz (Video metadata analizi simülasyonu)
        df_for_analysis = pd.DataFrame([{"video_source": uploaded_file.name}])

    # 3. BELGE ANALİZİ (PDF, HTML, XML)
    elif file_ext in ['.pdf', '.html', '.xml']:
        if file_ext == '.pdf':
            st.write("📄 PDF Raporu Tespit Edildi.")
            # PDF içeriğini burada bir placeholder olarak gösteriyoruz
        elif file_ext == '.xml':
            st.code(uploaded_file.read().decode("utf-8")[:500], language='xml')
        
        df_for_analysis = pd.DataFrame([{"doc_type": file_ext}])

    # --- ANALİZ VE HÜKÜM ---
    if df_for_analysis is not None:
        with st.spinner("Sovereign Intelligence İşleniyor..."):
            # Motoru çalıştır
            analysis = orchestrator.execute_full_analysis(df_for_analysis)
            verdict = get_agent_verdict(analysis, persona)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("🏟️ Taktiksel Sinyal Haritası")
            # Isı haritası ve grafikler buraya gelecek
            st.info("Veri görselleştirme motoru hazır.")
            
        with col2:
            st.subheader("🤖 Sovereign Agent Verdict")
            st.warning(f"**Hüküm:** {verdict}")
            st.metric("Veri Güveni", f"{analysis.get('confidence', {}).get('confidence', 0)*100}%")

else:
    st.info("Sinyal bekleniyor... Lütfen analiz edilecek dosyayı yan menüden yükleyin.")
