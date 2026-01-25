from __future__ import annotations

"""Individual Review – UI destek katmanı

Streamlit arayüzünde, yüklenen CSV'nin hızlı bir kalite/özet kontrolünü sağlar.

Disiplin:
  - Temizleme yapmaz (no silent drops).
  - Tahmin üretmez.
  - Sadece *girdi* tablosu hakkında denetlenebilir özet verir.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import pandas as pd


@dataclass(frozen=True)
class IndividualReviewOutput:
    status: str
    row_count: int
    col_count: int
    columns: list[str]
    null_map: Dict[str, int]
    sample: list[dict]
    notes: list[str]


class IndividualReviewEngine:
    """CSV tablo hızlı kontrol/özet üreticisi."""

    def review_events_table(self, df: pd.DataFrame, sample_n: int = 20) -> Dict[str, Any]:
        notes: list[str] = []

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            out = IndividualReviewOutput(
                status="EMPTY_OR_INVALID",
                row_count=0,
                col_count=0,
                columns=[],
                null_map={},
                sample=[],
                notes=["Yüklenen tablo boş veya geçersiz."],
            )
            return asdict(out)

        # No silent drops: sadece rapor
        row_count = int(len(df))
        col_count = int(len(df.columns))
        columns = [str(c) for c in df.columns.tolist()]
        null_map = df.isna().sum().astype(int).to_dict()

        # Minimal sözleşme ipuçları (zorunlu değil; sadece uyarı)
        expected_any = {"team", "event_type", "type", "timestamp_s", "timestamp", "x", "y"}
        if len(expected_any.intersection(set(columns))) == 0:
            notes.append("Uyarı: Beklenen temel kolonlardan hiçbiri görünmüyor (team/type/timestamp/x/y).")

        # Örnek satırlar
        sample = df.head(sample_n).to_dict(orient="records")

        status = "OK"
        if row_count < 50:
            notes.append("Uyarı: Satır sayısı çok düşük; bazı metrikler anlamlı olmayabilir.")
            status = "DEGRADED"

        out = IndividualReviewOutput(
            status=status,
            row_count=row_count,
            col_count=col_count,
            columns=columns,
            null_map=null_map,
            sample=sample,
            notes=notes,
        )
        return asdict(out)