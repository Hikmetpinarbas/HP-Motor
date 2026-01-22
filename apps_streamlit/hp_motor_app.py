import streamlit as st
from src.engine.persona_v5 import SovereignPersonaManager
from src.engine.table_factory import HPTableFactory
from src.narrative.archetypes import NarrativeArchetypes

# --- V5 INITIALIZATION ---
manager = SovereignPersonaManager()
factory = HPTableFactory()
narrative = NarrativeArchetypes()

# 1. PERSONA SEÇİMİ
selected_persona = st.sidebar.selectbox("🎭 Persona Karar Yüzeyi", list(manager.personas.keys()))
manifest = manager.get_persona_manifest(selected_persona)

# 2. KARAR ÇIKTISI (Pep/Klopp/Rangnick Diliyle)
st.subheader(f"💡 {selected_persona} Karar Paneli")
insight = narrative.apply_style({"phase": "F4"}, manifest['archetype'])
st.info(insight)

# 3. ZORUNLU TABLO VE GRAFİK ÜRETİMİ
col1, col2 = st.columns(2)
with col1:
    st.write(f"📊 {manifest['required_tables'][0]}")
    # factory.create_evidence_table(...) çağrısı buraya bağlanır.
    
with col2:
    st.write(f"📈 {manifest['required_plots'][0]}")
    # plots.py (Tesla Renderer) çağrısı buraya bağlanır.

# 4. HP MOTOR VİCDAN NOTU
st.caption(f"⚠️ Kritik Not: Bu analiz {manifest['focus']} odaklıdır. Yanlış çıkabilir: Epistemik Risk %12.")
