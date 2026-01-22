import pandas as pd

class HPProcessor:
    def __init__(self):
        self.version = "1.3.1"

    def apply_lens(self, df: pd.DataFrame):
        # 1. KAZANIM: 6 Fazlı Segmentasyon (Eskisi korunuyor)
        df['phase_hp'] = "F3: Build-Up"
        if 'action' in df.columns:
            df.loc[df['action'].str.contains('corner', case=False), 'phase_hp'] = "F6: Set-Pieces"
            df.loc[df['action'].str.contains('tackle', case=False), 'phase_hp'] = "F1: Org-Defense"

        # 2. YENİ KAZANIM: Zihin Haritası Formülleri (LEGO Mantığı)
        # PSxG ve xG varsa SGA'yı otomatik hesapla
        if 'psxg' in df.columns and 'xg' in df.columns:
            df['sga_hp'] = df['psxg'] - df['xg'] # SGA: Bitiricilik Yeteneği

        # 3. KAZANIM: 3 Katmanlı Lens (Micro-Mezzo-Macro)
        df['layer_hp'] = "micro"
        return df
