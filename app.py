import streamlit as st
import pandas as pd
import numpy as np
import sys
import os


# ----------------------------
# 0) Path bootstrap (root/app.py -> ./src)
# ----------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from hp_motor.pipelines.run_analysis import SovereignOrchestrator
    from hp_motor.agents.sovereign_agent import get_agent_verdict
except ImportError as e:
    st.error(f"Kritik Hata: 'src' klasörü altındaki modüller okunamıyor. Hata: {e}")
    st.stop()


# ----------------------------
# 1) UI config
# ----------------------------
st.set_page_config(page_title="HP MOTOR v6.0", layout="wide", page_icon="🛡️")
st.title("🛡️ HP MOTOR v6.0 | ARCHITECT")


# ----------------------------
# 2) Orchestrator cache
# ----------------------------
@st.cache_resource
def load_orchestrator():
    return SovereignOrchestrator()

orchestrator = load_orchestrator()


# ----------------------------
# 3) Helpers
# ----------------------------
def detect_phase(filename: str) -> str:
    fname = (filename or "").lower()
    if any(k in fname for k in ["pozisyon", "hucum", "hücum", "attack", "offensive"]):
        return "PHASE_OFFENSIVE"
    if any(k in fname for k in ["savunma", "defans", "defensive", "block"]):
        return "PHASE_DEFENSIVE"
    if any(k in fname for k in ["gecis", "geçiş", "transition", "counter"]):
        return "PHASE_TRANSITION"
    return "ACTION_GENERIC"


