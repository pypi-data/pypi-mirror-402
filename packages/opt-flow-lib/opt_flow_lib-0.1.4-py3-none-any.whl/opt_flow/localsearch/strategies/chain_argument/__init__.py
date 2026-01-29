"""
This module provides chain argument generators for local search algorithms.

Chain argument generators produce sequences or combinations of arguments
for chained local search operations. They control how multiple moves or
solution components are combined and evaluated during the search.

"""

from opt_flow.localsearch.strategies.chain_argument.full_combination_generator import FullCombinationGenerator
from opt_flow.localsearch.strategies.chain_argument.generic_generator import GenericGenerator
from opt_flow.localsearch.strategies.chain_argument.linked_element_generator import LinkedElementGenerator

__all__ = ["FullCombinationGenerator", "GenericGenerator", "LinkedElementGenerator"]