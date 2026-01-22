import pandas as pd
import numpy as np

class ValuationEngine:
    """HP Motor v1.0 - Aksiyon Değerleme ve Metrik Hesaplama Motoru"""
    
    def calculate_sga(self, goals, xg):
        """Shot Goals Added (SGA) = Goals - xG"""
        return goals - xg

    def process_actions(self, df):
        """Her aksiyonun (SPADL-like) değerini hesaplar"""
        # xT (Expected Threat) Basitleştirilmiş Grid Model (v1.0)
        # 10x10 grid üzerinden ilerleme değerini hesaplar
        df['grid_x'] = (df['pos_x'] // 10).astype(int)
        df['grid_y'] = (df['pos_y'] // 10).astype(int)
        
        # Grid bazlı değer artışı (Hücum yönüne doğru artan değer)
        df['xt_value'] = df['grid_x'] * 0.01 
        return df

    def get_phase(self, row):
        """HP 6-Phase Model (v1.0) Entegrasyonu"""
        action = str(row['action']).lower()
        if 'corner' in action or 'free kick' in action: return 'F6: Set-Pieces'
        if 'tackle' in action or 'interception' in action: return 'F1: Org. Defense'
        if row['pos_x'] > 66: return 'F4: Incision'
        return 'F3: Org. Attack'
