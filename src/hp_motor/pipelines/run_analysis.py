from hp_motor.canon import load_canon_metrics, CanonMetricRegistry
from hp_motor.engine.metric_executor import execute_metric

class SovereignOrchestrator:

    def __init__(self):
        self.registry = CanonMetricRegistry()
        self.registry.register_bulk(load_canon_metrics())

    def execute(
        self,
        analysis_object_id: str,
        raw_df,
        entity_id: str,
        role: str,
        phase: str
    ):
        # v1 dummy aggregation
        base_metrics = {
            "ppda": 12.3,
            "progressive_passes": 5.1
        }

        computed = {}
        for metric_id in self.registry.list_metrics():
            spec = self.registry.get(metric_id)
            computed[metric_id] = execute_metric(spec, base_metrics)

        return {
            "status": "OK",
            "metrics": [{"metric_id": k, "value": v} for k, v in computed.items()],
            "confidence": 0.72,
            "tables": {},
            "lists": {},
            "figure_objects": {}
        }