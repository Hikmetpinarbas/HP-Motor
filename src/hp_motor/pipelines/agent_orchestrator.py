from src.hp_motor.pipelines.run_analysis import SovereignOrchestrator

class HPAgenticEngine:
    """HP Motor v5.0 - Copilot SDK Destekli Karar Katmanı"""
    
    def __init__(self):
        self.orchestrator = SovereignOrchestrator()

    def ask_hp_motor(self, raw_data, question):
        # Bu kısım ileride Copilot SDK ile 'doğal dil' işleyecek
        # Şimdilik sistemin muhakeme motorunu çalıştırıyor
        analysis_results = self.orchestrator.execute_full_analysis(raw_data)
        
        # Karar matrisini oluştur
        return {
            "analysis": analysis_results,
            "agent_note": f"Analiz tamamlandı. {question} sorusu için veriler hazır."
        }
