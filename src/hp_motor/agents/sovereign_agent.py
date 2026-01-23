from __future__ import annotations

from typing import Any, Dict


def get_agent_verdict(adapted: Dict[str, Any], persona: str) -> str:
    """
    adapted: app.py içinde adapt_for_agent_verdict() ile dönüştürülen çıktı.
    """
    persona = (persona or "Match Analyst").strip()
    conf = float((adapted or {}).get("confidence", 0.55))
    phase = ((adapted or {}).get("metadata") or {}).get("phase", "ACTION_GENERIC")

    metrics = (adapted or {}).get("metrics", {}) or {}
    ppda = metrics.get("PPDA", 12.0)
    xg = metrics.get("xG", 0.0)

    if persona == "Scout":
        return f"Arketip uyumu için metrik seti eksik olabilir. Faz: {phase}. Güven: %{int(conf*100)}."
    if persona == "Technical Director":
        return f"Yapısal stabilite/riski izlenmeli. PPDA: {ppda:.1f}, xG: {xg:.2f}. Güven: %{int(conf*100)}. Faz: {phase}."
    # Match Analyst default
    return f"Yapısal dominans mevcut. PPDA: {ppda:.1f} ve xG: {xg:.2f} verileriyle taktiksel stabilite %{int(conf*100)}. Faz: {phase}."