class HPProcessor:
    def __init__(self):
        self.phases = ["F1: Savunma", "F2: Sav->Hüc", "F3: Build-Up", 
                       "F4: Hücum", "F5: Hüc->Sav", "F6: Set-Pieces"]

    def process(self, df):
        # 6 Fazlı Lens ve 3 Katmanlı etiketleme
        df['phase_hp'] = "F3: Build-Up" # Varsayılan başlangıç
        df['layer_hp'] = "micro"       # Varsayılan bireysel
        
        if 'action' in df.columns:
            df.loc[df['action'].str.contains('corner|free', na=False), 'phase_hp'] = "F6: Set-Pieces"
            df.loc[df['action'].str.contains('tackle|inter', na=False), 'phase_hp'] = "F1: Savunma"
            
        return df
