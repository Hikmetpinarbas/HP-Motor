import pandas as pd
import numpy as np

class SOTValidator:
    def __init__(self):
        # Canonical Saha Ölçüleri (Metre)
        self.target_dims = {'x': 105, 'y': 68}

    def validate(self, df):
        report = {"status": "HEALTHY", "issues": [], "coverage": 0.0}
        
        # 1. Koordinat Normalizasyonu (0.0 Değerleri Korunur)
        # Formüller:
        # $x_{std} = x_{raw} \cdot \frac{105}{100}$
        # $y_{std} = y_{raw} \cdot \frac{68}{100}$
        
        df['x_std'] = df['pos_x'] * (self.target_dims['x'] / 100)
        df['y_std'] = df['pos_y'] * (self.target_dims['y'] / 100)

        # 2. Veri Sağlık Denetimi (Explicit Audit)
        valid_rows = df['pos_x'].notnull().sum()
        report["coverage"] = valid_rows / len(df)
        
        if report["coverage"] < 1.0:
            report["status"] = "DEGRADED"
            report["issues"].append(f"Veri Kaybı: %{100 - (report['coverage']*100):.2f} oranında boş koordinat.")

        return report, df
