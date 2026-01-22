class NarrativeArchetypes:
    """HP Motor v5.0 - Stil Arketipleri ve Karar Dili"""
    
    def apply_style(self, data, archetype):
        if archetype == "Pep":
            return f"Yapısal Analiz: {data['phase']} fazında geometrik yerleşim hatası tespit edildi. Neden: Alan parselasyonu eksik."
        
        if archetype == "Klopp":
            return f"Geçiş Analizi: Top kazanımı sonrası enerji arkı (Tesla Arc) %90 verimle F5 fazına aktı."
        
        if archetype == "Rangnick":
            return f"Sistemik Ölçek: Oyuncu profilinin 'Role-Fit' uyumu %94. Pazar değeri ve gelişim eğrisi sürdürülebilir."
            
        return "Analiz hazır. Egemen karar bekleniyor."
