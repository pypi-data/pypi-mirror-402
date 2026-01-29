from opt_flow.acceptance.scalar_acceptance import ScalarAcceptance
from opt_flow.structure import ScalarObjective
from opt_flow.structure import ObjectiveDirection

class DeterministicAcceptance(ScalarAcceptance):

    """
    Deterministic acceptance strategy for scalar objectives.

    The candidate is accepted if it is strictly better than the reference
    according to the objective direction, ignoring values that are
    considered numerically close.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.direction == ObjectiveDirection.MAXIMIZE:
            self.compare = self.compare_maximize
        else:
            self.compare = self.compare_minimize


    def compare_maximize(self, a: ScalarObjective, b: ScalarObjective) -> bool:
        return a.value < b.value
    
    def compare_minimize(self, a: ScalarObjective, b: ScalarObjective) -> bool:
        return a.value > b.value
    
