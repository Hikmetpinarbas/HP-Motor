import streamlit as st
import pandas as pd
# Yollar sadeleşti: Direkt hp_motor üzerinden
from hp_motor.pipelines.run_analysis import SovereignOrchestrator
from hp_motor.viz.table_factory import HPTableFactory
from hp_motor.viz.plot_factory import HPPlotFactory
from hp_motor.core.cdl_models import EvidenceNode
from hp_motor.agents.sovereign_agent import get_agent_verdict

st.set_page_config(page_title="HP MOTOR v5.0", layout="wide")
st.markdown("<style>.main { background-color: #000000; color: #FFD700; }</style>", unsafe_allow_html=True)

st.title("🛡️ HP MOTOR v5.0")
st.caption("Felsefe: Saper Vedere | Güç: GitHub Copilot SDK")

orchestrator = SovereignOrchestrator()
table_factory = HPTableFactory()
plot_factory = HPPlotFactory()

uploaded_file = st.sidebar.file_uploader("Sinyal (CSV) Yükle", type=['csv'])
persona = st.sidebar.selectbox("Persona", ["Match Analyst", "Scout", "Technical Director"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';')
    with st.spinner("Analiz ediliyor..."):
        analysis = orchestrator.execute_full_analysis(df)
        verdict = get_agent_verdict(analysis, persona)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.pyplot(plot_factory.plot_trauma_zones(analysis['trauma_loops']))
        st.table(table_factory.create_evidence_table([])) # Tabloyu buraya bağla
    with col2:
        st.warning(f"**Hüküm:** {verdict}")
