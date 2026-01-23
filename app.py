# -*- coding: utf-8 -*-
import os
import sys
from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1) Path bootstrap: root/app.py -> ./src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from hp_motor.engine.hp_engine_v12 import HPEngineV12


st.set_page_config(page_title="HP Engine v22.5", layout="wide", page_icon="🛡️")

st.markdown(
    """
<style>
.main { background-color: #0a0a0a; color: #00ff41; }
h1, h2, h3 { color: #ffffff !important; font-family: 'Courier New', Courier, monospace; }
</style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR: SYSTEM CONTROL ---
st.sidebar.title("HP ENGINE v22.5")
st.sidebar.info("Deterministik Futbol Analiz Modülü")

mode = st.sidebar.selectbox(
    "Analiz Modu",
    ["Pre-Match DNA", "Mezzo-Phase Flow", "Micro-BioMech Autopsy", "Event Stream (H-Rejim)"],
)

uploaded = st.sidebar.file_uploader("CSV yükle (event stream)", type=["csv"], accept_multiple_files=False)

st.title("HP Engine | Stratejik Otopsi")
st.caption("Rastlantısallık yoktur; yalnızca yetersiz veri vardır.")

engine = HPEngineV12()


def _read_csv(uploaded_file) -> pd.DataFrame:
    b = uploaded_file.getvalue()
    df = pd.read_csv(BytesIO(b), sep=None, engine="python")
    return df


def _infer_event_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    En azından event_type kolonu yoksa basit infer denemesi.
    """
    if "event_type" not in df.columns:
        # common aliases
        for c in ["type", "event", "action", "eventName"]:
            if c in df.columns:
                df = df.rename(columns={c: "event_type"})
                break
    return df


def run_engine_on_df(df: pd.DataFrame) -> pd.DataFrame:
    df = _infer_event_columns(df)
    if "event_type" not in df.columns:
        st.error("CSV içinde 'event_type' kolonu bulunamadı. En azından event_type gerekli.")
        st.write("Kolonlar:", list(df.columns))
        st.stop()

    rows = []
    for _, r in df.iterrows():
        event = r.to_dict()
        out = engine.process_match_event(event)
        d = engine.format_output(out)
        rows.append(
            {
                "event_type": event.get("event_type"),
                "player_id": event.get("player_id", None),
                "role": event.get("role", event.get("player_role", None)),
                "h_score": d["h_score"],
                "regime": d["regime"],
                "uncertainty": d["uncertainty"],
                "bio_status": d["bio_risk"].get("status"),
                "bio_alignment": d["bio_risk"].get("alignment"),
                "flags": ", ".join(d["protocols"]["summary"].get("flags", [])),
            }
        )
    return pd.DataFrame(rows)


# --- UI MODES ---
if mode == "Pre-Match DNA":
    st.header("1) Stratejik DNA Matrisi (v1 placeholder)")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("FB DNA: 0.72")
        st.progress(0.72)
        st.write("- Fiziksel Dominans: Yüksek\n- Taktik Yerleşim: Kararlı")
    with c2:
        st.subheader("GS DNA: 0.70")
        st.progress(0.70)
        st.write("- Hava Hakimiyeti: Düşük\n- Statik Hücum Riski: Kritik")

elif mode == "Mezzo-Phase Flow":
    st.header("2) 6 Fazlı Momentum Akışı (basit görselleştirme)")
    # placeholder: 6 faz için random momentum
    phases = ["Kurulum", "Karşılama", "Geçiş(H->A)", "Geçiş(A->H)", "Set", "Final"]
    vals = np.clip(np.random.normal(0.5, 0.15, size=6), 0, 1)

    fig = plt.figure()
    plt.plot(phases, vals, marker="o")
    plt.xticks(rotation=25, ha="right")
    plt.ylim(0, 1)
    plt.title("Phase Flow (v1)")
    st.pyplot(fig, clear_figure=True)

    st.success("Not: Bu grafik v1 placeholder; gerçek fazlar event-tagging ile bağlanacak.")

elif mode == "Micro-BioMech Autopsy":
    st.header("3) Biyomekanik Veri İspatı (Somatotype SRU Gate)")
    st.info("Bu mod, CSV yoksa bile prensip tablosu gösterir; CSV varsa bio alignment hesaplar.")

    if uploaded is None:
        metrics = {
            "Parametre": ["Scanning Rate", "Reaction Time", "Side-on Angle"],
            "Value": ["0.8/s", "0.52s", "45°"],
            "Status": ["Elite", "Critical", "Stable"],
        }
        st.table(pd.DataFrame(metrics))
    else:
        df = _read_csv(uploaded)
        df = _infer_event_columns(df)
        # event stream bio audit results
        out = run_engine_on_df(df)
        st.subheader("Somatotype / Role Alignment")
        st.dataframe(out[["player_id", "role", "bio_status", "bio_alignment"]].dropna(how="all"), use_container_width=True)

        alarms = out[out["bio_status"] == "ALARM"]
        if len(alarms) > 0:
            st.warning(f"ALARM sayısı: {len(alarms)} (Somatotip-Rol uyuşmazlığı)")
        else:
            st.success("Somatotype SRU Gate: Stabil (ALARM yok)")

elif mode == "Event Stream (H-Rejim)":
    st.header("4) Event Stream (H-Rejimi + Protokol Bayrakları)")

    if uploaded is None:
        st.warning("Bu mod için CSV yüklemelisin. Minimum kolon: event_type.")
        st.stop()

    df = _read_csv(uploaded)
    st.write("CSV Önizleme", df.head(10))

    out = run_engine_on_df(df)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Son H-Score", f"{out['h_score'].iloc[-1]:.2f}")
    with c2:
        st.metric("Son Rejim", f"{out['regime'].iloc[-1]}")
    with c3:
        st.metric("Epistemik Belirsizlik", f"{out['uncertainty'].iloc[-1]:.2f}")

    st.subheader("H-Score Zaman Çizgisi")
    fig = plt.figure()
    plt.plot(out["h_score"].values)
    plt.ylim(0, 1)
    plt.title("H-Score (0=CONTROL, 1=CHAOS)")
    st.pyplot(fig, clear_figure=True)

    st.subheader("Protokol Bayrakları")
    st.dataframe(out.tail(50), use_container_width=True)

else:
    st.info("Mod seç.")