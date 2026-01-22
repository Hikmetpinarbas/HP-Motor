import json

class MetricRegistry:
    def __init__(self, registry_path="canon/metric_ontology.json"):
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.families = data.get("canonical_families", {})

    def get_phase_metrics(self, phase_id: str):
        """Belirli bir faz (F1-F6) için tanımlı metrikleri döner."""
        return {k: v for k, v in self.families.items() if phase_id in v.get("phases", [])}

    def map_provider_metric(self, provider_col: str):
        """Provider ismini (örn: 'xG') HP Kanonik ismine eşler."""
        for key, family in self.families.items():
            if provider_col in family.get("aliases", []) or provider_col == key:
                return key
        return None
