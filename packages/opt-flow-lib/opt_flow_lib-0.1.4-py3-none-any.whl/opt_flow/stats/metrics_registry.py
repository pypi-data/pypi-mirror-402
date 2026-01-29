_METRIC_REGISTRY = {}

def register_metric(cls):
    """Decorator to register a metric class automatically."""
    _METRIC_REGISTRY[cls.name] = cls
    return cls

def get_registered_metrics():
    return dict(_METRIC_REGISTRY)
