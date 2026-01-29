from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric

@register_metric
class TotalTime(BaseMetric):
    name = "total_time"
    description = "Total time passed."

    def compute(self, history):
        timestamps = history.timestamps()
        return timestamps[-1] - timestamps[0]