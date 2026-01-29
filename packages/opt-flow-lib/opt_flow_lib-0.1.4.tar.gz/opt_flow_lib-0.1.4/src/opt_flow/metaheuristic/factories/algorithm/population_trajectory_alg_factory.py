from opt_flow.metaheuristic.factories._base.algorithm_factory import AlgorithmFactory
from opt_flow.metaheuristic.factories._base.population_factory import PopulationFactory
from opt_flow.metaheuristic.metaheuristic import Metaheuristic
from opt_flow.metaheuristic import Algorithm, AlgorithmType
from opt_flow.structure import Data, BaseIndividual
from opt_flow.trajectory import BaseTrajectory
from opt_flow.core import BasePopulation

class PopulationTrajectoryAlgFactory(AlgorithmFactory):
    """
    Factory for creating Algorithm instances that combine population and
    trajectory phases.

    This factory produces an Algorithm of type `AlgorithmType.population`
    that internally executes a population algorithm followed by a
    trajectory-based algorithm.
    """
    
    def __init__(self, data: Data, population_factory: PopulationFactory, trajectory: BaseTrajectory):
        self.data = data
        self.population_factory = population_factory
        self.trajectory = trajectory
        
    def create(self) -> Algorithm:
        """
        Creates and returns a population Algorithm instance with an embedded
        trajectory phase.

        Returns:
            Algorithm: A new Algorithm instance of type
            AlgorithmType.population that internally executes a population
            algorithm followed by a trajectory algorithm.
        """
        alg = Algorithm(PopulationTrajectoryAlgorithm(self.population_factory.create(self.data), self.trajectory), "population", AlgorithmType.population)
        return alg
    

class PopulationTrajectoryAlgorithm(Metaheuristic):
    """
    Metaheuristic that sequentially applies a population algorithm followed
    by an trajectory algorithm.

    This class internally builds a two-node metaheuristic graph:
    population → trajectory.
    """
    
    def __init__(self, population: BasePopulation, trajectory: BaseIndividual):
        super().__init__()
        self.population = population
        self.trajectory = trajectory
        
    def create(self) -> BaseIndividual:
        """
        Executes the population phase followed by the trajectory phase.

        The method builds an internal metaheuristic graph with a population
        node connected to an trajectory node, then executes it.

        Returns:
            BaseIndividual: The final individual.
        """
        pop = Algorithm(self.population, "population", AlgorithmType.population)
        self.add_algorithm(pop)
        traj = Algorithm(self.trajectory, "trajectory", AlgorithmType.trajectory)
        self.add_algorithm(traj)
        self.connect(pop, traj)
        return self._run_create()