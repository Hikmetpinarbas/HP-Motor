import pandas as pd

class HPProcessor:
    """
    HP Lens & Calculation Engine
    Kazanım: 6 Faz + 3 Katman + Zihin Haritası Formülleri (SGA, Prog Score vb.)
    """
    def __init__(self):
        self.version = "1.4.0"

    def apply_lens_and_logic(self, df: pd.DataFrame):
        # --- PHASE 1: 6 Fazlı Segmentasyon (0.0 Korunarak) ---
        df['phase_hp'] = "F3: Build-Up"
        if 'action' in df.columns:
            df.loc[df['action'].str.contains('corner|free', case=False, na=False), 'phase_hp'] = "F6: Set-Pieces"
            df.loc[df['action'].str.contains('tackle|inter', case=False, na=False), 'phase_hp'] = "F1: Org-Defense"

        # --- PHASE 2: Metrik Kombinasyonları (Zihin Haritası LEGO Mantığı) ---
        # 1. Bitiricilik: SGA = PSxG - xG
        if 'psxg' in df.columns and 'xg' in df.columns:
            df['sga_hp'] = df['psxg'] - df['xg']
        
        # 2. Top İlerleme: Prog Score = (Prog*3) + (F3rd*2) + (Box*4)
        # Sütun isimleri platform_mappings'den gelir
        if all(col in df.columns for col in ['prog_passes', 'f3rd_entries', 'box_entries']):
            df['prog_score_hp'] = (df['prog_passes'] * 3) + (df['f3rd_entries'] * 2) + (df['box_entries'] * 4)

        # --- PHASE 3: 3 Katmanlı Etiketleme ---
        df['layer_hp'] = "micro"
        return df
