from enum import Enum


class AlgorithmType(Enum):
    """
    Enum representing the types of algorithms in optimization.

    Attributes:
        population (str): Algorithms that build an individual from scratch.
        trajectory (str): Algorithms that iteratively modify an existing individual.
        recombination (str): Algorithms that combine multiple individuals to create new ones.
        acceptance (str): Algorithms that decide whether to accept an individual or not.
    """
    
    population = "population"
    trajectory = "trajectory"
    recombination = "recombination"
    acceptance = "acceptance"