from __future__ import annotations

from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt


class ReportBuilder:
    """
    Minimal report builder (v0).

    Purpose:
      - Convert analysis outputs into tangible products:
        tables / lists / figures
      - Never invent data; if missing, mark explicitly.

    Outputs:
      {
        "tables": {...},
        "lists": {...},
        "figure_objects": {...}
      }
    """

    def build(
        self,
        df: pd.DataFrame,
        metrics: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        tables: Dict[str, Any] = {}
        lists: Dict[str, Any] = {}
        figures: Dict[str, Any] = {}

        # --- Table 1: Team summary (very minimal, deterministic)
        tables["team_summary"] = self._team_summary(df, metrics)

        # --- Table 2: Player summary (per-player counts)
        tables["player_summary"] = self._player_summary(df)

        # --- Figure 1: Event heatmap (if spatial columns exist)
        fig = self._event_heatmap(df)
        if fig is not None:
            figures["event_heatmap"] = fig

        return {
            "tables": tables,
            "lists": lists,
            "figure_objects": figures,
        }

    def _team_summary(self, df: pd.DataFrame, metrics: Dict[str, Any]) -> pd.DataFrame:
        data = {
            "rows": len(df),
            "unique_players": df["player_id"].nunique() if "player_id" in df.columns else None,
            "ppda": metrics.get("ppda"),
            "xg": metrics.get("xg"),
        }
        return pd.DataFrame([data])

    def _player_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        if "player_id" not in df.columns:
            return pd.DataFrame()

        out = (
            df.groupby("player_id")
            .size()
            .reset_index(name="event_count")
            .sort_values("event_count", ascending=False)
        )
        return out

    def _event_heatmap(self, df: pd.DataFrame):
        if not {"x", "y"}.issubset(df.columns):
            return None

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist2d(df["x"], df["y"], bins=25, cmap="Reds")
        ax.set_title("Event density")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        return fig