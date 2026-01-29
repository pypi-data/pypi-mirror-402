from opt_flow.localsearch.interfaces.link_checker import LinkChecker
from typing import Dict, Tuple, Type, Optional
from opt_flow.movement import Movement
from opt_flow.utils import NamedOperator

class LinkMatrix(NamedOperator):
    """
    Stores and retrieves link checkers between pairs of movement types.

    A link checker defines whether a move of one movement type can legally
    follow a move of another movement type, given their arguments and
    intermediate individuals.

    The matrix can optionally be symmetric: registering a checker for
    (A → B) will automatically register a reversed checker for (B → A).
    """

    def __init__(self, is_simmetric: bool = True):
        """
        Initialize an empty link matrix.

        Args:
            is_simmetric (bool): Whether link checkers should be automatically
                mirrored in reverse order using a `ReversedChecker`.
        """
        self._matrix: Dict[
            Tuple[Type[Movement], Type[Movement]],
            LinkChecker
        ] = {}
        self.is_simmetric = is_simmetric

    def register(
        self,
        from_move: Type[Movement],
        to_move: Type[Movement],
        checker: LinkChecker
    ) -> None:
        """
        Register a link checker for a pair of movement types.

        Args:
            from_move (Type[Movement]): The preceding movement type.
            to_move (Type[Movement]): The succeeding movement type.
            checker (LinkChecker): Checker validating the transition.

        Notes:
            If the matrix is symmetric, a reversed checker will be automatically
            registered for the opposite movement order.
        """
        self._matrix[(from_move, to_move)] = checker
        if self.is_simmetric:
            self._matrix[(to_move, from_move)] = ReversedChecker(checker)

    def get(
        self,
        from_to_move: Tuple[Type[Movement], Type[Movement]],
    ) -> Optional[LinkChecker]:
        """
        Retrieve the link checker for a given movement transition.

        Args:
            from_to_move (Tuple[Type[Movement], Type[Movement]]): Movement
                transition (previous, next).

        Returns:
            Optional[LinkChecker]: The associated checker, or None if the
            transition is unrestricted.
        """
        return self._matrix.get(from_to_move)

    
class ReversedChecker(LinkChecker):
    """
    Adapter that reverses the direction of an existing link checker.

    This allows symmetric link matrices by reusing a single checker
    implementation for both movement orders.
    """
    
    def __init__(self, checker: LinkChecker):
        """
        Initialize a reversed checker.

        Args:
            checker (LinkChecker): Original checker to be reversed.
        """
        self.checker = checker
    
    def check(self, prev_arg, prev_individual, next_arg, individual) -> bool:
        """
        Perform the reversed link check.

        Args:
            prev_arg: Argument of the previous move.
            prev_individual: individual before the previous move.
            next_arg: Argument of the next move.
            individual: Current individual state.

        Returns:
            bool: True if the reversed transition is allowed.
        """
        return self.checker.check(next_arg, individual, prev_arg, prev_individual)