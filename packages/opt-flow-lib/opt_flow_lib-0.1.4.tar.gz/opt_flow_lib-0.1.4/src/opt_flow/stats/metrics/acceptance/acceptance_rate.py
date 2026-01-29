from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric

@register_metric
class AcceptanceRate(BaseMetric):
    name = "acceptance_rate"
    description = "Rate of accepted improvements."

    def compute(self, history):
        accepted = history.accepted_mask()
        return float(sum(accepted) / len(accepted))