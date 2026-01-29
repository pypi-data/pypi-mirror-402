from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
from opt_flow.stats.metrics.acceptance.acceptance_rate import AcceptanceRate
import numpy as np

@register_metric
class AcceptanceEntropy(BaseMetric):
    name = "acceptance_entropy"
    description = "Entropy of accepted vs rejected decisions."

    def compute(self, history):
        acceptance_rate = AcceptanceRate().compute(history)
        p = np.array([acceptance_rate, 1 - acceptance_rate])
        return float(-np.sum(p * np.log2(p + 1e-12)))
