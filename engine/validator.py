import pandas as pd

class SOTValidator:
    def __init__(self):
        self.dims = {'x': 105, 'y': 68}

    def validate_and_normalize(self, df):
        # 0.0 Koordinatlarını meşru kabul ederek 105x68 düzlemine taşır
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            df['x_std'] = df['pos_x'] * (self.dims['x'] / 100)
            df['y_std'] = df['pos_y'] * (self.dims['y'] / 100)
        
        report = {
            "health": df.notnull().mean().mean(),
            "status": "HEALTHY" if df.notnull().mean().mean() > 0.9 else "DEGRADED"
        }
        return report, df
