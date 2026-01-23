import asyncio

class SovereignAgent:
    """HP Motor v5.0 - Karar Verici Yapay Zeka Katmanı"""
    def __init__(self, api_key="HP_MOTOR_KEY"):
        self.api_key = api_key

    async def generate_tactical_verdict(self, analysis_results, persona):
        verdicts = {
            "Match Analyst": "Yapısal dominans yüksek, ancak F4 fazında karar hızı düşük.",
            "Scout": "Mekansal travma döngüsü tespit edildi, stres altında hata riski var.",
            "Technical Director": "Geçiş oyununda tempo kaybı var, bloklar arası mesafeyi daralt."
        }
        await asyncio.sleep(0.1)
        return verdicts.get(persona, "Analiz mühürlendi.")

def get_agent_verdict(analysis_results, persona):
    agent = SovereignAgent()
    return asyncio.run(agent.generate_tactical_verdict(analysis_results, persona))
