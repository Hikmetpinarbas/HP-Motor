def execute_metric(metric_spec: dict, data: dict):
    """
    Executes a metric_spec against provided data.
    v1: weighted sum
    """
    value = 0.0
    for component in metric_spec.get("components", []):
        key = component["metric"]
        weight = component.get("weight", 1.0)
        value += data.get(key, 0.0) * weight
    return value