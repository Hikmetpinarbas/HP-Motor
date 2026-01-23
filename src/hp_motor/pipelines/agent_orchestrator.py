from hp_motor.pipelines.run_analysis import SovereignOrchestrator

class HPAgenticEngine:
    """HP Motor - Agentic dispatcher (v1.0: tool/dispatcher seviyesinde)"""

    def __init__(self):
        self.orchestrator = SovereignOrchestrator()

    def ask_hp_motor(self, raw_data, question, phase="ACTION_GENERIC"):
        analysis_results = self.orchestrator.execute_full_analysis(raw_data, phase)

        return {
            "analysis": analysis_results,
            "agent_note": f"Analiz tamamlandı. Soru: {question}"
        }