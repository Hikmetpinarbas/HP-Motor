from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt

try:
    from mplsoccer import Pitch
except Exception:
    Pitch = None  # type: ignore


@dataclass
class RenderContext:
    theme: str
    sample_minutes: Optional[float]
    source: str
    uncertainty: Optional[dict]


class PlotRenderer:
    def __init__(self, theme: str = "clinical"):
        self.theme = theme

    def render(self, spec: Dict[str, Any], raw_df, metric_map: Dict[str, float], ctx: RenderContext):
        t = spec.get("type")
        if t == "scatter":
            return self._scatter(spec, metric_map, ctx)
        if t == "radar":
            return self._radar(spec, metric_map, ctx)
        if t == "pitch_heatmap":
            return self._pitch_heatmap(raw_df, ctx)
        if t == "pitch_overlay":
            return self._pitch_overlay(raw_df, ctx)
        return None

    def _scatter(self, spec: Dict[str, Any], metric_map: Dict[str, float], ctx: RenderContext):
        x_key = spec.get("axes", {}).get("x")
        y_key = spec.get("axes", {}).get("y")
        if not x_key or not y_key:
            return None

        x = metric_map.get(x_key)
        y = metric_map.get(y_key)
        if x is None or y is None:
            return None

        fig = plt.figure()
        plt.scatter([x], [y])
        plt.xlabel(x_key)
        plt.ylabel(y_key)
        title = f"{spec.get('plot_id', 'scatter')} | src={ctx.source}"
        if ctx.sample_minutes is not None:
            title += f" | min={int(ctx.sample_minutes)}"
        plt.title(title)
        return fig

    def _radar(self, spec: Dict[str, Any], metric_map: Dict[str, float], ctx: RenderContext):
        req = spec.get("required_metrics") or []
        if not req:
            return None

        vals = []
        labels = []
        for k in req:
            v = metric_map.get(k)
            if v is None:
                v = 0.0
            vals.append(float(v))
            labels.append(k)

        # Normalize to 0..1 for display (v1 heuristic)
        vmax = max(vals) if vals else 1.0
        if vmax == 0:
            vmax = 1.0
        norm = [v / vmax for v in vals]

        import numpy as np

        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        norm += norm[:1]
        angles += angles[:1]

        fig = plt.figure()
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, norm)
        ax.fill(angles, norm, alpha=0.15)
        ax.set_thetagrids([a * 180 / np.pi for a in angles[:-1]], labels)
        ax.set_title(f"{spec.get('plot_id', 'radar')} | src={ctx.source}")
        return fig

    def _pitch_heatmap(self, df, ctx: RenderContext):
        if Pitch is None:
            return None
        if df is None or df.empty:
            return None
        if "x" not in df.columns or "y" not in df.columns:
            return None

        import pandas as pd

        x = pd.to_numeric(df["x"], errors="coerce")
        y = pd.to_numeric(df["y"], errors="coerce")
        if x.dropna().empty or y.dropna().empty:
            return None

        pitch = Pitch(pitch_type="custom", pitch_length=105, pitch_width=68)
        fig, ax = pitch.draw()
        bs = pitch.bin_statistic(x, y, statistic="count", bins=(12, 8))
        pitch.heatmap(bs, ax=ax, alpha=0.6)
        ax.set_title(f"half_space_touchmap | src={ctx.source}")
        return fig

    def _pitch_overlay(self, df, ctx: RenderContext):
        # v1: simple scatter overlay; later: zone overlays and xT surface
        if Pitch is None:
            return None
        if df is None or df.empty:
            return None
        if "x" not in df.columns or "y" not in df.columns:
            return None

        import pandas as pd

        x = pd.to_numeric(df["x"], errors="coerce")
        y = pd.to_numeric(df["y"], errors="coerce")
        if x.dropna().empty or y.dropna().empty:
            return None

        pitch = Pitch(pitch_type="custom", pitch_length=105, pitch_width=68)
        fig, ax = pitch.draw()
        pitch.scatter(x, y, ax=ax, alpha=0.35, s=15)
        ax.set_title(f"xt_zone_overlay | src={ctx.source}")
        return fig