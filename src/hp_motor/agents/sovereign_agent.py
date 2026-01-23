from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool
import asyncio

# --- AJANIN KULLANDIĞI ARAÇLAR ---
class TacticalParams(BaseModel):
    summary: str = Field(description="Futbol analitik verilerinin özeti")

@define_tool(description="Verilen metrikleri taktiksel bir hükme dönüştürür")
async def generate_verdict(params: TacticalParams) -> str:
    # Burada veriyi yorumlayan temel mantık çalışır
    return f"Analiz tamamlandı. Veriler doğrultusunda: {params.summary[:100]}... odaklı bir strateji öneriliyor."

class SovereignAgent:
    """HP Motor v5.0 - Copilot SDK Destekli Egemen Zeka"""
    
    def __init__(self, api_key="HP_MOTOR_SOVEREIGN_KEY"):
        # 2026 SDK Standartlarına göre başlatma
        self.client = CopilotClient(api_key=api_key)

    async def analyze_with_agent(self, analysis_results, persona):
        """Metrikleri Ajan üzerinden yorumlar (Multi-turn Conversation)"""
        
        summary = f"Persona: {persona}. Epistemik Güven: {analysis_results['confidence']['confidence']}. " \
                  f"Travma Döngüsü: {len(analysis_results['trauma_loops'])}. " \
                  f"Bilişsel Hız: {analysis_results['cognitive_speed'].mean() if not analysis_results['cognitive_speed'].empty else 'N/A'}"
        
        # Copilot SDK ile oturum başlatma
        session = await self.client.create_session({
            "model": "gpt-5-2-codex", # 2026'nın en güncel modeli
            "tools": [generate_verdict]
        })
        
        prompt = f"Sen bir {persona} uzmanısın. Şu verileri klinik bir dille yorumla: {summary}"
        response = await session.ask(prompt)
        
        return response.content if response else "Ajan şu an muhakeme edemiyor."

# Streamlit için async wrapper
def get_agent_verdict(analysis_results, persona):
    agent = SovereignAgent()
    return asyncio.run(agent.analyze_with_agent(analysis_results, persona))
