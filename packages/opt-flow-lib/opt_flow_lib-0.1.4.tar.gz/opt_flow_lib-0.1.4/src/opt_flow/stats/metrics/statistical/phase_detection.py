from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
@register_metric
class PhaseDetection(BaseMetric):
    name = "phase_detection"
    description = "Identify distinct optimization phases by moving average trend."

    def __init__(self, window_size: int = 10):
        super().__init__()
        self.window_size = window_size

    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        timestamps = history.timestamps()
        datetime_stamps = [t for t in timestamps]

        results = {}

        for d in range(vals.shape[1]):
            v = vals[:, d]

            if len(v) < self.window_size:
                results[d] = []
                continue

            moving = np.convolve(
                v,
                np.ones(self.window_size) / self.window_size,
                mode="valid",
            )

            slope = np.diff(moving)
            phases, start = [], 0
            sign = np.sign(slope[0])

            for i, s in enumerate(np.sign(slope)):
                if s != sign:
                    phases.append(
                        (len(phases), datetime_stamps[start], datetime_stamps[i])
                    )
                    start, sign = i, s

            phases.append(
                (len(phases), datetime_stamps[start], datetime_stamps[-1])
            )

            results[d] = phases

        return results
