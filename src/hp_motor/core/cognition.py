from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class CognitiveSignals:
    decision_speed_mean_s: Optional[float] = None
    scan_freq_10s: Optional[float] = None
    contextual_awareness_score: Optional[float] = None
    note: str = ""


def _safe_mean_numeric(df: pd.DataFrame, col: str) -> Optional[float]:
    if df is None or df.empty or col not in df.columns:
        return None
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.mean())


def extract_cognitive_signals(df: pd.DataFrame) -> CognitiveSignals:
    """
    v1 Cognitive proxy:
      - decision_speed_mean_s:
          Prefer (timestamp_end - timestamp_start)
          Else (t2 - t1)
      - scan_freq_10s: if scan_count_10s exists
      - contextual_awareness_score:
          simple mapping from decision speed + scan frequency (0..1)
    """
    if df is None or df.empty:
        return CognitiveSignals(note="empty_df")

    # decision speed from timestamps
    ds = None
    if "timestamp_start" in df.columns and "timestamp_end" in df.columns:
        ts1 = pd.to_numeric(df["timestamp_start"], errors="coerce")
        ts2 = pd.to_numeric(df["timestamp_end"], errors="coerce")
        delta = (ts2 - ts1).astype("float64")
        if delta.notna().sum() > 0:
            ds = float(delta.mean())
    elif "t1" in df.columns and "t2" in df.columns:
        t1 = pd.to_numeric(df["t1"], errors="coerce")
        t2 = pd.to_numeric(df["t2"], errors="coerce")
        delta = (t2 - t1).astype("float64")
        if delta.notna().sum() > 0:
            ds = float(delta.mean())

    scan = _safe_mean_numeric(df, "scan_freq_10s")
    if scan is None:
        # alternative: scan_count_10s => per second
        c10 = _safe_mean_numeric(df, "scan_count_10s")
        if c10 is not None:
            scan = float(c10) / 10.0

    # awareness score: deterministic, falsifiable
    # - faster decision speed -> higher score
    # - higher scan -> higher score
    score = None
    parts = []

    if ds is not None:
        # Elite <0.8, Average <1.2, clamp
        if ds <= 0.6:
            ds_score = 0.90
        elif ds <= 0.8:
            ds_score = 0.75
        elif ds <= 1.2:
            ds_score = 0.55
        else:
            ds_score = 0.35
        parts.append(f"ds={ds:.3f}->{ds_score:.2f}")
    else:
        ds_score = None

    if scan is not None:
        if scan >= 0.8:
            sc_score = 0.90
        elif scan >= 0.4:
            sc_score = 0.60
        else:
            sc_score = 0.35
        parts.append(f"scan={scan:.3f}->{sc_score:.2f}")
    else:
        sc_score = None

    if ds_score is not None and sc_score is not None:
        score = float((0.55 * sc_score) + (0.45 * ds_score))
    elif sc_score is not None:
        score = float(sc_score)
    elif ds_score is not None:
        score = float(ds_score)

    note = " | ".join(parts) if parts else "no_cognitive_columns"
    return CognitiveSignals(
        decision_speed_mean_s=ds,
        scan_freq_10s=scan,
        contextual_awareness_score=score,
        note=note,
    )


@dataclass
class OrientationSignals:
    defender_side_on_score: Optional[float] = None
    square_on_rate: Optional[float] = None
    channeling_to_wing_rate: Optional[float] = None
    note: str = ""


def extract_orientation_signals(df: pd.DataFrame) -> OrientationSignals:
    """
    v1 orientation:
      - if already provided as columns, read means
      - otherwise None (video/tracking needed)
    """
    if df is None or df.empty:
        return OrientationSignals(note="empty_df")

    side_on = _safe_mean_numeric(df, "defender_side_on_score")
    square = _safe_mean_numeric(df, "square_on_rate")
    channel = _safe_mean_numeric(df, "channeling_to_wing_rate")

    note = "orientation_from_columns" if any(v is not None for v in [side_on, square, channel]) else "no_orientation_columns"
    return OrientationSignals(
        defender_side_on_score=side_on,
        square_on_rate=square,
        channeling_to_wing_rate=channel,
        note=note,
    )