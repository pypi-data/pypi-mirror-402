import numpy as np
from opt_flow.config import config
class RandomClass:
    """Random number generator interface"""
    def __init__(self, seed=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if seed is None:
            seed = config.seed
        self.rng = np.random.default_rng(seed)
        self.seed = seed
