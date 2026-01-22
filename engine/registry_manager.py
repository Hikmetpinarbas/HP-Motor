import json
import logging

class RegistryManager:
    """
    HP Motor - Registry Manager
    Metrikleri 'BLOCKED' durumundan 'READY' durumuna çeker.
    """
    def __init__(self, ontology_path="metric_ontology.json", registry_path="registry.json"):
        with open(ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
        except:
            self.registry = {"metrics": {}}

    def resolve_metric(self, raw_name):
        """
        Ham metrik ismini (Örn: 'Actions successful, %') kanonik aileye bağlar.
        """
        raw_clean = raw_name.lower().strip()
        
        # 1. Tam Eşleşme ve Aliases Kontrolü
        for family_id, info in self.ontology['canonical_families'].items():
            checks = [family_id.lower(), info['name'].lower(), info.get('turkish', '').lower()]
            checks.extend([a.lower() for a in info.get('aliases', [])])
            
            if any(c in raw_clean for c in checks):
                return family_id
        return "UNKNOWN_SIGNAL"

    def get_metric_spec(self, metric_id):
        return self.ontology['canonical_families'].get(metric_id, {})