def canonicalize_xy_inplace(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input bazen 0-100 ölçeğinde (platform), bazen 105x68 (canonical).
    Bu fonksiyon:
      - x,y varsa ve 0..100 bandındaysa 105x68'e çevirip x,y'yi canonical yapar.
      - x_m, y_m üretmek yerine renderer için x,y'yi garanti etmeye çalışır.
    """
    if df is None or df.empty:
        return df

    if "x" in df.columns and "y" in df.columns:
        try:
            x = pd.to_numeric(df["x"], errors="coerce")
            y = pd.to_numeric(df["y"], errors="coerce")
            # Heuristic: 0..100 scale
            if x.notna().any() and y.notna().any():
                xmax = float(np.nanmax(x.values))
                ymax = float(np.nanmax(y.values))
                xmin = float(np.nanmin(x.values))
                ymin = float(np.nanmin(y.values))

                if xmin >= 0 and ymin >= 0 and xmax <= 100.5 and ymax <= 100.5:
                    df["x"] = (x / 100.0) * 105.0
                    df["y"] = (y / 100.0) * 68.0
        except Exception:
            pass

    return df


def confidence_from_evidence(out: dict) -> float:
    """
    orchestrator -> evidence_graph.overall_confidence: low/medium/high
    """
    eg = (out or {}).get("evidence_graph") or {}
    level = eg.get("overall_confidence", "medium")
    mapping = {"low": 0.35, "medium": 0.65, "high": 0.85}
    return float(mapping.get(str(level).lower(), 0.55))


def adapt_for_agent_verdict(out: dict, phase: str) -> dict:
    """
    sovereign_agent.py eski şema bekliyor:
      analysis['metrics'] dict, analysis['metadata']['phase'], analysis['confidence']
    Biz orchestrator outputunu buna çeviriyoruz.
    """
    metrics_list = out.get("metrics", []) or []
    # metrics_list: [{metric_id, value, ...}, ...]
    m = {}
    for row in metrics_list:
        mid = row.get("metric_id")
        val = row.get("value")
        if mid is None:
            continue
        m[mid] = val

    # Agent'in beklediği anahtarlar
    # PPDA ve xG (xG yoksa 0.0 veriyoruz)
    legacy_metrics = {
        "PPDA": float(m.get("ppda", 12.0)) if m.get("ppda") is not None else 12.0,
        "xG": 0.0,  # v1.0: yok, sonra metric factory ile gelir
    }

    return {
        "metrics": legacy_metrics,
        "metadata": {"phase": phase},
        "confidence": confidence_from_evidence(out),
    }


def pick_entity_id(df: pd.DataFrame) -> str:
    """
    execute(...) entity_id istiyor.
    - player_id varsa UI’dan seçtireceğiz.
    - yoksa 'entity' fallback.
    """
    if df is None or df.empty:
        return "entity"

    if "player_id" in df.columns:
        uniq = [x for x in df["player_id"].dropna().unique().tolist()]
        if len(uniq) == 1:
            return str(uniq[0])
    return "entity"


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext == ".csv":
        return pd.read_csv(uploaded_file, sep=None, engine="python")
    if file_ext in [".xlsx", ".xls"]:
        return pd.read_excel(uploaded_file).reset_index(drop=True)
    # mp4 vb. için df yerine placeholder döndür
    return pd.DataFrame()


# ----------------------------
# 4) Sidebar
# ----------------------------
st.sidebar.header("📥 Veri Girişi")
uploaded_files = st.sidebar.file_uploader(
    "Sinyalleri Bırakın (CSV, MP4, XLSX)",
    accept_multiple_files=True,
    type=["csv", "mp4", "xlsx", "xls"]
)

persona = st.sidebar.selectbox("Analiz Personası", ["Match Analyst", "Scout", "Technical Director"])
role = st.sidebar.text_input("Rol (player_role_fit)", value="Mezzala")

# Analysis object şu an orchestrator.execute(...) ile çalışıyor
analysis_object_id = st.sidebar.selectbox(
    "Analysis Object",
    ["player_role_fit"],
    index=0
)

# Görsel çıktılar opsiyonel
show_figures = st.sidebar.checkbox("Grafikleri Göster", value=True)
show_tables = st.sidebar.checkbox("Tabloları Göster", value=True)
show_lists = st.sidebar.checkbox("Listeleri Göster", value=True)


# ----------------------------
# 5) Main flow
# ----------------------------
if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.expander(f"⚙️ Analiz: {uploaded_file.name}", expanded=True):
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            phase = detect_phase(uploaded_file.name)

            try:
                # MP4: sadece göster
                if file_ext == ".mp4":
                    st.video(uploaded_file)
                    st.info(f"Faz: {phase} | Video sinyali alındı. (v1.0: video analizi pipeline'a bağlı değil)")
                    continue

                # Data read
                df = read_uploaded_file(uploaded_file)
                if df is None or df.empty:
                    st.warning("Dosya okundu ama tablo boş görünüyor.")
                    continue

                # Canonicalize coords
                df = canonicalize_xy_inplace(df)

                # Entity id
                entity_id = pick_entity_id(df)
                if "player_id" in df.columns:
                    candidates = [str(x) for x in df["player_id"].dropna().unique().tolist()]
                    if candidates:
                        entity_id = st.selectbox("player_id", candidates, index=0)

                # Run engine
                with st.spinner("Sovereign Intelligence işleniyor..."):
                    out = orchestrator.execute(
                        analysis_object_id=analysis_object_id,
                        raw_df=df,
                        entity_id=str(entity_id),
                        role=role,
                        phase=phase,
                    )

                # Status + verdict
                if out.get("status") != "OK":
                    st.error("Analiz UNKNOWN/FAIL döndü.")
                    st.write(out)
                    continue

                adapted = adapt_for_agent_verdict(out, phase)
                verdict = get_agent_verdict(adapted, persona)

                c1, c2, c3 = st.columns([1, 1, 3])
                with c1:
                    conf = confidence_from_evidence(out)
                    st.metric("Güven", f"%{int(conf*100)}")
                with c2:
                    st.info(f"Faz: {phase}")
                    miss = out.get("missing_metrics", [])
                    if miss:
                        st.warning(f"Missing: {', '.join(miss[:6])}" + ("..." if len(miss) > 6 else ""))
                with c3:
                    st.warning(f"**Sovereign Verdict:** {verdict}")

                # Tables
                if show_tables:
                    st.subheader("📋 Tables")
                    tables = out.get("tables", {}) or {}
                    if not tables:
                        st.info("Tablo üretilmedi.")
                    else:
                        for tname, rows in tables.items():
                            st.markdown(f"### {tname}")
                            st.dataframe(pd.DataFrame(rows), use_container_width=True)

                # Lists
                if show_lists:
                    st.subheader("🧾 Lists")
                    lists = out.get("lists", {}) or {}
                    if not lists:
                        st.info("Liste üretilmedi.")
                    else:
                        for lname, items in lists.items():
                            st.markdown(f"### {lname}")
                            st.write(items)

                # Figures (matplotlib)
                if show_figures:
                    st.subheader("📈 Figures")
                    fig_objs = out.get("figure_objects", {}) or {}
                    if not fig_objs:
                        st.info("Grafik üretilmedi.")
                    else:
                        for pid, fig in fig_objs.items():
                            st.markdown(f"### {pid}")
                            st.pyplot(fig, clear_figure=False)

            except Exception as e:
                st.error(f"Dosya analiz edilemedi: {e}")

else:
    st.info("Sinyal bekleniyor... Saper Vedere.")