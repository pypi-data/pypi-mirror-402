from opt_flow.stats.base_metric import BaseMetric
from opt_flow.stats.metrics_registry import register_metric
import numpy as np
from opt_flow.structure import ObjectiveDirection
from typing import List
@register_metric
class ImprovementFrequencySpectrum(BaseMetric):
    name = "improvement_frequency_spectrum"
    description = "Frequency analysis of improvements — shows oscillation tendency (per objective, direction-aware)."
    
    def __init__(self, directions: List[ObjectiveDirection] = [ObjectiveDirection.MINIMIZE]):
        self.directions = directions



    def compute(self, history):
        vals = np.asarray(history.objectives())  # (T, D)
        directions = self.directions
        accepted = np.asarray(history.accepted_mask())

        diffs = np.diff(vals, axis=0)
        # multiply by direction
        for d, direction in enumerate(directions):
            diffs[:, d] *= direction.value

        results = {}
        for d in range(vals.shape[1]):
            dd = diffs[:, d]
            # consider only accepted steps
            dd = dd[accepted[:-1]]  # exclude last step
            if len(dd) == 0:
                results[d] = {"dominant_frequency": np.nan, "dominant_amplitude": np.nan}
            else:
                spectrum = np.abs(np.fft.rfft(dd))
                freqs = np.fft.rfftfreq(len(dd))
                peak_idx = np.argmax(spectrum)
                results[d] = {
                    "dominant_frequency": float(freqs[peak_idx]),
                    "dominant_amplitude": float(spectrum[peak_idx]),
                }
        return results