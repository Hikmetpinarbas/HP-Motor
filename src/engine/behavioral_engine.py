import pandas as pd

class BehavioralEngine:
    """
    Sovereign Behavioral Layer (Sapolsky & Mate Influence)
    Görevi: Verideki 'Tekrar Zorlantılarını' ve Stres Kırılmalarını saptamak.
    """
    def __init__(self):
        self.stress_threshold = 0.75 # Karar mekanizmasının (PFC) çöküş sınırı

    def analyze_trauma_loops(self, df):
        # Aynı bölgede üst üste yapılan 3 hatalı pas = Tekrar Zorlantısı
        df['is_loop'] = (df['action'].str.contains('Inaccurate', na=False)) & \
                        (df['action'].shift(1).str.contains('Inaccurate', na=False))
        return df

    def calculate_emotional_load(self, df):
        # Maçın son 15 dakikasında ve 1 farkla gerideyken hata payı 'Stres Yükü'dür.
        # Voltaj dalgalanması olarak UI'a yansıyacak.
        df['stress_load'] = 0.0
        # Basit bir simülasyon: Maç sonu + Kritik anlar
        df.loc[df['start'] > 4500, 'stress_load'] += 0.4
        return df
