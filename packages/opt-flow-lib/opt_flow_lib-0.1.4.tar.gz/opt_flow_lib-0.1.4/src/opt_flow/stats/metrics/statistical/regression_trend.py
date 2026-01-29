from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np

@register_metric
class RegressionTrend(BaseMetric):
    name = "regression_trend"
    description = "Linear regression of objective over time."

    def compute(self, history):
        from scipy.stats import linregress

        vals = np.asarray(history.objectives())  # (T, D)
        t = history.timestamps()

        results = {}

        for d in range(vals.shape[1]):
            v = vals[:, d]
            slope, _, r, p, se = linregress(t, v)

            results[d] = {
                "slope": float(slope),
                "r_value": float(r),
                "p_value": float(p),
                "stderr": float(se),
            }

        return results

