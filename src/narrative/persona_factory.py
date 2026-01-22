class PersonaFactory:
    """Aynı veriye 4 ayrı gözle bakan Narrative Engine (v2.0)"""
    def __init__(self, persona_type):
        self.type = persona_type # Analist, Scout, TD, SD

    def generate_sovereign_insight(self, processed_data):
        if self.type == "Scout":
            # Gabor Mate/Sapolsky odaklı davranışsal raporlama
            return self._scout_logic(processed_data)
        elif self.type == "TechnicalDirector":
            # Faz geçişleri ve antrenman metotları
            return self._td_logic(processed_data)
        # ... diğer personallar
