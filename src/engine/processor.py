from src.engine.formulas import HPLegoLogic

class HPProcessor:
    def __init__(self):
        self.lego = HPLegoLogic()

    def apply_lens_and_logic(self, df):
        # 1. KAZANIM: 6 Fazlı Segmentasyon (Korunuyor)
        df['phase_hp'] = "F3: Build-Up"
        if 'action' in df.columns:
            df.loc[df['action'].str.contains('corner', case=False), 'phase_hp'] = "F6: Set-Pieces"

        # 2. KAZANIM: 3 Katmanlı Lens (Korunuyor)
        df['layer_hp'] = "micro"

        # 3. YENİ KAZANIM: Zihin Haritası Formül Aktivasyonu
        df['sga_hp'] = self.lego.calculate_sga(df)
        df['prog_score_hp'] = self.lego.calculate_prog_score(df)
        df['bdp_hp'] = self.lego.calculate_bdp(df)
        
        return df
