import asyncio

class SovereignAgent:
    def __init__(self, api_key="HP_MOTOR_KEY"):
        self.api_key = api_key

    async def generate_tactical_verdict(self, analysis_results, persona):
        verdicts = {
            "Match Analyst": "Yapısal dominans yüksek, F4 fazında hız düşük.",
            "Scout": "Mekansal travma döngüsü tespit edildi, risk var.",
            "Technical Director": "Geçiş oyununda tempo kaybı var, blokları daralt."
        }
        await asyncio.sleep(0.1)
        return verdicts.get(persona, "Analiz mühürlendi.")

def get_agent_verdict(analysis_results, persona):
    agent = SovereignAgent()
    return asyncio.run(agent.generate_tactical_verdict(analysis_results, persona))
