_PLOTS_REGISTRY = {}

def register_plot(cls):
    """Decorator to register a plot class automatically."""
    _PLOTS_REGISTRY[cls.name] = cls
    return cls

def get_registered_plots():
    return dict(_PLOTS_REGISTRY)
