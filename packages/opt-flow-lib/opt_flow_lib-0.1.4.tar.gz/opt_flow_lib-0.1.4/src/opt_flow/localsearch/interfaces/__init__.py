"""
This module defines interfaces for local search components used in opt_flow.

The interfaces in this package specify the roles of various local search
building blocks, enabling flexible and modular construction of local
search algorithms. Each interface focuses on a specific responsibility
within the local search process.

"""


from opt_flow.localsearch.interfaces.chain_argument_generator import ChainArgumentGenerator
from opt_flow.localsearch.interfaces.first_movement_selector import FirstMovementSelector
from opt_flow.localsearch.interfaces.link_checker import LinkChecker
from opt_flow.localsearch.interfaces.memory_strategy import MemoryStrategy
from opt_flow.localsearch.interfaces.next_movement_selector import NextMovementSelector
from opt_flow.localsearch.interfaces.score_calculator import ScoreCalculator
from opt_flow.localsearch.interfaces.score_filter import ScoreFilter
from opt_flow.localsearch.interfaces.score_normalizer import ScoreNormalizer

__all__ = ["ChainArgumentGenerator", "FirstMovementSelector", "LinkChecker", "MemoryStrategy", "NextMovementSelector", "ScoreCalculator", "ScoreFilter", "ScoreNormalizer"]