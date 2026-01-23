import asyncio

class SovereignAgent:
    """HP Motor v5.0 - Karar Verici Yapay Zeka Katmanı"""
    
    def __init__(self, api_key="HP_MOTOR_SOVEREIGN_KEY"):
        self.api_key = api_key

    async def generate_tactical_verdict(self, analysis_results, persona):
        """Metrikleri Persona diline tercüme eder (Agentic Logic)."""
        
        # Ajanın hüküm kütüphanesi
        verdicts = {
            "Match Analyst": "Yapısal dominans yüksek, ancak F4 fazında karar hızı (Jordet Hızı) düşük seyrediyor.",
            "Scout": "Mekansal travma döngüsü tespit edildi. Oyuncu baskı altında stabilite sorunu yaşayabilir.",
            "Technical Director": "Geçiş oyununda tempo kaybı var. Bloklar arası mesafeyi daraltmak çözüm olabilir."
        }
        
        await asyncio.sleep(0.1) # Simülasyon
        return verdicts.get(persona, "Analiz mühürlendi, egemen karar bekleniyor.")

def get_agent_verdict(analysis_results, persona):
    agent = SovereignAgent()
    return asyncio.run(agent.generate_tactical_verdict(analysis_results, persona))
