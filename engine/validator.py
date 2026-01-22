import pandas as pd
import json

class SOTValidator:
    def __init__(self, ontology_path="canon/metric_ontology.json"):
        with open(ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
        self.dims = {'x': 105, 'y': 68}

    def clean_and_normalize(self, df):
        # 0.0 değerlerini silmeden canonical koordinatlara taşıma
        if 'pos_x' in df.columns and 'pos_y' in df.columns:
            df['x_std'] = df['pos_x'] * (self.dims['x'] / 100)
            df['y_std'] = df['pos_y'] * (self.dims['y'] / 100)
        
        # Boş veri raporu
        report = {
            "total_rows": len(df),
            "health_score": df.notnull().mean().mean(),
            "status": "HEALTHY" if df.notnull().mean().mean() > 0.9 else "DEGRADED"
        }
        return report, df
