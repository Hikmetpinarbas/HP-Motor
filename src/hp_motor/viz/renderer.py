from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Pitch

from hp_motor.viz.theme.theme_caravaggio_tesla import CaravaggioTeslaTheme


@dataclass
class RenderContext:
    theme: CaravaggioTeslaTheme
    # provenance bits for legend
    sample_minutes: Optional[float] = None
    source: str = "unknown"
    uncertainty: Optional[str] = None


class PlotRenderer:
    """
    v1.0 renderer: implements a minimal set of PlotSpec types:
      - scatter
      - pitch_heatmap
      - pitch_overlay (xT-like)
      - radar (fallback: bar proxy if radar not implemented)
    """

    def __init__(self, theme: Optional[CaravaggioTeslaTheme] = None) -> None:
        self.theme = theme or CaravaggioTeslaTheme()
        self.theme.apply_rc()

    def render(self, plot_spec: Dict[str, Any], raw_df: pd.DataFrame, metrics: Dict[str, float], ctx: RenderContext):
        plot_id = plot_spec.get("plot_id")
        plot_type = plot_spec.get("type")

        if plot_type == "scatter":
            return self._scatter(plot_id, plot_spec, metrics, ctx)
        if plot_type == "pitch_heatmap":
            return self._pitch_heatmap(plot_id, plot_spec, raw_df, ctx)
        if plot_type == "pitch_overlay":
            return self._pitch_overlay(plot_id, plot_spec, raw_df, metrics, ctx)
        if plot_type == "radar":
            return self._radar_proxy(plot_id, plot_spec, metrics, ctx)

        raise ValueError(f"Unsupported plot type: {plot_type} (plot_id={plot_id})")

    def _legend_text(self, ctx: RenderContext) -> str:
        parts = []
        if ctx.sample_minutes is not None:
            parts.append(f"Sample: {ctx.sample_minutes:.0f} min")
        parts.append(f"Source: {ctx.source}")
        if ctx.uncertainty:
            parts.append(f"Uncertainty: {ctx.uncertainty}")
        return " | ".join(parts)

    def _scatter(self, plot_id: str, spec: Dict[str, Any], metrics: Dict[str, float], ctx: RenderContext):
        x_id = spec["axes"]["x"]
        y_id = spec["axes"]["y"]
        x = metrics.get(x_id)
        y = metrics.get(y_id)

        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        if x is not None and y is not None:
            ax.scatter([x], [y])
            ax.set_xlabel(x_id)
            ax.set_ylabel(y_id)
        else:
            ax.text(0.5, 0.5, "Missing metrics for scatter", ha="center", va="center")
            ax.set_axis_off()

        self.theme.finalize_plot(
            fig, ax,
            title=f"{plot_id}",
            subtitle=f"{x_id} vs {y_id}",
            legend_text=self._legend_text(ctx),
        )
        return fig

    def _pitch(self) -> Tuple[Pitch, Any, Any]:
        pitch = Pitch(pitch_type="custom", pitch_length=105, pitch_width=68, line_color="#2b2b2b")
        fig, ax = pitch.draw(figsize=(7.2, 4.8))
        return pitch, fig, ax

    def _pitch_heatmap(self, plot_id: str, spec: Dict[str, Any], df: pd.DataFrame, ctx: RenderContext):
        pitch, fig, ax = self._pitch()

        # Expect columns: start_x, start_y (or x,y)
        xcol = "start_x" if "start_x" in df.columns else "x"
        ycol = "start_y" if "start_y" in df.columns else "y"

        if xcol in df.columns and ycol in df.columns and not df.empty:
            # Bin heatmap (Tesla: clean grid, no extra lines)
            bs = pitch.bin_statistic(df[xcol], df[ycol], statistic="count", bins=(12, 8))
            pitch.heatmap(bs, ax=ax, alpha=0.85)
        else:
            ax.text(52.5, 34, "No spatial data", ha="center", va="center")

        self.theme.finalize_plot(
            fig, ax,
            title=f"{plot_id}",
            subtitle="Touch/Receive density (binned)",
            legend_text=self._legend_text(ctx),
        )
        return fig

    def _pitch_overlay(self, plot_id: str, spec: Dict[str, Any], df: pd.DataFrame, metrics: Dict[str, float], ctx: RenderContext):
        pitch, fig, ax = self._pitch()

        xcol = "start_x" if "start_x" in df.columns else "x"
        ycol = "start_y" if "start_y" in df.columns else "y"

        # v1.0: overlay points sized by a single metric (xt_value)
        xt = metrics.get("xt_value")
        if xcol in df.columns and ycol in df.columns and not df.empty and xt is not None:
            # plot a sample of points (keep it clean)
            sdf = df[[xcol, ycol]].dropna().head(500)
            pitch.scatter(sdf[xcol], sdf[ycol], s=20, ax=ax, alpha=0.35)
        else:
            ax.text(52.5, 34, "No overlay data", ha="center", va="center")

        self.theme.finalize_plot(
            fig, ax,
            title=f"{plot_id}",
            subtitle="Spatial overlay (v1.0 minimal)",
            legend_text=self._legend_text(ctx),
        )
        return fig

    def _radar_proxy(self, plot_id: str, spec: Dict[str, Any], metrics: Dict[str, float], ctx: RenderContext):
        # v1.0: radar proxy using horizontal bars (more stable than custom radar libs)
        req = spec.get("required_metrics", [])
        vals = [(m, metrics.get(m)) for m in req]
        vals = [(m, v) for m, v in vals if v is not None]

        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        if not vals:
            ax.text(0.5, 0.5, "Missing metrics for role profile", ha="center", va="center")
            ax.set_axis_off()
        else:
            labels = [m for m, _ in vals]
            data = [v for _, v in vals]
            ax.barh(labels, data)
            ax.invert_yaxis()
            ax.set_xlabel("Value (raw, v1.0)")

        self.theme.finalize_plot(
            fig, ax,
            title=f"{plot_id}",
            subtitle="Role profile (bar proxy for radar)",
            legend_text=self._legend_text(ctx),
        )
        return fig