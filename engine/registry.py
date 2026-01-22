import json

class MetricRegistry:
    def __init__(self, ontology_path="canon/metric_ontology.json"):
        with open(ontology_path, "r", encoding='utf-8') as f:
            self.ontology = json.load(f)

    def resolve_metric(self, raw_name):
        # Ham ismi kanonik aileye bağlar (xT, PPDA, NAS vb.)
        raw_clean = raw_name.lower().strip()
        for family_id, info in self.ontology['canonical_families'].items():
            aliases = [a.lower() for a in info.get('aliases', [])]
            if raw_clean == family_id or raw_clean in aliases:
                return family_id
        return "UNKNOWN_SIGNAL"
