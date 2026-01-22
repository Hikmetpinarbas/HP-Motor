import pandas as pd
import numpy as np

class ValuationEngine:
    """HP Motor v1.0 - Aksiyon Değerleme ve Faz Analiz Motoru"""
    
    def process_match_data(self, df):
        # 0.0 Veri Namusu (Validator)
        df['pos_x'] = pd.to_numeric(df['pos_x'], errors='coerce').fillna(0)
        df['pos_y'] = pd.to_numeric(df['pos_y'], errors='coerce').fillna(0)
        
        # 1. Faz Segmentasyonu (6-Phase Model)
        df['phase'] = df.apply(self._assign_phase, axis=1)
        
        # 2. Metrik Hesaplama (v1.0 Logic)
        # xT (Expected Threat) Proxy
        df['xT'] = (df['pos_x'] / 100) * 0.1 # Basit v1.0 grid model
        
        # SGA (Shot Goals Added) - Eğer gol verisi varsa
        df['sga'] = 0.0
        if 'xg' in df.columns:
             df['sga'] = df.apply(lambda r: 1.0 - r['xg'] if 'Gol' in str(r['action']) else -r['xg'], axis=1)
             
        return df

    def _assign_phase(self, row):
        action = str(row['action']).lower()
        if 'corner' in action or 'set' in action: return 'F6'
        if 'tackle' in action or 'interception' in action: return 'F1'
        if row['pos_x'] > 66: return 'F4'
        if row['pos_x'] < 33: return 'F3'
        return 'F5' # Transition
