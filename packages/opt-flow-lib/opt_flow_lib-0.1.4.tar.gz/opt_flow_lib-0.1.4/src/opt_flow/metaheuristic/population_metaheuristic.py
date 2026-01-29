from opt_flow.core.base_population import BasePopulation
from opt_flow.metaheuristic.metaheuristic import Metaheuristic
class PopulationMetaheuristic(Metaheuristic, BasePopulation):
    """
    Base class for metaheuristics that operate on a population of individuals.

    This class inherits from both BasePopulation and Metaheuristic to
    combine population initialization and metaheuristic behavior.

    Note:
        Population metaheuristics do not support single-solution trajectory operators
        via the `iterate` method.
    """
    
    def iterate(self, individual):
        raise RuntimeError("Not possible to call a population metaheuristic for trajectories.")
    
